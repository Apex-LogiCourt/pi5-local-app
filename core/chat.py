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
    st.session_state.turn = True  # True: 검사, False: 변호사
    st.session_state.done_flags = {"검사": False, "변호사": False}
    st.session_state.message_list = []
    st.session_state.mode = "debate"  # or "witness" 
    st.session_state.objection_count = {"검사": 0, "변호사": 0}  # 이의 제기 횟수 추적

    # CaseData 객체와 관련 데이터클래스들 저장
    st.session_state.case_data = None
    st.session_state.case = None
    st.session_state.profiles = None
    st.session_state.evidences = None

# 사건 개요 생성 단계
if st.session_state.game_phase == "init":
    # 이미 사건이 생성되었는지 확인
    if 'case_initialized' not in st.session_state:
        with st.spinner("사건을 생성 중입니다..."):
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
            
    # 어떤 경우든 게임 단계는 debate로 변경
    st.success("사건 생성 완료! 검사부터 시작하세요")
    st.session_state.game_phase = "debate"

# 메시지 출력
for i, message in enumerate(st.session_state.message_list):
    if i > 1:
        with st.chat_message(message["role"]):
            st.write(message["content"])

if (
    st.session_state.game_phase != "init"
    and st.session_state.message_list
    and len(st.session_state.message_list) > 1
):
    with st.sidebar:
        with st.expander("📜 사건 개요", expanded=True):
            st.markdown(st.session_state.message_list[0]["content"])
        with st.expander("🕵️ 등장인물", expanded=True):
            st.markdown(st.session_state.message_list[1]["content"])

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

    # 이 부분부터 밑에 주석처리한 코드까지 다 수정하는 게 좋겠습니다 ~ 
    # 피고인 정보 추출 (사건 개요에서 추출)
    # message_list에서 가져오지 말고 데이터 클래스에 접근해서 가져오면 됨 
    # if 'defendant_name' not in st.session_state and st.session_state.message_list:
    #     case_summary = st.session_state.message_list[0]["content"]
    #     # 용의자 정보 라인 찾기
    #     for line in case_summary.split("\n"):
    #         if "[용의자 정보]:" in line or "[용의자]:" in line:
    #             # 첫 단어를 이름으로 사용
    #             try:
    #                 st.session_state.defendant_name = line.split(":", 1)[1].strip().split()[0]
    #             except:
    #                 st.session_state.defendant_name = "피고인"
    #             break
    #     # 찾지 못한 경우 기본값 사용
    #     if 'defendant_name' not in st.session_state:
    #         st.session_state.defendant_name = "피고인"
    
    # col1, col2 = st.columns([3, 1])
    # with col1:
    #     with st.expander("🔎 참고인 호출하기"):
    #         st.markdown("**어떤 참고인을 호출하시겠습니까?**")
    #         cols = st.columns(len(st.session_state.witness_profiles))
    #         for i, witness in enumerate(st.session_state.witness_profiles):
    #             with cols[i]:
    #                 label = f"👤 {witness['name']}" if witness['type'] == "character" else f"🧠 {witness['name']}"
    #                 if st.button(label, key=f"w{i}"):
    #                     st.session_state.mode = "witness"
    #                     st.session_state.witness_name = witness['name']
    #                     st.session_state.witness_type = witness['type']
    
    # with col2:
    #     defendant_name = st.session_state.get('defendant_name', '피고인')
    #     if st.button(f"👨‍⚖️ {defendant_name}에게 질문하기"):
    #         st.session_state.mode = "defendant"
    #         st.session_state.defendant_name = defendant_name

# # 참고인 질문 모드
# if st.session_state.mode == "witness":
#     witness_name = st.session_state.witness_name
#     witness_type = st.session_state.witness_type
#     case_summary = st.session_state.message_list[0]["content"] if st.session_state.message_list else ""
    
#     st.markdown(f"**📞 {witness_name} 참고인에게 질문하세요.** (질문 1회)")
#     if q := st.chat_input("참고인에게 질문 입력..."):
#         with st.chat_message("user"): st.write(q)
#         with st.chat_message("witness"):
#             response = ask_witness(q, witness_name, witness_type, case_summary)
#             st.write(response)
#         st.session_state.message_list.append({"role": "user", "content": f"[참고인 질문: {q}]"})
#         st.session_state.message_list.append({"role": "witness", "content": response})
#         st.session_state.mode = "debate"
#         st.rerun()

# # 피고인 질문 모드
# if st.session_state.mode == "defendant":
#     defendant_name = st.session_state.defendant_name
#     case_summary = st.session_state.message_list[0]["content"] if st.session_state.message_list else ""
    
#     st.markdown(f"**⚖️ {defendant_name}에게 질문하세요.**")
#     if q := st.chat_input(f"{defendant_name}에게 질문 입력..."):
#         with st.chat_message("user"): st.write(q)
#         with st.chat_message("defendant"):
#             response = ask_defendant(q, defendant_name, case_summary)
#             st.write(response)
#         st.session_state.message_list.append({"role": "user", "content": f"[피고인 질문: {q}]"})
#         st.session_state.message_list.append({"role": "defendant", "content": response})
#         st.session_state.mode = "debate"
#         st.rerun()

# 사용자 주장 입력
if st.session_state.mode == "debate" and st.session_state.game_phase == "debate":
    col1, col2 = st.columns([8, 2])
    with col1:
        current_role = "검사" if st.session_state.turn else "변호사"
        user_input = st.text_input(
            "주장 입력",
            key=f"chat_input_{st.session_state.turn}_{len(st.session_state.message_list)}",
            placeholder=f"{current_role.upper()}의 주장을 입력하세요 (이상입니다 입력 시 종료)",
            label_visibility="collapsed"
        )
    with col2:
        objection = st.button("🚨이의 있음!", key="objection_button", use_container_width=True)

    # 메시지 입력 + 턴 전환 
    if user_input:
        role = "검사" if st.session_state.turn else "변호사"
        with st.chat_message(role):
            st.write(user_input)
        st.session_state.message_list.append({"role": role, "content": user_input})
        
        # "이상입니다" 입력 시에만 턴 전환 로직 실행
        if user_input.rstrip('.').strip().endswith("이상입니다"):
            if user_input.rstrip('.').strip() == "이상입니다":
                st.session_state.turn = not st.session_state.turn  # 턴 전환
                st.session_state.done_flags[role] = True
                print("현재 done_flags:", st.session_state.done_flags)
                if all(st.session_state.done_flags.values()):
                    print("모든 플레이어가 완료됨:", st.session_state.done_flags)
                    st.session_state.game_phase = "judgement"
                    print("game_phase 변경됨:", st.session_state.game_phase)
                    st.session_state.phase_changed = True  # phase 변경 플래그 추가
        st.rerun()

    if objection:
        st.session_state.turn = not st.session_state.turn  # 이의 제기 시 턴 전환
        role = "검사" if st.session_state.turn else "변호사"
        st.session_state.message_list.append({"role": role, "content": "이의 있음!"})
        st.rerun()

# 판결 단계
if st.session_state.game_phase == "judgement" or st.session_state.get("phase_changed", False):
    with st.chat_message("judge"):
        with st.spinner("AI 판사가 판단 중입니다..."):
            result = get_judge_result(st.session_state.message_list)
            st.write(result)
        st.session_state.game_phase = "done"

# 게임 종료 후 다시하기
if st.session_state.game_phase == "done":
    if st.button("🔁 다시하기"):
        for key in ["game_phase", "turn", "done_flags", "message_list", "mode", "witness_profiles", "case_initialized", "defendant_name", "phase_changed"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

