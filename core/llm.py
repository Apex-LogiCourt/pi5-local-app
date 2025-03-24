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

def ask_witness(question, name, wtype, case_summary):
    llm = get_llm()
    
    if wtype == "expert":
        context = f"""당신은 사건의 전문가 참고인 {name}입니다. 
        당신은 아래 사건에 대한 전문적인 분석과 의견을 제공하는 역할입니다.
        
        사건 개요:
        {case_summary}
        
        전문가로서 객관적이고 중립적인 의견을 제시하며, 사실에 근거한 전문적 분석을 제공하십시오.
        모르는 내용에 대해서는 정직하게 모른다고 답변하세요.
        """
    else:
        context = f"""당신은 사건에 연루된 참고인 {name}입니다. 
        당신은 아래 사건에 대한 개인적인 관점과 경험을 가지고 있습니다.
        
        사건 개요:
        {case_summary}
        
        귀하는 객관적 사실과 개인적 경험을 바탕으로 질문에 답변하십시오.
        당신이 실제로 알고 있는 정보만 공유하고, 추측성 발언은 피하세요.
        """

    prompt = ChatPromptTemplate.from_template("""
        {context}

        질문: {question}
        답변:
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

def ask_defendant(question, defendant_name, case_summary):
    llm = get_llm()
    
    context = f"""당신은 이 사건의 피고인 {defendant_name}입니다. 
    당신은 아래 사건에 대해 자신이 결백하다고 주장하며, 자신을 변호하려고 합니다.
    하지만 심리적으로는 불안하고 긴장되어 있을 수 있습니다.
    
    사건 개요:
    {case_summary}
    
    당신은 자신의 무죄를 주장하지만, 너무 작위적이거나 인위적인 대답은 하지 않습니다.
    모든 질문에 대해 현실적이고 인간적인 반응을 보이세요.
    당신이 실제로 기억하는 바를 바탕으로 답변하고, 유죄 판결을 피하기 위해 노력하세요.
    """

    prompt = ChatPromptTemplate.from_template("""
        {context}

        질문: {question}
        답변:
    """)

    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"question": question, "context": context})