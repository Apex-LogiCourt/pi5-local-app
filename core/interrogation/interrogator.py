from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 템플릿 임포트
from .prompt_templates.ex_witness_templates import (
    ASK_WITNESS_EXPERT_TEMPLATE,
    ASK_WITNESS_CHARACTER_TEMPLATE,
    ASK_WITNESS_WITNESS_TEMPLATE,
    ASK_WITNESS_REFERENCE_TEMPLATE,
    ASK_DEFENDANT_TEMPLATE
)

def get_llm(model="gpt-4o", temperature=0.7):
    return ChatOpenAI(model=model, temperature=temperature)

def ask_witness(question, name, wtype, case_summary, conversation_history):
    # 참고인 타입별 temperature 설정
    temperature_map = {
        "expert": 0.3,      # 전문가: 낮은 temperature로 일관된 전문적 답변
        "witness": 0.5,     # 목격자: 중간 temperature로 사실적이면서도 감정 표현
        "reference": 0.6,   # 참고인: 약간 높은 temperature로 자연스러운 대화
        "defendant": 0.7,   # 피고인: 높은 temperature로 감정적이고 인간적인 반응
        "character": 0.6    # 일반 캐릭터: 중간 temperature로 자연스러운 대화
    }
    
    temperature = temperature_map.get(wtype, 0.7)
    llm = get_llm(temperature=temperature)

    # 이전 대화 기록을 텍스트로 변환
    history_text = ""
    for msg in conversation_history:
        if msg["role"] == "user":
            history_text += f"질문: {msg['content']}\n"
        else:
            history_text += f"답변: {msg['content']}\n"

    # 참고인 타입별 템플릿 분기 처리
    if wtype == "expert":
        context = ASK_WITNESS_EXPERT_TEMPLATE.format(name=name, case_summary=case_summary, history=history_text)
    elif wtype == "witness":
        context = ASK_WITNESS_WITNESS_TEMPLATE.format(name=name, case_summary=case_summary, history=history_text)
    elif wtype == "reference":
        context = ASK_WITNESS_REFERENCE_TEMPLATE.format(name=name, case_summary=case_summary, history=history_text)
    else:
        context = ASK_WITNESS_CHARACTER_TEMPLATE.format(name=name, case_summary=case_summary, history=history_text)

    prompt = ChatPromptTemplate.from_template("""{context}

질문: {question}
답변:""")

    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"question": question, "context": context})


def ask_defendant(question, defendant_name, case_summary, conversation_history):
    # 피고인은 높은 temperature로 설정하여 감정적이고 인간적인 반응 유도
    llm = get_llm(temperature=0.7)

    # 이전 대화 기록을 텍스트로 변환
    history_text = ""
    for msg in conversation_history:
        if msg["role"] == "user":
            history_text += f"질문: {msg['content']}\n"
        else:
            history_text += f"답변: {msg['content']}\n"

    context = ASK_DEFENDANT_TEMPLATE.format(defendant_name=defendant_name, case_summary=case_summary, history=history_text)

    prompt = ChatPromptTemplate.from_template("""{context}

질문: {question}
답변:""")

    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"question": question, "context": context})
