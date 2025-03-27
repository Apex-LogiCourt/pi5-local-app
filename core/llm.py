from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, FewShotChatMessagePromptTemplate
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore 

from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

from config import answer_examples

# 다른 모듈에서 함수 임포트
from core.verdict import get_judge_result, get_truth_revelation, make_case_judgment_prompt, ask_llm
from core.case_generation.case_builder import get_full_case_story, get_case_overview, get_related_characters
from core.case_generation.case_builder import extract_victim_info, extract_suspect_info
from core.interrogation.interrogator import ask_witness, ask_defendant

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
    """LLM 모델 가져오기"""
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

def get_witness_profiles(case_summary):
    """참고인 프로필 가져오기 (하위 호환성 유지 함수)"""
    from core.interrogation.interrogator import get_witness_profiles as get_profiles
    return get_profiles(case_summary)