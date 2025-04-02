from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

def get_llm(model="gpt-4o"):
    llm = ChatOpenAI(model=model)  
    return llm

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