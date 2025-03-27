import streamlit as st
from dotenv import load_dotenv
import random

# 새 구조의 모듈들 임포트
from controller import initialize_game, generate_new_case, handle_judgment, reveal_truth
from controller import ask_witness_question, ask_defendant_question, reset_game_state

# 기존의 llm 모듈 임포트 (하위 호환성 유지)
from llm import get_judge_result, ask_witness, ask_defendant
from llm import get_full_case_story, get_case_overview, get_related_characters, get_truth_revelation

load_dotenv()

st.set_page_config(page_title="LogiCourt_AI", page_icon=":🤖:")
st.title("LogiCourt_AI")
st.caption("검사와 변호사가 주장하고, AI 판사가 판단합니다.")

# 게임 상태 초기화
initialize_game()

# 사건 개요 생성 단계
if st.session_state.game_phase == "init":
    # 이미 사건이 생성되었는지 확인
    if 'case_initialized' not in st.session_state:
        with st.spinner("사건을 생성 중입니다..."):
            # 컨트롤러를 통해 새 사건 생성
            generate_new_case()
        st.success("사건 생성 완료! 검사부터 시작하세요")
        
    # 어떤 경우든, 게임 단계는 debate로 변경
    st.session_state.game_phase = "debate"

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

# 메시지 출력
for i, message in enumerate(st.session_state.message_list):
    if i == 0 and message["role"] == "system":  # 첫 번째 메시지가 시스템(사건 개요)인 경우
        with st.expander("📜 사건 개요 및 증거", expanded=True):
            st.markdown(message["content"])
            
            # 사건 관련 인물 목록 추가
            if 'victim_name' in st.session_state and 'defendant_name' in st.session_state and 'witness_profiles' in st.session_state:
                st.markdown("---")
                st.markdown("### 📋 사건 관련 인물")
                
                # 피해자 정보
                victim_name = st.session_state.get('victim_name', '(정보 없음)')
                victim_desc = st.session_state.get('victim_desc', '피해자')
                st.markdown(f"**피해자**: {victim_name} - {victim_desc}")
                
                # 용의자 정보
                defendant_name = st.session_state.get('defendant_name', '(정보 없음)')
                defendant_desc = st.session_state.get('defendant_desc', '용의자')
                st.markdown(f"**용의자**: {defendant_name} - {defendant_desc}")
                
                # 참고인 정보
                st.markdown("**참고인**:")
                for witness in st.session_state.witness_profiles:
                    name = witness.get('name', '(정보 없음)')
                    background = witness.get('background', '관련자')
                    st.markdown(f"- {name} - {background}")
    else:
        with st.chat_message(message["role"]):
            st.write(message["content"])

# 참고인 호출 UI
if st.session_state.mode == "debate":
    # 용의자 정보 (이미 초기화 단계에서 추출됨)
    defendant_name = st.session_state.defendant_name
    
    # 유효한 참고인만 표시 (피해자 제외)
    valid_witnesses = st.session_state.witness_profiles
    
    # 사건 등장인물 소개 제거 (위에서 사건 개요와 함께 표시됨)
    
    # 4개 버튼 인터페이스로 표시 (용의자 + 최대 3명의 참고인)
    current_role = st.session_state.turn  # 현재 턴(검사/변호사)
    st.markdown(f"### 🔎 {current_role}의 질문하기")
    
    # 버튼 행 구성
    cols = st.columns(4)
    
    # 용의자 버튼 (항상 첫 번째)
    with cols[0]:
        if st.button(f"{defendant_name}", key="defendant_btn", use_container_width=True):
            st.session_state.mode = "defendant"
            st.session_state.defendant_name = defendant_name
            # 대화 기록은 유지 (새로고침 안함)
            if 'conversation_history' not in st.session_state:
                st.session_state.conversation_history = []
    
    # 참고인 버튼들
    for i, witness in enumerate(valid_witnesses[:3]):  # 최대 3명까지
        with cols[i+1]:
            icon = "👤" if witness['type'] == "character" else "🧠"
            if st.button(f"{icon} {witness['name']}", key=f"witness_{i}", use_container_width=True):
                st.session_state.mode = "witness"
                st.session_state.witness_name = witness['name']
                st.session_state.witness_type = witness['type']
                # 대화 기록은 유지 (새로고침 안함)
                if 'conversation_history' not in st.session_state:
                    st.session_state.conversation_history = []
    
    # 남은 칸이 있으면 빈 버튼 또는 메시지 표시
    for i in range(len(valid_witnesses) + 1, 4):
        with cols[i]:
            st.write("　")  # 빈 칸 (전각 공백)

# 참고인 질문 모드
if st.session_state.mode == "witness":
    witness_name = st.session_state.witness_name
    witness_type = st.session_state.witness_type
    case_summary = st.session_state.message_list[0]["content"] if st.session_state.message_list else ""
    full_story = st.session_state.full_story if "full_story" in st.session_state else ""
    
    # 현재 턴(검사/변호사) 표시
    current_role = st.session_state.turn
    
    st.markdown(f"### 📞 {current_role}가 {witness_name} 참고인과 대화 중입니다")
    
    # 대화 내역 표시 (항상 표시)
    with st.container():
        st.markdown("#### 대화 내역")
        if st.session_state.conversation_history:
            for msg in st.session_state.conversation_history:
                if msg["role"] == "user":
                    with st.chat_message(current_role):
                        st.write(msg["content"])
                else:
                    with st.chat_message("witness"):
                        st.write(msg["content"])
        else:
            st.info("아직 대화 내역이 없습니다. 질문을 입력해주세요.")
    
    # 대화 종료 버튼을 대화 내역 아래에 위치
    if st.button("🔙 대화 종료", type="primary"):
        # 전체 대화 내용을 채팅창에 표시
        if st.session_state.conversation_history:
            # 대화 내용을 채팅창에 표시
            for msg in st.session_state.conversation_history:
                role = current_role if msg["role"] == "user" else witness_name
                content = msg["content"]
                if msg["role"] == "user":
                    content = f"[{witness_name}에게] {content}"
                else:
                    content = f"[{witness_name}] {content}"
                
                st.session_state.message_list.append({"role": role, "content": content})
            
            # 요약 시스템 메시지 추가
            summary = f"[{current_role}의 {witness_name} 참고인 질문 완료]"
            st.session_state.message_list.append({"role": "system", "content": summary})
        
        # 대화 모드 종료
        st.session_state.mode = "debate"
        st.session_state.conversation_history = []  # 대화 기록 초기화
        st.rerun()
    
    # 대화 입력
    if q := st.chat_input(f"{current_role}의 {witness_name}에게 질문 입력..."):
        # 사용자 질문 표시 및 저장
        with st.chat_message(current_role):
            st.write(q)
        
        # 이전 대화 내역 포함하여 컨텍스트 구성
        previous_conversation = ""
        if st.session_state.conversation_history:
            for msg in st.session_state.conversation_history:
                role = "질문" if msg["role"] == "user" else "답변"
                previous_conversation += f"{role}: {msg['content']}\n"
        
        # 참고인 응답 생성 및 표시
        with st.chat_message("witness"):
            # 컨트롤러 함수 호출하여 응답 생성
            response = ask_witness_question(q, witness_name, witness_type, case_summary, full_story, previous_conversation)
            st.write(response)
        
        # 대화 내역 저장
        st.session_state.conversation_history.append({"role": "user", "content": q})
        st.session_state.conversation_history.append({"role": "witness", "content": response})
        
        st.rerun()

# 피고인 질문 모드
if st.session_state.mode == "defendant":
    defendant_name = st.session_state.defendant_name
    case_summary = st.session_state.message_list[0]["content"] if st.session_state.message_list else ""
    full_story = st.session_state.full_story if "full_story" in st.session_state else ""
    
    # 현재 턴(검사/변호사) 표시
    current_role = st.session_state.turn
    
    st.markdown(f"### ⚖️ {current_role}가 {defendant_name}과 대화 중입니다")
    
    # 대화 내역 표시 (항상 표시)
    with st.container():
        st.markdown("#### 대화 내역")
        if st.session_state.conversation_history:
            for msg in st.session_state.conversation_history:
                if msg["role"] == "user":
                    with st.chat_message(current_role):
                        st.write(msg["content"])
                else:
                    with st.chat_message("defendant"):
                        st.write(msg["content"])
        else:
            st.info("아직 대화 내역이 없습니다. 질문을 입력해주세요.")
    
    # 대화 종료 버튼을 대화 내역 아래에 위치
    if st.button("🔙 대화 종료", type="primary"):
        # 전체 대화 내용을 채팅창에 추가
        if st.session_state.conversation_history:
            # 대화 내용을 채팅창에 표시
            for msg in st.session_state.conversation_history:
                role = current_role if msg["role"] == "user" else defendant_name
                content = msg["content"]
                if msg["role"] == "user":
                    content = f"[{defendant_name}에게] {content}"
                else:
                    content = f"[{defendant_name}] {content}"
                
                st.session_state.message_list.append({"role": role, "content": content})
            
            # 요약 시스템 메시지 추가
            summary = f"[{current_role}의 {defendant_name} 피고인 질문 완료]"
            st.session_state.message_list.append({"role": "system", "content": summary})
        
        # 대화 모드 종료
        st.session_state.mode = "debate"
        st.session_state.conversation_history = []  # 대화 기록 초기화
        st.rerun()
    
    # 대화 입력
    if q := st.chat_input(f"{current_role}의 {defendant_name}에게 질문 입력..."):
        # 사용자 질문 표시 및 저장
        with st.chat_message(current_role):
            st.write(q)
        
        # 이전 대화 내역 포함하여 컨텍스트 구성
        previous_conversation = ""
        if st.session_state.conversation_history:
            for msg in st.session_state.conversation_history:
                role = "질문" if msg["role"] == "user" else "답변"
                previous_conversation += f"{role}: {msg['content']}\n"
        
        # 피고인 응답 생성 및 표시
        with st.chat_message("defendant"):
            # 컨트롤러 함수 호출하여 응답 생성
            response = ask_defendant_question(q, defendant_name, case_summary, full_story, previous_conversation)
            st.write(response)
        
        # 대화 내역 저장
        st.session_state.conversation_history.append({"role": "user", "content": q})
        st.session_state.conversation_history.append({"role": "defendant", "content": response})
        
        st.rerun()

# 사용자 주장 입력
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
            # 컨트롤러 함수 호출하여 판결 생성
            result = handle_judgment(st.session_state.message_list)
            st.write(result)
            st.session_state.judge_result = result
        st.session_state.game_phase = "reveal_truth"

# 진실 공개 단계
if st.session_state.game_phase == "reveal_truth":
    with st.chat_message("system"):
        with st.spinner("사건의 진실을 밝히는 중입니다..."):
            # 컨트롤러 함수 호출하여 진실 공개 메시지 생성
            truth = reveal_truth(st.session_state.full_story, st.session_state.judge_result)
            st.write(truth)
        st.session_state.game_phase = "done"

# 게임 종료 후 다시하기
if st.session_state.game_phase == "done":
    if st.button("🔁 다시하기"):
        # 컨트롤러 함수 호출하여 게임 상태 초기화
        reset_game_state()
        st.rerun()
