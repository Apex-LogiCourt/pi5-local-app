from typing import List, Dict, Optional
from data_models import CaseData, Evidence, Profile, Case, GameState, Phase, Role
from controller import CaseDataManager
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
import asyncio
from interrogation.interrogator import it
from verdict import get_judge_result
from game_workflow import create_game_workflow, run_workflow


class SignalEmitter(QObject):
    signal = pyqtSignal(str, object)

    def __init__(self):
        super().__init__()

class GameController(QObject):
    _instance = None
    _is_initialized = False
    _state : GameState = None
    _case_data : CaseData = None
    _workflow = None  # LangGraph 워크플로우


    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = GameController()
        return cls._instance
    
    def __init__(self):
        """
        GameController 초기화.
        - data_service: CaseDataService 인스턴스 (데이터 로드/저장 담당)
        """
        super().__init__()  # QObject 초기화
        if GameController._instance is not None:
            raise Exception("싱글톤 클래스는 직접 생성할 수 없습니다. get_instance() 메서드를 사용하세요.")
            
        GameController._instance = self
        self.signal = pyqtSignal()

        self._signal_emitter = SignalEmitter()
        self._signal = self._signal_emitter.signal  # SignalEmitter의 signal을 GameController의 _signal로 설정
        # GameState에 초기 데이터 반영

#==============================================
# UI 에서 호출하는 메서드 
#==============================================

    @classmethod
    async def initialize(cls) -> None:
        """게임 초기화 및 데이터 로드 (백그라운드 실행)"""
        cls._state = GameState()

        print("[GameController] 케이스 데이터 생성 시작 (전체 초기화)...")
        task = asyncio.create_task(CaseDataManager.generate_case_stream())  # 전체 CaseData 생성
        task.add_done_callback(cls._on_initialization_complete)

        # LangGraph 워크플로우 초기화
        cls._workflow = create_game_workflow()
        print(f"[GameController] LangGraph workflow initialized")

        return None

    @classmethod
    def initialize_with_stub(cls) -> None:
        """테스트모드: stub 데이터로 빠르게 초기화"""
        cls._state = GameState()

        print("[GameController] 테스트 모드: stub 데이터로 초기화...")
        cls._case_data = CaseDataManager.stub_case_data()
        cls._is_initialized = True

        cls._workflow = create_game_workflow()
        print(f"[GameController] 테스트 모드 초기화 완료")

        cls._send_signal("initialized", None)
        cls._send_signal("initialized", cls._case_data)

        return None
    
    @classmethod
    def _on_initialization_complete(cls, task):
        """초기화 완료 시 자동 호출되는 콜백"""
        try:
            result = task.result()
            cls._is_initialized = True
            cls._case_data = CaseData(case=result, profiles=[], evidences=[])
            cls._send_signal("initialized", None)
        except Exception as e:
            print(f"[GameController] 초기화 실패: {e}")
            import traceback
            traceback.print_exc()
            cls._send_signal("initialized", str(e))
        

    @classmethod
    async def prepare_case_data(cls) -> bool :

        timeout = 60
        elapsed = 0
        while not cls._is_initialized:
            if elapsed >= timeout:
                raise TimeoutError("초기화 시간 초과 (60초)")
            await asyncio.sleep(0.5)
            elapsed += 0.5
        
        task_profiles = asyncio.create_task(CaseDataManager.generate_profiles_stream())
        task_profiles.add_done_callback(cls._on_profiles_created)
        
        return True

    @classmethod
    def start_game(cls) -> bool :
        cls._state.phase = Phase.DEBATE
        cls._case_data = CaseDataManager.get_case_data()

        if not it.set_case_data(cls._case_data):
            print("[GameController] interrogator case_data 설정 실패")
            return False

        cls._state.messages.append({"role":"system", "content": cls._case_data.case.outline})
        cls._state.messages.append({"role":"system", "content": cls._case_data.profiles.__str__()})
        # 증거품은 _on_evidences_created()에서 생성 완료 시 추가됨

        return True

    
    @classmethod
    def _on_profiles_created(cls, task):
        cls._case_data.profiles = task.result()
        # CaseDataManager에도 case_data 설정 (증거품은 빈 리스트로)
        from controller import CaseDataManager
        CaseDataManager._case_data = cls._case_data
        # 프로필 생성 완료 시 바로 게임 화면으로 전환 (증거품은 빈 리스트로 시작)
        cls._send_signal("initialized", cls._case_data)
        # 증거품 생성은 백그라운드에서 계속 진행
        task_evidences = asyncio.create_task(CaseDataManager.generate_evidences())
        task_evidences.add_done_callback(cls._on_evidences_created)

    @classmethod
    def _on_evidences_created(cls, task):
        cls._case_data.evidences = task.result()
        # 증거품이 생성되면 messages에 추가
        cls._state.messages.append({"role":"system", "content": cls._case_data.evidences.__str__()})
        # 증거품 생성 완료 시 별도 시그널 전송 (이미지는 아직 없음)
        cls._send_signal("evidences_ready", cls._case_data.evidences)
        
        # 1차 전송: loading.png 이미지로 하드웨어에 전송
        from tools.service import handler_send_initial_evidence
        print("[GameController] 증거품 텍스트 생성 완료, loading 이미지로 1차 전송")
        handler_send_initial_evidence(cls._case_data.evidences)

        # 이미지를 병렬로 생성 (백그라운드에서)
        task_images = asyncio.create_task(cls._generate_evidence_images())
        task_images.add_done_callback(cls._on_evidence_images_created)

        asyncio.create_task(CaseDataManager.generate_case_behind())

    @classmethod
    async def _generate_evidence_images(cls):
        """증거품 이미지를 병렬로 생성"""
        from evidence import generate_evidence_images_parallel
        # 별도 스레드에서 병렬 이미지 생성
        evidences = await asyncio.to_thread(
            generate_evidence_images_parallel,
            cls._case_data.evidences
        )
        return evidences

    @classmethod
    def _on_evidence_images_created(cls, task):
        """이미지 생성 완료 시 하드웨어로 전송"""
        try:
            evidences = task.result()
            print("[GameController] 증거품 이미지 생성 완료")
            # 2차 전송: 실제 이미지로 하드웨어에 전송
            from tools.service import handler_send_initial_evidence
            handler_send_initial_evidence(evidences)
            # UI 업데이트 시그널 전송
            cls._send_signal("evidence_images_ready", evidences)
        except Exception as e:
            print(f"[GameController] 이미지 생성 실패: {e}")
            import traceback
            traceback.print_exc()

    @classmethod
    async def record_start(cls) -> None:
        """녹음 시작 후에 API 호출"""
        print("✅ GameController.record_start() 호출됨")  # 호출 확인 로그
        cls._state.record_state = True
        from tools.service import handler_record_start
        await handler_record_start()

    
    @classmethod
    async def record_end(cls) -> bool:
        """
        녹음 종료 버튼을 누름
        Returns:
            bool: True면 턴 전환, False면 턴 전환 없음
        """
        print("🛑 GameController.record_end() 호출됨")  # 호출 확인 로그
        cls._state.record_state = False
        from tools.service import handler_record_stop
        await handler_record_stop()
        
        if cls._state.phase == Phase.INTERROGATE:
            return False
        return True
    
    @classmethod
    async def user_input(cls, text: str) -> bool:
        """
        사용자의 수동 입력, 텍스트를 전송 (LangGraph 워크플로우 사용)
        Args:
            text: 사용자가 입력한 텍스트
        Returns:
             bool: True면 턴 전환, False면 턴 전환 없음
        """
        if not text.strip():
            return False

        if "이상입니다" in text:
            cls._state.done_flags[cls._state.turn] = True
            return True

        # LangGraph 워크플로우 실행
        try:
            result = await run_workflow(
                cls._workflow,
                user_input=text,
                game_state=cls._state,
                case_data=cls._case_data
            )

            # 결과 처리
            signal_code = result.get("signal_code")
            signal_data = result.get("signal_data")
            response = result.get("response")
            validation_result = result.get("validation_result", {})

            # DEBATE 모드 처리
            if cls._state.phase == Phase.DEBATE:
                relevant = validation_result.get("relevant")
                answer = validation_result.get("answer")
                interrogation_type = validation_result.get("interrogation_type")

                # 문맥과 관련 없는 경우
                if relevant == "false":
                    await cls._send_judge_message(
                        validation_result.get("answer"),
                        "no_context"
                    )
                    return False

                # 심문 요청인 경우
                if answer == "interrogation":
                    if interrogation_type == "retry":
                        await cls._send_judge_message(
                            validation_result.get("interrogation_answer"),
                            "no_context"
                        )
                        return False
                    else:
                        # 심문 모드로 전환
                        cls._state.phase = Phase.INTERROGATE
                        cls._state.current_profile = validation_result.get("target_profile")
                        await cls._send_judge_message(
                            validation_result.get("interrogation_answer"),
                            "interrogation_accepted",
                            {'type': interrogation_type}
                        )
                        return False

                # 정상 발언
                cls._add_message(cls._state.turn, text)
                return True

            # INTERROGATE 모드 처리 (워크플로우가 Interrogator 클래스 사용)
            elif cls._state.phase == Phase.INTERROGATE:
                # 사용자 질문 추가
                cls._add_message(cls._state.turn, text)

                # 워크플로우 결과를 심문 화면에 전송
                if signal_code == "interrogation" and signal_data:
                    # 스트리밍 효과를 위해 콜백 사용
                    from tools.service import handler_tts_service, run_str_streaming

                    def handle_response(sentence):
                        """생성되는 응답을 심문 화면에 전송하는 콜백"""
                        cls._send_signal("interrogation", {
                            "role": signal_data.get("role"),
                            "message": sentence
                        })

                    # 응답 스트리밍
                    run_str_streaming(response, handle_response)

                    # TTS 서비스 호출
                    # 워크플로우가 current_profile을 업데이트했으므로 결과에서 가져옴
                    updated_profile = result.get("current_profile")
                    if updated_profile:
                        cls._state.current_profile = updated_profile

                    voice = cls._state.current_profile.voice if cls._state.current_profile else "nraewon"
                    asyncio.create_task(handler_tts_service(response, voice))

                    # 메시지 추가
                    role_name = cls._state.current_profile.name if cls._state.current_profile else "증인"
                    cls._add_message(role_name, response)

                return True

        except Exception as e:
            print(f"[GameController] 워크플로우 실행 오류: {e}")
            import traceback
            traceback.print_exc()
            return False

        return True

    @classmethod
    def interrogation_end(cls) -> None:
        """심문 화면에서 뒤로 가기 버튼을 눌렀을 때 호출, 심문 종료"""
        cls._state.phase = Phase.DEBATE
        cls._state.current_profile = None
        if cls._state.record_state is True:
            asyncio.create_task(cls.record_end())

    @classmethod
    def done(cls) -> None:
        """발언 완전 종료 시에 호출, 양쪽 다 됐을 때는 최종 판결 시작"""
        cls._state.done_flags[cls._state.turn] = True
        print(f"[GameController] done() called: {cls._state.done_flags}")
        
        # if cls._state.done_flags[cls._state.turn.next()] == False:
        #     cls._switch_turn()

        if all(cls._state.done_flags.values()):
            cls._state.phase = Phase.JUDGEMENT
            cls._send_signal("judgement", {'role': '판사', 'message': '최종 판결을 내리겠습니다.'})
            cls._add_message("판사", "최종 판결을 내리겠습니다.")
            
            # 판결 생성 및 스트리밍
            cls._get_judgement()

    @classmethod
    def get_state(cls) -> GameState:
        """GameState 객체 반환."""
        return cls._state
    


#==============================================
# 내부 함수
#==============================================

    @classmethod
    def _send_signal(cls, code, arg):
        """ 신호 전송"""
        instance = cls.get_instance()
        instance._signal.emit(code, arg)

    @classmethod
    async def _send_judge_message(cls, message: str, signal_code: str, extra_data: dict = None):
        """판사의 발언을 음성으로 출력하고 시그널 전송"""
        judge_message = {
            'role': '판사',
            'message': message
        }
        if extra_data:
            judge_message.update(extra_data)

        cls._send_signal(signal_code, judge_message)
        cls._add_message("판사", message)

        from tools.service import handler_tts_service
        asyncio.create_task(handler_tts_service(message))

    
    @classmethod
    def _objection(cls) -> None:
        """
        이의 제기.
        - objection_count 증가, 메시지 추가, 턴 전환
        """
        cls._switch_turn()
        cls._state.objection_count[cls._state.turn] += 1
        cls._send_signal("objection", {"role": cls._state.turn.label(), "message": "이의 있음!"})
        print(f"[GameController] _objection() called: {cls._state.turn.label()}")

    @classmethod
    def _get_judgement(cls) -> str:
        """판결 단계에서 최종 결과를 얻어와 메시지에 추가하고 반환."""
        # 쌓인 대화 메시지들을 가져와서 판결 생성
        message_list = cls._state.messages
        print(f"[GameController] 판결 생성 시작 - 총 {len(message_list)}개 메시지")
        
        # 판결 결과 생성 (동기 함수)
        judgement_result = get_judge_result(message_list)
        
        from tools.service import handler_tts_service

        asyncio.create_task(handler_tts_service(judgement_result))
        cls._send_signal("verdict", judgement_result)
        print(judgement_result)
        
        print(f"[GameController] 판결 생성 완료")
        return judgement_result

    @classmethod
    def _add_message(cls, role: Role, content: str) -> None:
        """messages 리스트에 (role, content) 추가."""
        role_str = role.label() if isinstance(role, Role) else role
        cls._state.messages.append({"role": role_str, "content": content})
        print(f"[GameController] _add_message() called: {cls._state.messages[-1]}")

    @classmethod
    def _switch_turn(cls) -> None:
        """Role.PROSECUTOR ↔ Role.ATTORNEY 토글."""
        cls._state.turn = cls._state.turn.next()
        print(f"[GameController] _switch_turn() called: {cls._state.turn.value}")

    @classmethod
    def _handle_bnt_event(cls, role : str) -> None:
        """버튼 이벤트 처리 메서드"""
        # print(f"input_role : {role}, 현재 턴: {cls._state.turn.value}, 여부 : {role != cls._state.turn.value}")

        is_same_turn = role == cls._state.turn.value
        is_recording = cls._state.record_state # 값 복사 

        if cls._state.phase == Phase.DEBATE: # 토론 중일 때 
            if is_recording :
                asyncio.create_task(cls.record_end())
                cls._send_signal("record_toggled", False)
            if is_same_turn and not is_recording:
                asyncio.create_task(cls.record_start())
                cls._send_signal("record_toggled", True)
                return
            if not is_same_turn:
                cls._objection()
                return

        if cls._state.phase == Phase.INTERROGATE :
            if not is_same_turn : return
            else :
                if is_recording:
                    asyncio.create_task(cls.record_end())
                    cls._send_signal("record_toggled", False)
                else:
                    asyncio.create_task(cls.record_start())
                    cls._send_signal("record_toggled", True)
        return



