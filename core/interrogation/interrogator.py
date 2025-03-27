from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

def get_llm(model="gpt-4o"):
    """LLM 모델 가져오기"""
    llm = ChatOpenAI(model=model)  
    return llm

def ask_witness(question, name, wtype, case_summary, full_story="", previous_conversation=""):
    """참고인에게 질문하고 응답을 생성합니다."""
    llm = get_llm()
    
    # 피해자 정보 확인
    victim_name = ""
    victim_status = "unknown"
    for line in full_story.split("\n") if full_story else []:
        if line.startswith("[피해자 정보]:"):
            if "이름=" in line:
                try:
                    name_part = line.split("이름=")[1]
                    victim_name = name_part.split("|")[0] if "|" in name_part else name_part
                except:
                    pass
            if "상태=" in line:
                try:
                    status_part = line.split("상태=")[1]
                    victim_status = status_part.split("|")[0] if "|" in status_part else status_part
                except:
                    pass
            break
    
    # 해당 참고인이 피해자이고 사망한 상태인 경우 특별 처리
    if victim_name == name and victim_status.lower() == "사망":
        return f"죄송합니다만, {name}님은 사망한 피해자입니다. 따라서 참고인으로 증언할 수 없습니다."
    
    if wtype == "expert":
        context = f"""당신은 사건의 전문가 참고인 {name}입니다. 
        당신은 아래 사건에 대한 전문적인 분석과 의견을 제공하는 역할입니다.
        
        사건 개요:
        {case_summary}
        
        전문가로서 객관적이고 중립적인 의견을 제시하며, 사실에 근거한 전문적 분석을 제공하십시오.
        모르는 내용에 대해서는 정직하게 모른다고 답변하세요.
        답변은 반드시 2-3문장으로 간결하게 작성하세요. 불필요한 설명은 생략하고 핵심만 전달하세요.
        """
    else:
        # 관련자인 경우 전체 스토리도 참조
        context = f"""당신은 사건에 연루된 참고인 {name}입니다. 
        당신은 아래 사건에 대한 개인적인 관점과 경험을 가지고 있습니다.
        
        사건 개요(공개 정보):
        {case_summary}
        """
        
        if full_story:
            # 전체 스토리에서 이 참고인에 대한 정보 추출
            related_info = ""
            name_without_spaces = name.replace(" ", "")  # 공백 제거
            
            for line in full_story.split("\n"):
                # 다양한 방식으로 이름 포함 여부 확인
                if (f"이름={name}" in line or 
                    f"|이름={name}" in line or 
                    f"이름={name}|" in line or
                    f" {name} " in line and ("관련자" in line or "[관련자" in line)):
                    related_info = line
                    break
                    
                # 공백 없는 버전으로도 검색
                if (f"이름={name_without_spaces}" in line or 
                    f"|이름={name_without_spaces}" in line or 
                    f"이름={name_without_spaces}|" in line):
                    related_info = line
                    break
            
            # 관련자1, 관련자2, 피해자 정보 섹션 전체를 탐색
            if not related_info:
                for line in full_story.split("\n"):
                    # 관련자 또는 피해자 섹션에서 이 이름이 언급된 경우
                    if (name in line and 
                        (line.startswith("[관련자") or line.startswith("[피해자") or "관계=" in line)):
                        related_info = line
                        break
            
            # 관련자나 피해자 정보가 발견된 경우에만 처리
            if related_info:
                # 피해자 정보인 경우 해당 사람이 살아있는지 확인
                if "[피해자" in related_info:
                    if "상태=사망" in related_info or "사망" in related_info:
                        return f"죄송합니다만, {name}님은 사망한 피해자입니다. 따라서 참고인으로 증언할 수 없습니다."
                
                context += f"\n\n당신의 실제 상황(비공개 정보):\n{related_info}\n"
                
                # 이 참고인이 실제 범인인지 확인
                is_culprit = False
                for line in full_story.split("\n"):
                    if line.startswith("[진범]:") and name in line:
                        is_culprit = True
                        break
                
                if is_culprit:
                    context += "\n당신은 실제 범인이지만, 이 사실을 숨기고 있습니다. 자신의 결백을 주장하려고 합니다.\n"
        
        context += """
        귀하는 객관적 사실과 개인적 경험을 바탕으로 질문에 답변하십시오.
        당신이 실제로 알고 있는 정보만 공유하고, 추측성 발언은 피하세요.
        당신이 범인이라면 자신을 변호하려 할 것이고, 아니라면 아는 사실만 말할 것입니다.
        당신은 자신이 연루된 비밀이나 범행 관련성을 숨기려 할 수 있습니다.
        중요: 당신이 사망한 피해자라면, "저는 이미 사망했기 때문에 질문에 답할 수 없습니다."라고 응답하세요.
        답변은 반드시 2-3문장으로 간결하게 작성하세요. 불필요한 설명은 생략하고 핵심만 전달하세요.
        """
    
    # 이전 대화 내역이 있으면 추가
    if previous_conversation:
        context += f"""
        
        이전 대화 내역:
        {previous_conversation}
        
        위 대화 내역의 맥락을 유지하면서 질문에 답변하세요. 이전 답변과 일관성을 유지하되, 
        새로운 정보가 요청되면 적절히 제공하세요. 답변은 2-3문장으로 제한하세요.
        """

    prompt = ChatPromptTemplate.from_template("""
        {context}

        질문: {question}
        답변 (2-3문장으로 간결하게):
    """)

    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"question": question, "context": context})

def ask_defendant(question, defendant_name, case_summary, full_story="", previous_conversation=""):
    """피고인에게 질문하고 응답을 생성합니다."""
    llm = get_llm()
    
    context = f"""당신은 이 사건의 피고인 {defendant_name}입니다. 
    당신은 아래 사건에 대해 자신이 결백하다고 주장하며, 자신을 변호하려고 합니다.
    하지만 심리적으로는 불안하고 긴장되어 있을 수 있습니다.
    
    사건 개요(공개 정보):
    {case_summary}
    """
    
    if full_story:
        # 전체 스토리에서 용의자 정보와 진범 정보 추출
        suspect_info = ""
        real_culprit = ""
        name_without_spaces = defendant_name.replace(" ", "")  # 공백 제거
        
        # 용의자 정보 추출
        in_suspect_section = False
        suspect_section = ""
        
        for line in full_story.split("\n"):
            if line.startswith("[용의자 정보]:"):
                in_suspect_section = True
                suspect_section = line.split(":", 1)[1].strip()
            elif in_suspect_section and line.strip() and not line.startswith("["):
                suspect_section += " " + line
            elif in_suspect_section and line.startswith("["):
                break
            
            # 진범 정보 추출
            if line.startswith("[진범]:"):
                real_culprit = line.split(":", 1)[1].strip()
        
        if suspect_section:
            suspect_info = suspect_section
        
        if suspect_info:
            context += f"\n\n당신의 실제 상황(비공개 정보):\n{suspect_info}\n"
            
        # 피고인이 실제 범인인지 여부 파악 (다양한 방식으로 확인)
        is_culprit = False
        
        # 전체 이름 비교
        if real_culprit and defendant_name:
            # 1. 정확한 전체 이름 포함 확인
            if defendant_name in real_culprit:
                is_culprit = True
            # 2. 공백 제거 이름 확인
            elif name_without_spaces in real_culprit.replace(" ", ""):
                is_culprit = True
            # 3. 성+이름 부분 포함 확인
            else:
                name_parts = defendant_name.split()
                # 성이 하나라도 포함되고, 이름도 일부 포함됨
                if len(name_parts) > 1:
                    if name_parts[0] in real_culprit and any(part in real_culprit for part in name_parts[1:]):
                        is_culprit = True
        
        # 명시적으로 '용의자'가 범인이라고 언급된 경우
        if "용의자" in real_culprit.lower() and "맞" in real_culprit:
            is_culprit = True
            
        # 용의자 정보에 '범인이 맞다' 유형의 텍스트가 있는 경우
        if "범인이 맞" in suspect_info or "범행을 저질" in suspect_info or "실제로 죄를 지" in suspect_info:
            is_culprit = True
        
        if is_culprit:
            context += "\n당신은 실제 범인이지만, 자신의 결백을 주장하며 혐의를 부인하려 합니다. 증거에 대해 변명하거나 다른 이유를 대려고 합니다.\n"
        else:
            context += "\n당신은 실제로 무고합니다. 자신의 결백을 강하게 주장하세요. 당신의 알리바이를 설명하고 억울함을 표현하세요.\n"
    
    context += """
    당신은 자신의 무죄를 주장하지만, 너무 작위적이거나 인위적인 대답은 하지 않습니다.
    모든 질문에 대해 현실적이고 인간적인 반응을 보이세요.
    당신이 실제로 기억하는 바를 바탕으로 답변하고, 유죄 판결을 피하기 위해 노력하세요.
    답변은 반드시 2-3문장으로 간결하게 작성하세요. 불필요한 설명은 생략하고 핵심만 전달하세요.
    """
    
    # 이전 대화 내역이 있으면 추가
    if previous_conversation:
        context += f"""
        
        이전 대화 내역:
        {previous_conversation}
        
        위 대화 내역의 맥락을 유지하면서 질문에 답변하세요. 이전 답변과 일관성을 유지하되, 
        새로운 정보가 요청되면 적절히 제공하세요. 답변은 2-3문장으로 제한하세요.
        """

    prompt = ChatPromptTemplate.from_template("""
        {context}

        질문: {question}
        답변 (2-3문장으로 간결하게):
    """)

    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"question": question, "context": context})

def get_witness_profiles(case_summary):
    """참고인 프로필 생성"""
    llm = get_llm()
    prompt = ChatPromptTemplate.from_template("""
        다음 사건 개요를 바탕으로 게임에 등장할 참고인 3명의 프로필을 만들어주세요.
        참고인은 사건과 직접적으로 관련된 인물 2명(피해자, 목격자 등)과 전문가 1명(법의학자, 심리학자 등)으로 구성해주세요.
        
        사건 개요:
        {case_summary}
        
        다음 형식으로 각 참고인의 정보를 제공해주세요:

        참고인1:이름=홍길동|유형=character|배경=목격자
        참고인2:이름=김철수|유형=character|배경=피해자
        참고인3:이름=이전문|유형=expert|배경=법의학자
        
        각 참고인 정보는 새로운 줄에 제공하고, 정보 간에는 | 기호로 구분해주세요.
        다른 설명 없이 위 형식의 응답만 제공해주세요.
    """)
    
    chain = prompt | llm | StrOutputParser()
    response = chain.invoke({"case_summary": case_summary})
    
    # 텍스트 파싱
    witness_profiles = []
    try:
        lines = [line.strip() for line in response.split("\n") if line.strip()]
        for line in lines:
            if not line.startswith("참고인") or "=" not in line or "|" not in line:
                continue
                
            parts = line.split(":", 1)[1].split("|")
            profile = {}
            
            for part in parts:
                if "=" not in part:
                    continue
                key, value = part.split("=", 1)
                if key == "이름":
                    profile["name"] = value
                elif key == "유형":
                    profile["type"] = value
                elif key == "배경":
                    profile["background"] = value
            
            if "name" in profile and "type" in profile:
                witness_profiles.append(profile)
    except Exception:
        # 파싱에 실패한 경우 기본 프로필 사용
        witness_profiles = [
            {"name": "김민수", "type": "character", "background": "사건 목격자"},
            {"name": "박지연", "type": "character", "background": "관련자"},
            {"name": "박건우", "type": "expert", "background": "법의학 전문가"}
        ]
    
    # 프로필이 3개 미만이면 기본 프로필로 보충
    if len(witness_profiles) < 3:
        default_profiles = [
            {"name": "김민수", "type": "character", "background": "사건 목격자"},
            {"name": "박지연", "type": "character", "background": "관련자"},
            {"name": "박건우", "type": "expert", "background": "법의학 전문가"}
        ]
        witness_profiles.extend(default_profiles[:(3-len(witness_profiles))])
    
    return witness_profiles[:3]  # 최대 3개만 반환
