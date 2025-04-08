import streamlit as st

# ✅ 세션 상태 초기화는 최상단에 위치
st.session_state.witness_name = st.session_state.get("witness_name", "")
st.session_state.witness_type = st.session_state.get("witness_type", "")
st.session_state.defendant_name = st.session_state.get("defendant_name", "피고인")
st.session_state.mode = st.session_state.get("mode", "debate")
st.session_state.case_initialized = st.session_state.get("case_initialized", False)
st.session_state.message_list = st.session_state.get("message_list", [])
st.session_state.game_phase = st.session_state.get("game_phase", "init")
st.session_state.turn = st.session_state.get("turn", "검사")
st.session_state.done_flags = st.session_state.get("done_flags", {"검사": False, "변호사": False})
st.session_state.last_turn_input = st.session_state.get("last_turn_input", None)
st.session_state.witness_profiles = st.session_state.get("witness_profiles", [])
st.session_state.conversation_history = st.session_state.get("conversation_history", {})
st.session_state.case_context = st.session_state.get("case_context", "")

from dotenv import load_dotenv
import random

from controller import get_witness_profiles, get_case_summary
from controller import get_judge_result_wrapper as get_judge_result
from controller import ask_witness_wrapper as ask_witness
from controller import ask_defendant_wrapper as ask_defendant

load_dotenv()

st.set_page_config(page_title="LogiCourt_AI", page_icon=":🤖:")
st.title("LogiCourt_AI")
st.caption("검사와 변호사가 주장하고, AI 판사가 판단합니다.")

# 사건 개요 생성 단계
if st.session_state.game_phase == "init":
    with st.spinner("사건을 생성 중입니다..."):
        case_summary = get_case_summary()
        st.session_state.message_list.append({"role": "system", "content": case_summary})
        st.session_state.case_context = case_summary
        witness_profiles = get_witness_profiles(case_summary)
        st.session_state.witness_profiles = witness_profiles
        st.session_state.case_initialized = True
        # 각 참고인별 대화 기록 초기화
        for witness in witness_profiles:
            st.session_state.conversation_history[witness['name']] = []
        # 피고인의 대화 기록도 초기화
        st.session_state.conversation_history[st.session_state.defendant_name] = []
    st.success("사건 생성 완료! 검사로부터 시작하세요")
    st.session_state.game_phase = "debate"

# 이전 턴 처리 후 턴 전환
if st.session_state.last_turn_input:
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
    st.session_state.last_turn_input = None

# 메시지 출력
for i, message in enumerate(st.session_state.message_list):
    if i == 0 and message["role"] == "system":
        with st.expander("📜 사건 개요 및 증거", expanded=True):
            st.markdown(message["content"])
    else:
        with st.chat_message(message["role"]):
            st.write(message["content"])

# 참고인 호출 UI
if st.session_state.mode == "debate":
    case_summary = st.session_state.message_list[0]["content"]
    for line in case_summary.split("\n"):
        if "[용의자 정보]:" in line or "[용의자]:" in line:
            try:
                st.session_state.defendant_name = line.split(":", 1)[1].strip().split()[0]
            except:
                st.session_state.defendant_name = "피고인"
            break

    with st.expander("🔎 참고인 호출하기"):
        st.markdown("**어느 참고인을 호출하시겠습니까?**")
        cols = st.columns(len(st.session_state.witness_profiles))
        for i, witness in enumerate(st.session_state.witness_profiles):
            with cols[i]:
                if witness['type'] == "witness":
                    label = f"👁️ {witness['name']} (목격자)"
                elif witness['type'] == "reference":
                    label = f"👤 {witness['name']} (참고인)"
                else:  # defendant
                    label = f"⚖️ {witness['name']} (피고인)"
                if st.button(label, key=f"w{i}"):
                    st.session_state.mode = "witness"
                    st.session_state.witness_name = witness['name']
                    st.session_state.witness_type = witness['type']

# 참고인 질문 모드
if st.session_state.mode == "witness":
    witness_name = st.session_state.witness_name
    witness_type = st.session_state.witness_type
    case_summary = st.session_state.case_context
    conversation_history = st.session_state.conversation_history[witness_name]
    
    st.markdown(f"**📞 {witness_name} 참고인에게 질문하세요.** (질문 1회)")
    if q := st.chat_input("참고인에게 질문 입력..."):
        with st.chat_message("user"): st.write(q)
        with st.chat_message("witness"):
            # 이전 대화 기록과 사건 맥락을 함께 전달
            response = ask_witness(q, witness_name, witness_type, case_summary, conversation_history)
            st.write(response)
        
        # 대화 기록 업데이트
        conversation_history.append({"role": "user", "content": q})
        conversation_history.append({"role": "witness", "content": response})
        st.session_state.conversation_history[witness_name] = conversation_history
        
        st.session_state.message_list.append({"role": "user", "content": f"[{witness_name} 참고인 질문: {q}]"})
        st.session_state.message_list.append({"role": "witness", "content": response})
        st.session_state.mode = "debate"
        st.rerun()

# 피고인 질문 모드
if st.session_state.mode == "defendant":
    defendant_name = st.session_state.defendant_name
    case_summary = st.session_state.case_context
    conversation_history = st.session_state.conversation_history[defendant_name]
    
    st.markdown(f"**⚖️ {defendant_name}에게 질문하세요.**")
    if q := st.chat_input(f"{defendant_name}에게 질문 입력..."):
        with st.chat_message("user"): st.write(q)
        with st.chat_message("defendant"):
            # 이전 대화 기록과 사건 맥락을 함께 전달
            response = ask_defendant(q, defendant_name, case_summary, conversation_history)
            st.write(response)
        
        # 대화 기록 업데이트
        conversation_history.append({"role": "user", "content": q})
        conversation_history.append({"role": "defendant", "content": response})
        st.session_state.conversation_history[defendant_name] = conversation_history
        
        st.session_state.message_list.append({"role": "user", "content": f"[{defendant_name} 질문: {q}]"})
        st.session_state.message_list.append({"role": "defendant", "content": response})
        st.session_state.mode = "debate"
        st.rerun()

# 사용자 주장 입력 + 커맨드 인식
if st.session_state.mode == "debate" and st.session_state.game_phase == "debate":
    if user_input := st.chat_input(f"{st.session_state.turn.upper()}의 주장을 입력하세요 (요청합니다 / 이상입니다 명령어 사용 가능)"):
        role = st.session_state.turn
        with st.chat_message(role):
            st.write(user_input)

        lower_input = user_input.strip().lower()

        if "이상입니다" in lower_input:
            st.session_state.message_list.append({"role": role, "content": "이상입니다"})
            st.session_state.done_flags[role] = True
            st.session_state.last_turn_input = role
            st.rerun()

        elif "요청합니다" in lower_input:
            st.session_state.message_list.append({"role": role, "content": "참고인을 요청합니다."})
            st.session_state.mode = "witness_selection"
            st.rerun()

        else:
            st.session_state.message_list.append({"role": role, "content": user_input})
            st.session_state.last_turn_input = role
            st.rerun()

# 참고인 선택 모드
if st.session_state.mode == "witness_selection":
    st.markdown("**어느 참고인을 호출하시겠습니까?**")
    cols = st.columns(len(st.session_state.witness_profiles))
    for i, witness in enumerate(st.session_state.witness_profiles):
        with cols[i]:
            if witness['type'] == "witness":
                label = f"👁️ {witness['name']} (목격자)"
            elif witness['type'] == "reference":
                label = f"👤 {witness['name']} (참고인)"
            else:  # defendant
                label = f"⚖️ {witness['name']} (피고인)"
            if st.button(label, key=f"w{i}"):
                st.session_state.mode = "witness"
                st.session_state.witness_name = witness['name']
                st.session_state.witness_type = witness['type']
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
        for key in st.session_state:
            if key not in ["witness_name", "witness_type", "defendant_name", "mode", "case_initialized", "message_list", "game_phase", "turn", "done_flags", "last_turn_input", "witness_profiles", "conversation_history", "case_context"]:
                del st.session_state[key]
        st.rerun()
