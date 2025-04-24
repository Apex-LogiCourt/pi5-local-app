import streamlit as st
from dotenv import load_dotenv
import asyncio  # asyncio 모듈 추가
import random

from controller import CaseDataManager
from controller import get_judge_result_wrapper as get_judge_result
from controller import ask_witness_wrapper as ask_witness
from controller import ask_defendant_wrapper as ask_defendant
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from data_models import CaseData, Case, Profile, Evidence

load_dotenv()


# 증거품 생성 관련 핸들러 
def _handle_evidence_storage(evidences):
    st.session_state.evidences = evidences
    # print("session_state.evidences:", st.session_state.evidences) 
    # 터미널에 로그 출력 콘솔에는 stearmlit 보안 문제로 못 찍네용

def _handle_evidence_ui_update(evidences):
    # UI 업데이트 로직
    pass

st.set_page_config(page_title="LogiCourt_AI", page_icon=":🤖:")
st.title("LogiCourt_AI")
st.caption("검사와 변호사가 주장하고, AI 판사가 판단합니다.")

# 초기 상태 설정
if 'game_phase' not in st.session_state:
    st.session_state.game_phase = "init"  # init, debate, judgement
    st.session_state.turn = "검사"
    st.session_state.done_flags = {"검사": False, "변호사": False}
    st.session_state.message_list = []
    st.session_state.mode = "debate"  # or "witness" 


    # CaseData 객체와 관련 데이터클래스들 저장
    st.session_state.case_data = None
    st.session_state.case = None
    st.session_state.profiles = None
    st.session_state.evidences = None

# 사건 개요 생성 단계
if st.session_state.game_phase == "init":
    # 이미 사건이 생성되었는지 확인
    if 'case_initialized' not in st.session_state:
        case_container = st.container()  # 컨테이너 생성
        with case_container:  # 컨테이너 안에서 UI 요소들 배치
            with st.spinner("사건을 생성 중입니다..."):
                # 스트리밍 결과를 임시로 저장할 변수
                placeholder = st.empty()
                
                def update_ui(content, full_text):
                    placeholder.markdown(f"{full_text}▌")
                case_summary = asyncio.run(CaseDataManager.generate_case_stream(callback=update_ui))
                profiles = asyncio.run(CaseDataManager.generate_profiles_stream(callback=update_ui))
                
                placeholder.empty()
                
                
                # 메시지 리스트에 추가
                st.session_state.message_list.append({"role": "system", "content": case_summary})
                st.session_state.message_list.append({"role": "system", "content": profiles})
                st.session_state.case_initialized = True
                
        st.success("사건 생성 완료! 검사부터 시작하세요")
        
    # 어떤 경우든 게임 단계는 debate로 변경
    st.session_state.game_phase = "debate"

# 이전 턴 처리 후 턴 전환
if 'last_turn_input' in st.session_state:
    prev = st.session_state.last_turn_input
    last_msg = st.session_state.message_list[-1]["content"].strip().lower()
    print(f"입력 메시지: '{last_msg}', 처리 후: '{last_msg.replace('.', '').replace(' ', '')}'")
    print(f"현재 done_flags: {st.session_state.done_flags}")
    
    # '이상입니다'만 입력하거나 '이상입니다.' 등으로 끝나는 경우 모두 인식
    if last_msg.replace(".", "").replace(" ", "") == "이상입니다":
        st.session_state.done_flags[prev] = True
        print(f"'{prev}' 종료 플래그 설정됨: {st.session_state.done_flags}")
        
        if all(st.session_state.done_flags.values()):
            print("모든 당사자 종료 - 판결 단계로 진입")
            st.session_state.game_phase = "judgement"
        else:
            st.session_state.turn = "변호사" if prev == "검사" else "검사"
    else:
        st.session_state.turn = "변호사" if prev == "검사" else "검사"
    
    del st.session_state.last_turn_input

# 메시지 출력
for i, message in enumerate(st.session_state.message_list):
    if i == 0 and message["role"] == "system":  # 첫 번째 메시지가 시스템(사건 개요)인 경우
        # 초기화 단계(init)가 아닐 때만 사건 개요를 expander로 다시 표시
        if st.session_state.game_phase != "init":
            with st.expander("📜 사건 개요", expanded=True):
                st.markdown(message["content"])
    elif i == 1 and message["role"] == "system" :
        if st.session_state.game_phase != "init":
            with st.expander("🕵️ 등장인물", expanded=True):
                st.markdown(message["content"])
    else:
        with st.chat_message(message["role"]):
            st.write(message["content"])

# 참고인 호출 UI

if st.session_state.mode == "debate":
    # state 변수 초기화 
    if st.session_state.case is None:
        print("증거품 생성 중...")
        asyncio.run(CaseDataManager.generate_evidences(
            callbacks=[_handle_evidence_storage]))
        st.session_state.case = CaseDataManager.get_case()
        st.session_state.profiles = CaseDataManager.get_profiles()
        print("증거품 생성 완료!")
    st.session_state.game_phase = "debate"

    # 등장인물 정보 처리
    if 'witness_profiles' not in st.session_state and st.session_state.profiles:
        st.session_state.witness_profiles = []
        for profile in st.session_state.profiles:
            # 피고인 정보 추출
            if profile.type == "defendant":
                st.session_state.defendant_name = profile.name
            # 증인/참고인 정보 추출
            elif profile.type in ["witness", "reference", "victim"]:
                st.session_state.witness_profiles.append({
                    "name": profile.name,
                    "type": profile.type
                })
        
        # 피고인 이름이 없으면 기본값 설정
        if 'defendant_name' not in st.session_state:
            st.session_state.defendant_name = "피고인"
    
    # 참고인 호출 UI
    col1, col2 = st.columns([3, 1])
    with col1:
        with st.expander("🔎 참고인 호출하기", expanded=False):
            st.markdown("**어떤 참고인을 호출하시겠습니까?**")
            
            if 'witness_profiles' in st.session_state and st.session_state.witness_profiles:
                cols = st.columns(len(st.session_state.witness_profiles))
                for i, witness in enumerate(st.session_state.witness_profiles):
                    with cols[i]:
                        icon = "👤" if witness['type'] == "witness" else "🧠" if witness['type'] == "reference" else "😢" if witness['type'] == "victim" else "👁️"
                        label = f"{icon} {witness['name']}"
                        if st.button(label, key=f"w{i}"):
                            st.session_state.mode = "witness"
                            st.session_state.witness_name = witness['name']
                            st.session_state.witness_type = witness['type']
                            st.rerun()
            else:
                st.warning("등장인물 정보가 아직 준비되지 않았습니다.")
    
    with col2:
        if 'defendant_name' in st.session_state:
            defendant_name = st.session_state.defendant_name
            if st.button(f"👨‍⚖️ {defendant_name}에게 질문하기"):
                st.session_state.mode = "defendant"
                st.rerun()

# 참고인 질문 모드
if st.session_state.mode == "witness":
    witness_name = st.session_state.witness_name
    witness_type = st.session_state.witness_type
    case_summary = st.session_state.message_list[0]["content"] if st.session_state.message_list else ""
    
    st.markdown(f"**📞 {witness_name} 참고인에게 질문하세요.**")
    
    # 이전 질문/대답 기록 표시
    for msg in st.session_state.message_list:
        if msg["role"] == "user" and f"[참고인 {witness_name}에게 질문:" in msg["content"]:
            with st.chat_message("user"):
                # 질문 메시지에서 실제 질문만 추출
                q_text = msg["content"].split(f"[참고인 {witness_name}에게 질문: ")[1].rstrip("]")
                st.write(q_text)
        elif msg["role"] == "witness" and st.session_state.message_list[st.session_state.message_list.index(msg)-1]["role"] == "user" and f"[참고인 {witness_name}에게 질문:" in st.session_state.message_list[st.session_state.message_list.index(msg)-1]["content"]:
            with st.chat_message("witness"):
                st.write(msg["content"])
    
    if q := st.chat_input("참고인에게 질문 입력..."):
        with st.chat_message("user"): 
            st.write(q)
        with st.chat_message("witness"):
            with st.spinner(f"{witness_name} 참고인이 대답 중입니다..."):
                response = ask_witness(q, witness_name, witness_type, case_summary)
                st.write(response)
        st.session_state.message_list.append({"role": "user", "content": f"[참고인 {witness_name}에게 질문: {q}]"})
        st.session_state.message_list.append({"role": "witness", "content": response})
        st.rerun()
    
    # 뒤로 가기 버튼
    if st.button("↩️ 토론 모드로 돌아가기"):
        st.session_state.mode = "debate"
        st.rerun()

# 피고인 질문 모드
if st.session_state.mode == "defendant":
    defendant_name = st.session_state.defendant_name
    case_summary = st.session_state.message_list[0]["content"] if st.session_state.message_list else ""
    
    st.markdown(f"**⚖️ {defendant_name}에게 질문하세요.**")
    
    # 이전 질문/대답 기록 표시
    for msg in st.session_state.message_list:
        if msg["role"] == "user" and f"[피고인 {defendant_name}에게 질문:" in msg["content"]:
            with st.chat_message("user"):
                # 질문 메시지에서 실제 질문만 추출
                q_text = msg["content"].split(f"[피고인 {defendant_name}에게 질문: ")[1].rstrip("]")
                st.write(q_text)
        elif msg["role"] == "defendant" and st.session_state.message_list[st.session_state.message_list.index(msg)-1]["role"] == "user" and f"[피고인 {defendant_name}에게 질문:" in st.session_state.message_list[st.session_state.message_list.index(msg)-1]["content"]:
            with st.chat_message("defendant"):
                st.write(msg["content"])
    
    if q := st.chat_input(f"{defendant_name}에게 질문 입력..."):
        with st.chat_message("user"): 
            st.write(q)
        with st.chat_message("defendant"):
            with st.spinner(f"{defendant_name}이(가) 대답 중입니다..."):
                response = ask_defendant(q, defendant_name, case_summary)
                st.write(response)
        st.session_state.message_list.append({"role": "user", "content": f"[피고인 {defendant_name}에게 질문: {q}]"})
        st.session_state.message_list.append({"role": "defendant", "content": response})
        st.rerun()
    
    # 뒤로 가기 버튼
    if st.button("↩️ 토론 모드로 돌아가기"):
        st.session_state.mode = "debate"
        st.rerun()

# 사용자 주장 입력
if st.session_state.mode == "debate" and st.session_state.game_phase == "debate":
    if user_input := st.chat_input(f"{st.session_state.turn.upper()}의 주장을 입력하세요 (이상입니다 입력 시 종료)"):
        role = st.session_state.turn
        with st.chat_message(role):
            st.write(user_input)
        st.session_state.message_list.append({"role": role, "content": user_input})
        st.session_state.last_turn_input = role
        
        # 즉시 '이상입니다' 체크 및 판결 진행
        if user_input.strip().lower().replace(".", "").replace(" ", "") == "이상입니다":
            st.session_state.done_flags[role] = True
            print(f"'{role}' 종료 플래그 설정됨: {st.session_state.done_flags}")
            
            # 양쪽 모두 이상입니다라고 했는지 확인
            other_role = "변호사" if role == "검사" else "검사"
            if st.session_state.done_flags.get(other_role, False):
                print("모든 당사자 종료 - 즉시 판결 단계로 진입")
                st.session_state.game_phase = "judgement"
                
                # 판결 즉시 실행
                with st.chat_message("judge"):
                    st.warning("AI 판사가 판단 중입니다...")
                    # 명시적으로 controller.py의 함수 호출
                    from controller import get_judge_result_wrapper
                    filtered_messages = [m for m in st.session_state.message_list if m['role'] in ['검사', '변호사']]
                    print(f"판결용 메시지 개수: {len(filtered_messages)}")
                    for i, m in enumerate(filtered_messages):
                        print(f"메시지 {i}: [{m['role']}] '{m['content'][:30]}...'")
                        
                    result = get_judge_result_wrapper(st.session_state.message_list)
                    print(f"판결 결과: {result[:100]}...")
                    st.success("판결이 완료되었습니다!")
                    st.markdown("## AI 판사의 판결")
                    st.markdown(result)
                    
                    # 사건의 진실 생성 및 표시
                    st.markdown("---")
                    st.markdown("## 🔍 사건의 진실")
                    with st.spinner("사건의 진실을 밝히는 중..."):
                        case_behind = asyncio.run(CaseDataManager.generate_case_behind())
                        st.markdown(case_behind)
                
                st.session_state.game_phase = "done"
                
                # 다시하기 버튼 표시
                if st.button("🔁 다시하기", key="restart_button"):
                    for key in ["game_phase", "turn", "done_flags", "message_list", "mode", "witness_profiles", "case_initialized", "defendant_name"]:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()
                
                print("판결 완료: 게임 단계 'done'으로 설정")
            else:
                # 한 쪽만 이상입니다라고 했을 경우 rerun
                st.rerun()
        else:
            # 일반적인 경우 rerun
            st.rerun()

# 판결 단계
if st.session_state.game_phase == "judgement":
    print("기존 방식의 판결 단계 실행 시작")
    with st.chat_message("judge"):
        with st.spinner("AI 판사가 판단 중입니다..."):
            # 디버깅용 로그
            print(f"판결 단계 실행: {st.session_state.game_phase}, 함수: get_judge_result_wrapper")
            
            # 메시지 내용 검사
            filtered_messages = [m for m in st.session_state.message_list if m['role'] in ['검사', '변호사']]
            print(f"판결용 메시지 개수: {len(filtered_messages)}")
            for i, m in enumerate(filtered_messages):
                print(f"메시지 {i}: [{m['role']}] '{m['content'][:30]}...'")
            
            # 명시적으로 controller.py의 함수 호출
            from controller import get_judge_result_wrapper
            result = get_judge_result_wrapper(st.session_state.message_list)
            st.write(result)
        st.session_state.game_phase = "done"
        print("판결 완료: 게임 단계 'done'으로 설정")

# 게임 종료 후 다시하기
if st.session_state.game_phase == "done":
    if st.button("🔁 다시하기"):
        for key in ["game_phase", "turn", "done_flags", "message_list", "mode", "witness_profiles", "case_initialized", "defendant_name"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

print('Debugger activated')
