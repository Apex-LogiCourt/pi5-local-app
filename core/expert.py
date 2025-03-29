from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_anthropic import ChatAnthropic
from rag.legal_document_retriever import get_relevant_documents

def get_llm():
    """LLM 모델을 반환합니다."""
    return ChatAnthropic(model="claude-3-opus-20240229")

def get_expert_context(expert_name, expertise, case_summary, query):
    """전문가와 관련된 문서를 검색합니다."""
    try:
        # 검색 쿼리 구성 - 디버깅 로그 추가
        search_query = f"전문가 {expert_name} {expertise} {query} {case_summary[:100]}"
        print(f"전문가 검색 쿼리: {search_query[:100]}...")
        
        # 관련 문서 검색
        documents = get_relevant_documents(search_query)
        
        if documents:
            context = "\n\n".join([doc.page_content for doc in documents])
            return context
        else:
            print("전문가 관련 문서 검색 결과 없음")
            return ""
    except Exception as e:
        print(f"전문가 컨텍스트 검색 오류: {str(e)}")
        return ""

def extract_key_evidence(full_story):
    """사건의 핵심 증거를 추출합니다."""
    evidence = []
    
    # 범행 관련 세부 정보 추출
    crime_details = ""
    crime_scene = ""
    weapon = ""
    motive = ""
    alibi = ""
    
    for line in full_story.split("\n"):
        if line.startswith("[범행 내용]:") or line.startswith("[사건 세부사항]:"):
            crime_details = line.split(":", 1)[1].strip()
        elif line.startswith("[범행 현장]:") or "현장" in line.lower():
            crime_scene = line.split(":", 1)[1].strip() if ":" in line else line
        elif line.startswith("[범행 도구]:") or "도구" in line.lower() or "무기" in line.lower():
            weapon = line.split(":", 1)[1].strip() if ":" in line else line
        elif line.startswith("[동기]:") or "동기" in line.lower():
            motive = line.split(":", 1)[1].strip() if ":" in line else line
        elif line.startswith("[알리바이]:") or "알리바이" in line.lower():
            alibi = line.split(":", 1)[1].strip() if ":" in line else line
    
    # 핵심 증거 수집
    if crime_details:
        evidence.append(("범행 세부사항", crime_details))
    if crime_scene:
        evidence.append(("범행 현장", crime_scene))
    if weapon:
        evidence.append(("범행 도구/무기", weapon))
    if motive:
        evidence.append(("범행 동기", motive))
    if alibi:
        evidence.append(("알리바이", alibi))
    
    return evidence

def ask_expert(question, expert_name, expertise, case_summary, full_story="", previous_conversation=""):
    """전문가에게 질문하고 응답을 생성합니다."""
    llm = get_llm()
    
    # 기본 컨텍스트 구성
    context = f"""당신은 법정에 출석한 {expertise} 전문가 {expert_name}입니다. 
    당신은 아래 사건에 대해 전문적인 의견을 제시하도록 요청받았습니다.
    당신은 객관적이고 사실에 기반한 전문가적 견해를 제공해야 합니다.
    
    사건 개요:
    {case_summary}
    """
    
    # 전체 스토리 정보 추가 (있는 경우)
    if full_story:
        # 진범 정보 추출
        real_culprit = ""
        for line in full_story.split("\n"):
            if line.startswith("[진범]:"):
                real_culprit = line.split(":", 1)[1].strip()
                break
        
        # 전문가는 사건의 전체 내용과 진범을 알고 있음
        context += f"""
        
        당신은 사건의 진실을 알고 있습니다. {real_culprit}가 실제 범인입니다.
        하지만 이를 직접적으로 말하지 마세요. 대신, 과학적 분석과 전문적 견해를 통해
        간접적인 힌트를 제공하세요.
        
        당신의 임무는 질문에 대해 전문가적 견해를 제시하면서, 동시에 진실에 대한 
        미묘한 단서를 제공하는 것입니다. 너무 노골적인 힌트는 피하세요.
        """
    
    context += f"""
    당신은 {expertise} 전문가로서, 관련 전문 지식을 기반으로 질문에 답변해야 합니다.
    객관적이고 중립적인 태도를 유지하며, 과학적인 증거와 전문적 지식에 기반하여 답변하세요.
    너무 길거나 복잡한 설명은 피하고, 법정에서 이해하기 쉬운 언어로 설명하세요.
    답변은 3-4문장으로 제한하되, 핵심 정보를 포함해야 합니다.
    """
    
    # 이전 대화 내역이 있으면 추가
    if previous_conversation:
        context += f"""
        
        이전 대화 내역:
        {previous_conversation}
        
        위 대화 내역의 맥락을 유지하면서 질문에 답변하세요. 이전 답변과 일관성을 유지하세요.
        """

    prompt = ChatPromptTemplate.from_template("""
        {context}

        질문: {question}
        답변 (3-4문장으로, 전문가답게 힌트 포함):
    """)

    chain = prompt | llm | StrOutputParser()
    response = chain.invoke({"question": question, "context": context})
    
    return response 