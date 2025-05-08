import streamlit as st
from dotenv import load_dotenv
import asyncio
from game_controller import GameController

load_dotenv()

st.set_page_config(page_title="LogiCourt_AI", page_icon=":🤖:")
st.title("LogiCourt_AI")
st.caption("검사와 변호사가 주장하고, AI 판사가 판단합니다.")

# GameController 초기화
if 'game_controller' not in st.session_state:
    st.session_state.game_controller = GameController()

def display_message(message):
    actual_role = message.get("metadata", {}).get("actual_role", message["role"])
    with st.chat_message(actual_role):
        st.write(message["content"])


def process_user_input(user_input):
    """사용자 입력을 처리합니다."""
    result = st.session_state.game_controller.process_input(user_input)
    st.session_state.game_controller.add_message(result["role"], result["content"])
    if result["should_change_turn"]:
        st.session_state.game_controller.change_turn()
    if result["phase_changed"]:
        st.session_state.phase_changed = True
    st.rerun()

def initialize_case():
    """사건을 초기화합니다."""
    with st.spinner("사건을 생성 중입니다..."):
        placeholder = st.empty()
        def update_ui(content, full_text):
            placeholder.markdown(f"{full_text}▌")
        asyncio.run(st.session_state.game_controller.initialize_case(callback=update_ui))
        placeholder.empty()
    st.success("사건 생성 완료! 검사부터 시작하세요")
    st.session_state.game_controller.game_phase = "debate"

# 사건 개요 생성 단계
if st.session_state.game_controller.game_phase == "init":
    initialize_case()

# 메시지 출력
for i, message in enumerate(st.session_state.game_controller.message_list):
    if i > 1:
        display_message(message)

# 사이드바에 사건 정보 표시
if (
    st.session_state.game_controller.game_phase != "init"
    and st.session_state.game_controller.message_list
    and len(st.session_state.game_controller.message_list) > 1
):
    with st.sidebar:
        with st.expander("📜 사건 개요", expanded=True):
            st.markdown(st.session_state.game_controller.message_list[0]["content"])
        with st.expander("🕵️ 등장인물", expanded=True):
            st.markdown(st.session_state.game_controller.message_list[1]["content"])

# 사용자 주장 입력
if st.session_state.game_controller.mode == "debate" and st.session_state.game_controller.game_phase == "debate":
    col1, col2 = st.columns([8, 2])
    with col1:
        current_role = "검사" if st.session_state.game_controller.turn else "변호사"
        user_input = st.text_input(
            "주장 입력",
            key=f"chat_input_{st.session_state.game_controller.turn}_{len(st.session_state.game_controller.message_list)}",
            placeholder=f"{current_role.upper()}의 주장을 입력하세요 (이상입니다 입력 시 종료)",
            label_visibility="collapsed"
        )
    with col2:
        objection = st.button(
            "🚨이의 있음!",
            key="objection_button",
            use_container_width=True,
            disabled=st.session_state.game_controller.game_phase != "debate" or 
                    st.session_state.game_controller.done_flags["변호사" if st.session_state.game_controller.turn else "검사"]
        )

    # 메시지 입력 처리
    if user_input:
        process_user_input(user_input)

    # 이의제기 처리
    if objection:
        result = st.session_state.game_controller.process_objection()
        st.session_state.game_controller.add_message(result["role"], result["content"])
        st.session_state.game_controller.change_turn()
        st.rerun()

# 판결 단계
if st.session_state.game_controller.game_phase == "judgement":
    with st.chat_message("judge"):
        with st.spinner("AI 판사가 판단 중입니다..."):
            result = st.session_state.game_controller.get_judge_result()
            st.write(result)
        st.session_state.game_controller.game_phase = "done"

# 게임 종료 후 다시하기
if st.session_state.game_controller.game_phase == "done":
    if st.button("🔁 다시하기"):
        st.session_state.game_controller.reset()
        st.rerun()

