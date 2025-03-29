from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# ... existing code ...

def get_llm(model="gpt-4o"):
    llm = ChatOpenAI(model=model)  
    return llm


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