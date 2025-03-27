import streamlit as st
from dotenv import load_dotenv
import random
from llm import get_judge_result, ask_witness, ask_defendant
from llm import get_full_case_story, get_case_overview, get_related_characters, get_truth_revelation


class GameController:
    """게임 로직 전체를 관리하는 컨트롤러 클래스"""
    
    def __init__(self):
        """컨트롤러 초기화"""
        load_dotenv()
    
    def initialize_game_state(self):
        """게임 상태 초기화"""
        if 'game_phase' not in st.session_state:
            st.session_state.game_phase = "init"  # init, debate, judgement, reveal_truth
            st.session_state.turn = "검사"
            st.session_state.done_flags = {"검사": False, "변호사": False}
            st.session_state.message_list = []
            st.session_state.mode = "debate"  # debate, witness, defendant
            st.session_state.conversation_history = []  # 참고인/피고인과의 대화 내역 저장
    
    def generate_case(self):
        """새로운 사건 생성"""
        # 전체 스토리 생성
        full_story = get_full_case_story()
        st.session_state.full_story = full_story
        
        # 피해자 정보 추출
        self._extract_victim_info(full_story)
        
        # 용의자 정보 추출
        self._extract_suspect_info(full_story)
        
        # 게임 시작용 개요만 추출
        case_summary = get_case_overview(full_story)
        st.session_state.message_list.append({"role": "system", "content": case_summary})
        
        # 등장인물 이름 관리
        used_names = []
        if st.session_state.defendant_name:
            used_names.append(st.session_state.defendant_name)
        if st.session_state.victim_name:
            used_names.append(st.session_state.victim_name)

        # 사건 관련자 2명만 추출 
        related_characters = self._extract_related_characters(full_story, used_names)
        
        # 전문가 1명 추가
        expert = self._create_expert_profile(used_names)
        
        # 참고인 목록 구성 (관련자 2명 + 전문가 1명)
        witness_profiles = related_characters + [expert]
        
        # 최종 안전 검사: 모든 참고인이 서로 다른 이름을 가지도록 확인
        self._ensure_unique_names(witness_profiles, used_names)
            
        # 피해자 정보 기록 (참고용)
        if st.session_state.victim_name and st.session_state.victim_status == "사망":
            st.session_state.message_list.append({
                "role": "system",
                "content": f"[참고 정보: 피해자 {st.session_state.victim_name}(은)는 사망했습니다. 따라서 참고인으로 등장할 수 없습니다.]"
            })
        
        st.session_state.witness_profiles = witness_profiles
        
        # 사건이 초기화되었음을 표시
        st.session_state.case_initialized = True

    def _extract_victim_info(self, full_story):
        """피해자 정보 추출"""
        victim_name = ""
        victim_status = "unknown"
        victim_desc = ""
        for line in full_story.split("\n"):
            if line.startswith("[피해자 정보]:"):
                victim_info = line.split(":", 1)[1].strip()
                if "이름=" in victim_info:
                    try:
                        name_part = victim_info.split("이름=")[1]
                        victim_name = name_part.split("|")[0] if "|" in name_part else name_part.strip()
                    except:
                        pass
                if "상태=" in victim_info:
                    try:
                        status_part = victim_info.split("상태=")[1]
                        victim_status = status_part.split("|")[0] if "|" in status_part else status_part.strip()
                    except:
                        pass
                if "설명=" in victim_info:
                    try:
                        desc_part = victim_info.split("설명=")[1]
                        victim_desc = desc_part.split("|")[0] if "|" in desc_part else desc_part.strip()
                    except:
                        pass
                break
        
        # 피해자 정보가 없을 경우 검색 시도
        if not victim_name:
            for line in full_story.split("\n"):
                if "피해자" in line and ("이름=" in line or "|이름=" in line):
                    try:
                        name_part = line.split("이름=")[1]
                        victim_name = name_part.split("|")[0] if "|" in name_part else name_part.strip()
                        if "사망" in line:
                            victim_status = "사망"
                        elif "생존" in line:
                            victim_status = "생존"
                        break
                    except:
                        pass
        
        st.session_state.victim_name = victim_name
        st.session_state.victim_status = victim_status
        st.session_state.victim_desc = victim_desc if victim_desc else "피해자"

    def _extract_suspect_info(self, full_story):
        """용의자 정보 추출"""
        suspect_name = ""
        suspect_desc = ""
        for line in full_story.split("\n"):
            if "[용의자 정보]:" in line:
                try:
                    # 용의자 정보에서 이름 및 설명 추출
                    info_text = line.split(":", 1)[1].strip()
                    
                    # 이름 추출
                    if "이름=" in info_text:
                        name_part = info_text.split("이름=")[1]
                        suspect_name = name_part.split("|")[0] if "|" in name_part else name_part.strip()
                    else:
                        # 이름이 명시적으로 없는 경우 첫 단어를 이름으로 가정
                        name_parts = info_text.split()[:2]  # 성과 이름 추출 시도 (성 + 이름)
                        if len(name_parts) >= 1:
                            suspect_name = ' '.join(name_parts[:2]) if len(name_parts) >= 2 else name_parts[0]
                            
                    # 설명 추출
                    if "설명=" in info_text:
                        desc_part = info_text.split("설명=")[1]
                        suspect_desc = desc_part.split("|")[0] if "|" in desc_part else desc_part.strip()
                    else:
                        # 설명이 명시적으로 없는 경우 전체 정보를 설명으로 사용
                        suspect_desc = info_text
                    
                    break
                except:
                    pass
        
        # 용의자 이름을 찾지 못한 경우
        if not suspect_name:
            suspect_name = "용의자"
            suspect_desc = "주요 용의자"
        
        st.session_state.defendant_name = suspect_name
        st.session_state.defendant_desc = suspect_desc

    def _extract_related_characters(self, full_story, used_names):
        """관련 등장인물 추출"""
        related_characters = get_related_characters(full_story)[:2]  # 최대 2명으로 제한
        
        # 각 관련자에 대한 설명 추가
        for i in range(len(related_characters)):
            if "background" not in related_characters[i]:
                related_characters[i]["background"] = "사건 관련자"
        
        # 이름 중복 확인 및 수정
        for i in range(len(related_characters)):
            # 피해자나 용의자와 이름이 같은 경우 수정
            if related_characters[i]["name"] in used_names:
                backup_names = [
                    "백도현", "임지은", "손예진", "오현우", "노은서", "진승호", 
                    "권나라", "류태민", "장서윤", "홍태경", "송민아", "윤도현",
                    "신지우", "조현우", "한소연", "남윤재", "하승리", "강태희",
                    "이동우", "박하연", "서준혁", "전지영", "구영민", "민서윤"
                ]
                # 사용되지 않은 이름 중 하나 선택
                for new_name in backup_names:
                    if new_name not in used_names:
                        related_characters[i]["name"] = new_name
                        break
            
            # 이름 사용 기록
            used_names.append(related_characters[i]["name"])
            
        return related_characters

    def _create_expert_profile(self, used_names):
        """전문가 프로필 생성"""
        expert_names = [
            {"name": "최준혁", "title": "법의학 교수"},
            {"name": "박지영", "title": "법의학 전문가"},
            {"name": "김태영", "title": "범죄심리학자"},
            {"name": "서민지", "title": "디지털 포렌식 전문가"},
            {"name": "정성훈", "title": "범죄심리학 교수"},
            {"name": "이현우", "title": "법의학 전문의"},
            {"name": "문수진", "title": "범죄 프로파일러"},
            {"name": "황도윤", "title": "과학수사 전문가"},
            {"name": "유지원", "title": "법정 심리학자"},
            {"name": "안세준", "title": "증거분석 전문가"}
        ]
        
        # 이미 사용된 이름은 제외
        available_experts = [e for e in expert_names if e["name"] not in used_names]
        
        # 가능한 전문가가 없으면 백업 이름 사용
        if not available_experts:
            backup_names = [
                {"name": "고태식", "title": "법의학 교수"},
                {"name": "신현주", "title": "범죄심리학 전문가"},
                {"name": "양준호", "title": "디지털 포렌식 전문가"},
                {"name": "정미영", "title": "법의학 전문의"}
            ]
            available_experts = [e for e in backup_names if e["name"] not in used_names]
            
            # 그래도 없으면 기본 이름 생성
            if not available_experts:
                names = ["윤성철", "한지민", "배수지", "정해인", "류승범"]
                for name in names:
                    if name not in used_names:
                        available_experts = [{"name": name, "title": "범죄 분석 전문가"}]
                        break
        
        # 전문가 선택 및 추가
        expert_profile = random.choice(available_experts)
        expert = {
            "name": expert_profile["name"], 
            "type": "expert", 
            "background": expert_profile["title"]
        }
        
        return expert

    def _ensure_unique_names(self, witness_profiles, used_names):
        """모든 참고인이 고유한 이름을 갖도록 함"""
        unique_names = set()
        for i, profile in enumerate(witness_profiles):
            if profile["name"] in unique_names:
                # 중복 발견 시 새 이름 할당
                backup_names = ["강민식", "한소영", "윤태호", "임유진", "신동우", "조혜원"]
                for name in backup_names:
                    if name not in used_names and name not in unique_names:
                        witness_profiles[i]["name"] = name
                        break
            
            unique_names.add(profile["name"])

    def handle_case_judgment(self, message_list):
        """판결 처리"""
        judge_result = get_judge_result(message_list)
        return judge_result
    
    def get_truth_revelation(self, full_story, judge_result):
        """진실 공개"""
        return get_truth_revelation(full_story, judge_result)
    
    def ask_witness(self, question, name, wtype, case_summary, full_story="", previous_conversation=""):
        """참고인 질문 처리"""
        return ask_witness(question, name, wtype, case_summary, full_story, previous_conversation)
    
    def ask_defendant(self, question, defendant_name, case_summary, full_story="", previous_conversation=""):
        """피고인 질문 처리"""
        return ask_defendant(question, defendant_name, case_summary, full_story, previous_conversation)
    
    def reset_game(self):
        """게임 초기화"""
        keys = ["game_phase", "turn", "done_flags", "message_list", "mode", 
                "witness_profiles", "case_initialized", "defendant_name", 
                "full_story", "judge_result"]
        for key in keys:
            if key in st.session_state:
                del st.session_state[key]


# 컨트롤러 객체 생성
game_controller = GameController()

# 컨트롤러 메서드들을 외부에서 직접 사용할 수 있도록 함수 제공
def initialize_game():
    """게임 초기화"""
    game_controller.initialize_game_state()

def generate_new_case():
    """새 사건 생성"""
    game_controller.generate_case()

def handle_judgment(message_list):
    """판결 처리"""
    return game_controller.handle_case_judgment(message_list)

def reveal_truth(full_story, judge_result):
    """진실 공개"""
    return game_controller.get_truth_revelation(full_story, judge_result)

def ask_witness_question(question, name, wtype, case_summary, full_story="", previous_conversation=""):
    """참고인 질문"""
    return game_controller.ask_witness(question, name, wtype, case_summary, full_story, previous_conversation)

def ask_defendant_question(question, defendant_name, case_summary, full_story="", previous_conversation=""):
    """피고인 질문"""
    return game_controller.ask_defendant(question, defendant_name, case_summary, full_story, previous_conversation)

def reset_game_state():
    """게임 상태 초기화"""
    game_controller.reset_game()
