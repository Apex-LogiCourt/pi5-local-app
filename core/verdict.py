from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

def get_llm(model="gpt-4o"):
    """LLM 모델 가져오기"""
    llm = ChatOpenAI(model=model)  
    return llm

def get_judge_result(message_list):
    """검사와 변호사의 주장을 바탕으로 판결 결과 생성"""
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

def make_case_judgment_prompt(case: dict) -> str:
    """케이스 판결 프롬프트 생성"""
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
    """LLM에 직접 질문"""
    llm = get_llm()
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", "당신은 공정하고 논리적인 AI 판사입니다."),
        ("human", "{prompt}")
    ])
    chain = prompt_template | llm | StrOutputParser()
    return chain.invoke({"prompt": prompt})
