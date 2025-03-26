from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate , MessagesPlaceholder, FewShotChatMessagePromptTemplate
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore 

from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

from config import answer_examples

store = {}

def get_session_history(session_id):
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

def get_retriever():
    embedding = OpenAIEmbeddings(model="text-embedding-3-large")
    index_name = 'tax-index'
    database = PineconeVectorStore.from_existing_index(index_name=index_name, embedding=embedding)
    retriever = database.as_retriever(search_kwargs={'k' : 4})
    return retriever

def get_history_aware_retriever():
    llm = get_llm()
    retriever = get_retriever()

    contextualize_q_system_prompt = (
        "Given a chat history and the latest user question "
        "두괄식으로 대답해주세요"
        "which might reference context in the chat history, "
        "formulate a standalone question which can be understood "
        "without the chat history. Do NOT answer the question, "
        "just reformulate it if needed and otherwise return it as is."
    )

    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )
    history_aware_retriever = create_history_aware_retriever(
        llm, retriever, contextualize_q_prompt
    )
    return history_aware_retriever

def get_llm(model="gpt-4o"):
    llm = ChatOpenAI(model=model)  
    return llm

def get_dictionary_chain():
    dictionary = ["사람을 나타내는 표현 -> 거주자"]
    llm = get_llm()
    prompt = ChatPromptTemplate.from_template(f"""
        사용자의 질문을 보고, 우리의 사전을 참고해서 사용자의 질문을 변경해주세요.
        만약 변경할 필요가 없다고 판단되면, 사용자의 질문을 변경하지 않아도 됩니다.
        사전: {dictionary}

        질문: {{question}}
    """)

    dictionary_chain = prompt | llm | StrOutputParser()

    return dictionary_chain

def get_rag_chain():
    llm = get_llm()    

    example_prompt = ChatPromptTemplate.from_messages(
        [
            ("human", "{input}"),
            ("ai", "{answer}"),
        ]
    )

    few_shot_prompt = FewShotChatMessagePromptTemplate(
        example_prompt=example_prompt,
        examples=answer_examples,
        input_variables=["input"]
    )

    system_prompt = (
        "2-3 문장정도의 짧은 내용의 답변을 원합니다."
        "\n\n"
        "{context}"
    )
    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            few_shot_prompt,
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )
    history_aware_retriever = get_history_aware_retriever()
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)

    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    conversation_rag_chain = RunnableWithMessageHistory(
        rag_chain, 
        get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key="answer",
    ).pick("answer")

    return conversation_rag_chain

def get_ai_response(user_message):
    dictionary_chain = get_dictionary_chain()
    rag_chain = get_rag_chain()
    tax_chain = {"input":dictionary_chain} | rag_chain
    ai_response = tax_chain.stream(
        {
            "question": user_message
        },
        config={
            "configurable": {"session_id": "123"}
        }
    )

    return ai_response

def get_case_summary():
    llm = get_llm()
    prompt = ChatPromptTemplate.from_template("""
        다음 형식에 맞춰 재판 게임을 위한 사건 개요와 증거를 생성해주세요.
        사건 개요는 더 구체적이고 현실적이며, 용의자와 피해자의 관계, 사건 상황, 배경 등을 포함해주세요.
        사건의 전후 맥락을 명확히 설명하고, 각 증거가 사건과 어떻게 연결되는지 논리적으로 설명해주세요.

        [사건 제목]: (간단한 제목)
        [사건 배경]: (사건 발생 이전의 상황, 인물들의 관계 등 2-3문장)
        [사건 개요]: (3-4문장으로 상세한 사건 설명)
        [용의자 정보]: (용의자의 신상정보, 동기, 알리바이 등)
        [검사 측 증거]:
        1. (검사 측 증거 1과 이 증거가 사건과 어떻게 연결되는지)
        2. (검사 측 증거 2와 이 증거가 사건과 어떻게 연결되는지)
        3. (검사 측 증거 3과 이 증거가 사건과 어떻게 연결되는지)
        [변호사 측 증거]:
        1. (변호사 측 증거 1과 이 증거가 용의자의 무죄를 어떻게 뒷받침하는지)
        2. (변호사 측 증거 2와 이 증거가 용의자의 무죄를 어떻게 뒷받침하는지)
        3. (변호사 측 증거 3과 이 증거가 용의자의 무죄를 어떻게 뒷받침하는지)
        [핵심 쟁점]: (이 사건의 핵심 쟁점 2-3가지)
    """)

    chain = prompt | llm | StrOutputParser()
    return chain.invoke({})

def get_judge_result(message_list):
    llm = get_llm()
    prompt = ChatPromptTemplate.from_template("""
        당신은 공정한 AI 판사입니다. 아래는 검사와 변호사의 주장 및 증거입니다. 
        이 정보를 바탕으로 누가 더 논리적이고 설득력 있는 주장을 했는지 판단해주세요.
        그 이유도 간단히 설명해주세요.

        [전체 대화 내용]:
        {messages}

        판결 형식:
        [승자]: (검사 또는 변호사)
        [판결 이유]: (간단하고 논리적인 이유)
    """)

    messages_joined = "\n".join([f"[{m['role']}]: {m['content']}" for m in message_list if m['role'] in ['검사', '변호사']])
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"messages": messages_joined})

def get_truth_revelation(full_story, judge_result):
    """판결 후 진실을 공개하는 메시지를 생성합니다."""
    llm = get_llm()
    prompt = ChatPromptTemplate.from_template("""
        다음 전체 스토리와 판결 결과를 바탕으로, 사건의 진실을 공개하는 메시지를 작성해주세요.
        이 메시지는 게임이 끝난 후 플레이어에게 실제 사건의 진실을 알려주는 역할을 합니다.
        
        전체 스토리:
        {full_story}
        
        판결 결과:
        {judge_result}
        
        진실 공개 메시지는 다음 형식으로 작성해주세요:
        
        [사건의 진실]
        (실제로 어떤 일이 있었는지 상세히 설명)
        
        [실제 범인]
        (누가 범인이었는지, 또는 용의자가 정말 범인이었는지)
        
        [결정적 증거]
        (범행을 결정적으로 증명하는 증거와 그 의미)
        
        [판결의 정확성]
        (판사의 판결이 실제 진실에 얼마나 부합했는지)
    """)
    
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"full_story": full_story, "judge_result": judge_result})

def ask_witness(question, name, wtype, case_summary, full_story="", previous_conversation=""):
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

def make_case_judgment_prompt(case: dict) -> str:
    return f"""
당신은 AI 판사입니다. 아래 사건 설명을 바탕으로 용의자의 유죄 여부에 대한 판단을 내려주세요.

[사건 제목]: {case['title']}
[사건 설명]: {case['description']}
[용의자]: {case['suspect']}
[논쟁의 핵심]: {case['hint']}

이 사람이 유죄라고 판단되는 이유 또는 무죄라고 판단되는 이유를 설명한 뒤,
마지막에 '판단: 유죄' 또는 '판단: 무죄'로 정리해 주세요.
""".strip()


def ask_llm(prompt: str):
    llm = get_llm()
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", "당신은 공정하고 논리적인 AI 판사입니다."),
        ("human", "{prompt}")
    ])
    chain = prompt_template | llm | StrOutputParser()
    return chain.invoke({"prompt": prompt})

def get_witness_profiles(case_summary):
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

def get_full_case_story():
    llm = get_llm()
    prompt = ChatPromptTemplate.from_template("""
        다음 형식에 맞춰 재판 게임을 위한 완전한 범죄 스토리를 생성해주세요.
        이 스토리는 게임 종료 후 실제 사건의 진실을 공개하는 데 사용됩니다.
        범죄 스토리는 범인이 누구인지, 실제로 어떤 일이 일어났는지, 증거가 어떻게 해석되는지 등 모든 진실을 담아야 합니다.

        등장인물들은 다양한 이름을 가져야 합니다. 모든 등장인물의 이름은 완전히 달라야 합니다.
        흔한 이름(홍길동, 김철수 등)은 사용하지 말고 독특하고 현실적인 이름을 사용해주세요.
        피해자, 용의자, 목격자, 관련자 등 모든 등장인물의 이름은 서로 달라야 합니다.
        성씨도 다양하게 사용해주세요. 특히 관련자1과 관련자2, 그리고 용의자의 이름은 서로 완전히 달라야 합니다.
        절대로 강민준, 정하늘 같은 이름은 사용하지 마세요(실제 사건과 혼동될 수 있음).
        사망한 피해자와 생존한 목격자/관련자의 이름이 같으면 안 됩니다.
        
        독특한 이름을 사용해주세요. 모든 등장인물의 이름은 성과 이름을 모두 포함해야 합니다.
        예시 이름: 백도현, 임지은, 손예진, 오현우, 노은서, 진승호, 권나라, 류태민, 장서윤 등
        
        [사건 제목]: (간단한 제목)
        [전체 스토리]: (사건의 실제 진실을 모두 담은 상세한 설명, 5-6문장)
        [진범]: (실제 범인이 누구인지, 만약 용의자가 범인이 아니라면 누가 범인인지)
        [동기]: (범행의 동기)
        [결정적 증거]: (범인을 가리키는 결정적 증거와 그 의미)
        [피해자 정보]: (이름=피해자이름 | 설명=피해자에 대한 설명)
        [용의자 정보]: (이름:고유한용의자이름 | 나이=?? | 직업=??)
        [관련자1]: (이름=고유한이름1|관계=목격자 또는 기타 관계|나이=??|비밀=...)
        [관련자2]: (이름=고유한이름2|관계=목격자 또는 기타 관계|나이=??|비밀=...)
        
        관련자들은 사건과 밀접한 관계가 있으며, 각자 숨기고 있는 비밀이나 동기가 있어야 합니다.
        용의자가 실제 범인일 수도 있고, 무고할 수도 있습니다.
        모든 등장인물의 이름은 성과 이름을 모두 포함하고 서로 완전히 달라야 합니다.
        피해자가 관련자로 중복 등장하지 않도록 해주세요. 특히 피해자가 사망한 경우 참고인으로 등장할 수 없습니다.
    """)

    chain = prompt | llm | StrOutputParser()
    return chain.invoke({})

def get_case_overview(full_story):
    """전체 스토리에서 게임 시작용 개요만 추출합니다."""
    llm = get_llm()
    
    # 피해자 정보 추출
    victim_info = ""
    for line in full_story.split("\n"):
        if line.startswith("[피해자 정보]:"):
            victim_info = line
            break
    
    # 피해자 정보가 없으면 전체 스토리에서 찾기
    if not victim_info:
        for line in full_story.split("\n"):
            if "피해자" in line and ("이름=" in line or "|이름=" in line):
                victim_info = line
                break
    
    prompt = ChatPromptTemplate.from_template("""
        다음 전체 스토리를 바탕으로 게임 시작을 위한 간략한 사건 개요를 생성해주세요.
        개요는 범인이 누구인지 확실히 드러나지 않도록 중립적으로 작성되어야 합니다.
        
        전체 스토리:
        {full_story}
        
        피해자 정보:
        {victim_info}
        
        다음 형식으로 사건 개요를 작성해주세요:
        
        [사건 제목]: (간단한 제목)
        [사건 배경]: (사건 발생 이전의 상황, 인물들의 관계 등 2-3문장)
        [사건 개요]: (3-4문장으로 상세한 사건 설명)
        [피해자 정보]: (피해자의 정보, 피해 상황 등)
        [용의자 정보]: (용의자의 신상정보, 동기, 알리바이 등)
        [검사 측 증거]:
        1. (검사 측 증거 1과 이 증거가 사건과 어떻게 연결되는지)
        2. (검사 측 증거 2와 이 증거가 사건과 어떻게 연결되는지)
        3. (검사 측 증거 3와 이 증거가 사건과 어떻게 연결되는지)
        [변호사 측 증거]:
        1. (변호사 측 증거 1과 이 증거가 용의자의 무죄를 어떻게 뒷받침하는지)
        2. (변호사 측 증거 2과 이 증거가 용의자의 무죄를 어떻게 뒷받침하는지)
        3. (변호사 측 증거 3와 이 증거가 용의자의 무죄를 어떻게 뒷받침하는지)
        [핵심 쟁점]: (이 사건의 핵심 쟁점 2-3가지)
        
        참고: 피해자가 사망한 경우, 사망 사실을 명확히 기록해 주세요. 피해자와 관련자들의 관계를 명확히 설명해주세요.
    """)
    
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"full_story": full_story, "victim_info": victim_info})

def get_related_characters(full_story):
    """전체 스토리에서 관련자 정보를 추출합니다. 피해자는 제외합니다."""
    llm = get_llm()
    
    # 먼저 피해자 정보 추출
    victim_name = ""
    victim_status = "unknown"
    for line in full_story.split("\n"):
        if line.startswith("[피해자 정보]:"):
            victim_info = line.split(":", 1)[1].strip()
            if "이름=" in victim_info:
                try:
                    name_part = victim_info.split("이름=")[1]
                    victim_name = name_part.split("|")[0] if "|" in name_part else name_part
                except:
                    pass
            if "상태=" in victim_info:
                try:
                    status_part = victim_info.split("상태=")[1]
                    victim_status = status_part.split("|")[0] if "|" in status_part else status_part
                except:
                    pass
            break
            
    # 피해자 정보가 없을 경우 전체 스토리에서 피해자 찾기 시도
    if not victim_name:
        for line in full_story.split("\n"):
            if "피해자" in line and ("이름=" in line or "|이름=" in line):
                try:
                    name_part = line.split("이름=")[1]
                    victim_name = name_part.split("|")[0] if "|" in name_part else name_part
                    if "사망" in line:
                        victim_status = "사망"
                    elif "생존" in line:
                        victim_status = "생존"
                    break
                except:
                    pass
    
    prompt = ChatPromptTemplate.from_template("""
        다음 전체 스토리에서 관련자 정보를 추출해주세요.
        피해자가 이미 확인되었으므로 피해자는 제외하고 다른 관련자만 추출해주세요.
        
        전체 스토리:
        {full_story}
        
        피해자 정보:
        이름: {victim_name}
        상태: {victim_status}
        
        다음 형식으로만 출력해주세요:
        
        관련자1:이름=스토리의관련자1|관계=목격자 또는 기타 관계|배경=...
        관련자2:이름=스토리의관련자2|관계=목격자 또는 기타 관계|배경=...
        
        특히 다음 조건을 반드시 지켜주세요:
        1. 피해자 {victim_name}을(를) 관련자 목록에 포함하지 마세요
        2. 피해자가 사망한 경우, 생존한 다른 인물만 포함해야 합니다
        3. 모든 관련자는 용의자가 아닌 다른 인물이어야 합니다
        4. 각 관련자는 현재 살아있고 증언이 가능한 사람이어야 합니다
        
        다른 설명 없이 위 형식의 응답만 제공해주세요.
        전체 스토리에 있는 실제 관련자 이름을 그대로 사용하세요.
        모든 이름은 성과 이름을 모두 포함해야 합니다.
    """)
    
    chain = prompt | llm | StrOutputParser()
    response = chain.invoke({"full_story": full_story, "victim_name": victim_name, "victim_status": victim_status})
    
    # 텍스트 파싱
    related_characters = []
    try:
        lines = [line.strip() for line in response.split("\n") if line.strip()]
        for line in lines:
            if not line.startswith("관련자") or "|" not in line:
                continue
                
            parts = line.split(":", 1)[1].split("|")
            profile = {"type": "character"}
            
            for part in parts:
                if "=" not in part:
                    continue
                key, value = part.split("=", 1)
                if key == "이름":
                    profile["name"] = value
                elif key == "관계":
                    profile["role"] = value
                elif key == "배경":
                    profile["background"] = value
            
            # 피해자와 같은 이름인 경우 건너뛰기
            if "name" in profile and profile["name"] != victim_name:
                related_characters.append(profile)
    except Exception as e:
        print(f"관련자 추출 오류: {e}")
        # 파싱에 실패한 경우 기본 프로필 사용
        related_characters = [
            {"name": "백도현", "type": "character", "role": "목격자", "background": "현장 근처에서 중요한 정보를 목격한 인물"},
            {"name": "임지은", "type": "character", "role": "관계자", "background": "사건과 관련된 중요 인물"}
        ]
    
    # 피해자와 이름이 같은 경우 다른 이름으로 변경
    for i in range(len(related_characters)):
        if related_characters[i]["name"] == victim_name:
            backup_names = [
                "백도현", "임지은", "손예진", "오현우", "노은서", "진승호", 
                "권나라", "류태민", "장서윤", "홍태경", "송민아", "윤도현"
            ]
            for new_name in backup_names:
                if new_name != victim_name:
                    related_characters[i]["name"] = new_name
                    break
    
    # 프로필이 2개 미만이면 기본 프로필로 보충
    if len(related_characters) < 2:
        default_profiles = [
            {"name": "백도현", "type": "character", "role": "목격자", "background": "현장 근처에서 중요한 정보를 목격한 인물"},
            {"name": "임지은", "type": "character", "role": "관계자", "background": "사건과 관련된 중요 인물"}
        ]
        
        # 피해자와 같은 이름이 있으면 변경
        for profile in default_profiles:
            if profile["name"] == victim_name:
                profile["name"] = "한수민" if victim_name != "한수민" else "박태준"
        
        # 모자란 수만큼 추가
        needed = 2 - len(related_characters)
        for i in range(needed):
            # 이미 있는 이름과 중복되지 않게 추가
            existing_names = [char["name"] for char in related_characters]
            if default_profiles[i]["name"] not in existing_names and default_profiles[i]["name"] != victim_name:
                related_characters.append(default_profiles[i])
    
    return related_characters[:2]  # 최대 2개만 반환