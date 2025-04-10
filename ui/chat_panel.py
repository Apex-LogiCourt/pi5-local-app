# streamlit run ui/st_chat_panel.py로 실행행
import sys
import os
import streamlit as st
from dotenv import load_dotenv
import random

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.controller import make_witness_profiles, make_case_summary
from core.controller import get_judge_result_wrapper as get_judge_result
from core.controller import ask_witness_wrapper as ask_witness
from core.controller import ask_defendant_wrapper as ask_defendant

load_dotenv()

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

# 사건 개요 생성 단계
if st.session_state.game_phase == "init":
    if 'case_initialized' not in st.session_state:
        with st.spinner("사건을 생성 중입니다..."):
            case_summary = make_case_summary()
            st.session_state.message_list.append({"role": "system", "content": case_summary})
            witness_profiles = make_witness_profiles(case_summary)
            st.session_state.witness_profiles = witness_profiles
            st.session_state.case_initialized = True
        st.success("사건 생성 완료! 검사부터 시작하세요")
    st.session_state.game_phase = "debate"

# ✅ 사이드바에 사건 개요 & 증거물 분리 (접었다 펼 수 있게)
if st.session_state.message_list and st.session_state.message_list[0]["role"] == "system":
    full_summary = st.session_state.message_list[0]["content"]
    lines = full_summary.split("\n")

    summary_lines = []
    evidence_lines = []

    capture = None
    for line in lines:
        if "[사건 제목]" in line or "[사건 배경]" in line or "[사건 개요]" in line or "[용의자 정보]" in line:
            capture = "summary"
            summary_lines.append(line)
        elif "[검사 측 증거]" in line or "[변호사 측 증거]" in line:
            capture = "evidence"
            evidence_lines.append(line)
        elif capture == "summary":
            summary_lines.append(line)
        elif capture == "evidence":
            evidence_lines.append(line)

    with st.sidebar:
        if summary_lines:
            with st.expander("📜 사건 개요", expanded=True):
                st.markdown("\n".join(summary_lines))
        if evidence_lines:
            with st.expander("🧾 증거물", expanded=False):
                st.markdown("\n".join(evidence_lines))

# 이전 턴 처리 후 턴 전환
if 'last_turn_input' in st.session_state:
    prev = st.session_state.last_turn_input
    last_msg = st.session_state.message_list[-1]["content"].strip().lower()
    if last_msg == "이상입니다":
        st.session_state.done_flags[prev] = True
        if all(st.session_state.done_flags.values()):
            st.session_state.game_phase = "judgement"
        else:
            st.session_state.turn = "변호사" if prev == "검사" else "검사"
    else:
        st.session_state.turn = "변호사" if prev == "검사" else "검사"
    del st.session_state.last_turn_input

# 나머지 메시지 출력
for i, message in enumerate(st.session_state.message_list):
    if i == 0 and message["role"] == "system":
        continue  # 사건 개요는 사이드바에 출력되므로 건너뜀
    with st.chat_message(message["role"]):
        st.write(message["content"])

# 참고인 호출 UI
if st.session_state.mode == "debate":
    if 'defendant_name' not in st.session_state and st.session_state.message_list:
        case_summary = st.session_state.message_list[0]["content"]
        for line in case_summary.split("\n"):
            if "[용의자 정보]:" in line or "[용의자]:" in line:
                try:
                    st.session_state.defendant_name = line.split(":", 1)[1].strip().split()[0]
                except:
                    st.session_state.defendant_name = "피고인"
                break
        if 'defendant_name' not in st.session_state:
            st.session_state.defendant_name = "피고인"
    
    # 이의 사용 횟수 초기화
    if "objection_count" not in st.session_state:
        st.session_state.objection_count = 0  # 최대 2회 허용
    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        with st.expander("🔎 참고인 호출하기"):
            st.markdown("**어떤 참고인을 호출하시겠습니까?**")
            cols = st.columns(len(st.session_state.witness_profiles))
            for i, witness in enumerate(st.session_state.witness_profiles):
                with cols[i]:
                    label = f"👤 {witness['name']}" if witness['type'] == "character" else f"🧠 {witness['name']}"
                    if st.button(label, key=f"w{i}"):
                        st.session_state.mode = "witness"
                        st.session_state.witness_name = witness['name']
                        st.session_state.witness_type = witness['type']
    
    with col2:
        defendant_name = st.session_state.get('defendant_name', '피고인')
        if st.button(f"👨‍⚖️ {defendant_name}에게 질문하기"):
            st.session_state.mode = "defendant"
            st.session_state.defendant_name = defendant_name

    with col3:
        if st.button("🚨 이의 있습니다!", use_container_width=True):
            if "objection_count" not in st.session_state:
                st.session_state.objection_count = 0

            if st.session_state.objection_count >= 2:
                st.warning("❗ 더 이상 이의 제기할 수 없습니다.")
            else:
                opponent = "변호사" if st.session_state.turn == "검사" else "검사"
                st.session_state.message_list.append({
                    "role": opponent,
                    "content": "이의 있습니다!"
                })
                st.session_state.message_list.append({
                    "role": "judge",
                    "content": "이의, 받아들입니다."
                })
                st.session_state.objection_count += 1
                st.session_state.last_turn_input = st.session_state.turn
                st.rerun()

# 참고인 질문 모드
if st.session_state.mode == "witness":
    witness_name = st.session_state.witness_name
    witness_type = st.session_state.witness_type
    case_summary = st.session_state.message_list[0]["content"] if st.session_state.message_list else ""
    
    st.markdown(f"**📞 {witness_name} 참고인에게 질문하세요.** (질문 1회)")
    if q := st.chat_input("참고인에게 질문 입력..."):
        with st.chat_message("user"): st.write(q)
        with st.chat_message("witness"):
            response = ask_witness(q, witness_name, witness_type, case_summary)
            st.write(response)
        st.session_state.message_list.append({"role": "user", "content": f"[참고인 질문: {q}]"})
        st.session_state.message_list.append({"role": "witness", "content": response})
        st.session_state.mode = "debate"
        st.rerun()

# 피고인 질문 모드
if st.session_state.mode == "defendant":
    defendant_name = st.session_state.defendant_name
    case_summary = st.session_state.message_list[0]["content"] if st.session_state.message_list else ""
    
    st.markdown(f"**⚖️ {defendant_name}에게 질문하세요.**")
    if q := st.chat_input(f"{defendant_name}에게 질문 입력..."):
        with st.chat_message("user"): st.write(q)
        with st.chat_message("defendant"):
            response = ask_defendant(q, defendant_name, case_summary)
            st.write(response)
        st.session_state.message_list.append({"role": "user", "content": f"[피고인 질문: {q}]"})
        st.session_state.message_list.append({"role": "defendant", "content": response})
        st.session_state.mode = "debate"
        st.rerun()

# ✅ 사용자 주장 입력 (항상 하단에 위치)
if st.session_state.mode == "debate" and st.session_state.game_phase == "debate":
    if user_input := st.chat_input(f"{st.session_state.turn.upper()}의 주장을 입력하세요 (이상입니다 입력 시 종료)"):
        role = st.session_state.turn
        with st.chat_message(role):
            st.write(user_input)
        st.session_state.message_list.append({"role": role, "content": user_input})
        st.session_state.last_turn_input = role
        st.rerun()



# 판결 단계
if st.session_state.game_phase == "judgement":
    with st.chat_message("judge"):
        with st.spinner("AI 판사가 판단 중입니다..."):
            result = get_judge_result(st.session_state.message_list)
            st.write(result)
        st.session_state.game_phase = "done"

# 게임 종료 후 다시하기
if st.session_state.game_phase == "done":
    if st.button("🔁 다시하기"):
        for key in ["game_phase", "turn", "done_flags", "message_list", "mode", "witness_profiles", "case_initialized", "defendant_name"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
