from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from rag.legal_document_retriever import get_relevant_documents

def get_llm(model="gpt-4o"):
    """LLM 모델 가져오기"""
    llm = ChatOpenAI(model=model)  
    return llm

def get_defendant_context(defendant_name, case_summary, query):
    """용의자 관련 문서 검색 (RAG)"""
    search_query = f"피고인 {defendant_name} {query} {case_summary[:100]}"
    relevant_docs = get_relevant_documents(search_query, k=3)
    
    if not relevant_docs:
        return ""
        
    context = "\n\n".join([doc.page_content for doc in relevant_docs])
    return context

def ask_defendant(question, defendant_name, case_summary, full_story="", previous_conversation=""):
    """피고인에게 질문하고 응답을 생성합니다."""
    llm = get_llm()
    
    # 관련 문서 검색 (RAG)
    rag_context = get_defendant_context(defendant_name, case_summary, question)
    
    # 기본 컨텍스트 구성
    context = f"""당신은 이 사건의 피고인 {defendant_name}입니다. 
    당신은 아래 사건에 대해 자신이 결백하다고 주장하며, 자신을 변호하려고 합니다.
    하지만 심리적으로는 불안하고 긴장되어 있을 수 있습니다.
    
    사건 개요(공개 정보):
    {case_summary}
    """
    
    # RAG 정보 추가 (있는 경우)
    if rag_context:
        context += f"""
        
        관련 법률 및 사례 정보:
        {rag_context}
        """
    
    # 전체 스토리 정보 추가 (있는 경우)
    if full_story:
        # 전체 스토리에서 용의자 정보와 진범 정보 추출
        suspect_info = ""
        real_culprit = ""
        culprit_role = ""
        
        for line in full_story.split("\n"):
            if line.startswith("[용의자 정보]:"):
                suspect_info = line.split(":", 1)[1].strip()
            if line.startswith("[진범]:"):
                real_culprit = line.split(":", 1)[1].strip()
            if line.startswith("[진범역할]:"):
                culprit_role = line.split(":", 1)[1].strip()
        
        if suspect_info:
            context += f"\n\n당신의 실제 상황(비공개 정보):\n{suspect_info}\n"
            
        # 피고인이 진범인지 확인
        is_culprit = culprit_role == "defendant" and defendant_name.lower() == real_culprit.lower()
        
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
    response = chain.invoke({"question": question, "context": context})
    
    # 이름을 명시적으로 추가하지 않도록 수정
    return response 