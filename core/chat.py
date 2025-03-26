import streamlit as st
from dotenv import load_dotenv
from llm import get_ai_response, get_judge_result, get_case_summary, ask_witness, get_witness_profiles, ask_defendant
from llm import get_full_case_story, get_case_overview, get_related_characters, get_truth_revelation
import random
from config import CASE_EXAMPLES
from llm import make_case_judgment_prompt, ask_llm


load_dotenv()

st.set_page_config(page_title="LogiCourt_AI", page_icon=":🤖:")
st.title("LogiCourt_AI")
st.caption("검사와 변호사가 주장하고, AI 판사가 판단합니다.")

# 초기 상태 설정
if 'game_phase' not in st.session_state:
    st.session_state.game_phase = "init"  # init, debate, judgement, reveal_truth
    st.session_state.turn = "검사"
    st.session_state.done_flags = {"검사": False, "변호사": False}
    st.session_state.message_list = []
    st.session_state.mode = "debate"  # debate, witness, defendant
    st.session_state.conversation_history = []  # 참고인/피고인과의 대화 내역 저장

# 사건 개요 생성 단계
if st.session_state.game_phase == "init":
    # 이미 사건이 생성되었는지 확인
    if 'case_initialized' not in st.session_state:
        with st.spinner("사건을 생성 중입니다..."):
            # 전체 스토리 생성
            full_story = get_full_case_story()
            st.session_state.full_story = full_story
            
            # 피해자 정보 추출
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
            
            # 용의자 정보 추출 (전체 스토리에서 추출)
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
            
            # 게임 시작용 개요만 추출
            case_summary = get_case_overview(full_story)
            st.session_state.message_list.append({"role": "system", "content": case_summary})
            
            # 이미 추출된 등장인물 이름 저장
            used_names = []
            if suspect_name:
                used_names.append(suspect_name)
            if victim_name:
                used_names.append(victim_name)

            # 사건 관련자 2명만 추출 
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
            
            # 전문가 1명 추가 (다양한 이름과 직업 사용)
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
            
            # 참고인 목록 구성 (관련자 2명 + 전문가 1명)
            witness_profiles = related_characters + [expert]
            
            # 최종 안전 검사: 모든 참고인이 서로 다른 이름을 가지도록 확인
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
                
            # 피해자 정보 기록 (참고용)
            if victim_name and victim_status == "사망":
                st.session_state.message_list.append({
                    "role": "system",
                    "content": f"[참고 정보: 피해자 {victim_name}(은)는 사망했습니다. 따라서 참고인으로 등장할 수 없습니다.]"
                })
            
            st.session_state.witness_profiles = witness_profiles
            
            # 사건이 초기화되었음을 표시
            st.session_state.case_initialized = True
            
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
            response = ask_witness(q, witness_name, witness_type, case_summary, full_story, previous_conversation)
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
            response = ask_defendant(q, defendant_name, case_summary, full_story, previous_conversation)
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
            result = get_judge_result(st.session_state.message_list)
            st.write(result)
            st.session_state.judge_result = result
        st.session_state.game_phase = "reveal_truth"

# 진실 공개 단계
if st.session_state.game_phase == "reveal_truth":
    with st.chat_message("system"):
        with st.spinner("사건의 진실을 밝히는 중입니다..."):
            truth = get_truth_revelation(st.session_state.full_story, st.session_state.judge_result)
            st.write(truth)
        st.session_state.game_phase = "done"

# 게임 종료 후 다시하기
if st.session_state.game_phase == "done":
    if st.button("🔁 다시하기"):
        for key in ["game_phase", "turn", "done_flags", "message_list", "mode", "witness_profiles", "case_initialized", "defendant_name", "full_story", "judge_result"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
