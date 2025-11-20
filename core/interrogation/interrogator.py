from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from data_models import CaseData, Case, Profile, Evidence
from typing import List, Dict, Optional


# 템플릿 임포트

# 만질 때 username_witness_templates.py으로 각자 생성해서 갈아 끼우세용 
# from .prompt_templates.username_witness_templates import (
#     ASK_WITNESS_EXPERT_TEMPLATE,
#     ASK_WITNESS_CHARACTER_TEMPLATE,
#     ASK_DEFENDANT_TEMPLATE
# )

from .prompt_templates.ex_witness_templates import (
    ASK_WITNESS_EXPERT_TEMPLATE,
    ASK_WITNESS_CHARACTER_TEMPLATE,
    ASK_DEFENDANT_TEMPLATE
)

# ... existing code ...

def get_llm(model="gpt-4o-mini"):
    llm = ChatOpenAI(model=model)  
    return llm


def ask_witness(question, name, wtype, case_summary):
    llm = get_llm()
    
    if wtype == "expert":
        context = ASK_WITNESS_EXPERT_TEMPLATE.format(name=name, case_summary=case_summary)
    else:
        context = ASK_WITNESS_CHARACTER_TEMPLATE.format(name=name, case_summary=case_summary)

    prompt = ChatPromptTemplate.from_template("""
        {context}

        질문: {question}
        답변:
    """)

    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"question": question, "context": context})


def ask_defendant(question, defendant_name, case_summary):
    llm = get_llm()
    
    context = ASK_DEFENDANT_TEMPLATE.format(defendant_name=defendant_name, case_summary=case_summary)

    prompt = ChatPromptTemplate.from_template("""
        {context}

        질문: {question}
        답변:
    """)

    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"question": question, "context": context})


#===============================================
# Interrogator 클래스

class Interrogator:
    _instance = None
    _initialized = False
    
    _evidences : Evidence = None
    _case : str = None
    _profiles : List[Profile] = None
    _role = None
    _current_profile : Profile = None
    llm = get_llm("gpt-5-mini")  # 기본 LLM 설정
    
    # 각 인물별 대화 히스토리를 관리 (인물명을 키로 사용)
    _chat_histories: Dict[str, List] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Interrogator, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            Interrogator._initialized = True
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def set_case_data(cls, case_data: CaseData) -> bool:
        if case_data is None:
            print("[Interrogator] case_data가 None입니다")
            return False

        cls._case = case_data.case
        cls._profiles = case_data.profiles
        # 증거품이 아직 없을 수 있으므로 빈 리스트로 초기화
        cls._evidence = case_data.evidences if case_data.evidences else []
        return True

    @classmethod
    def build_ask_chain(cls, question: str, profile : Profile):
        # 프로필 키 생성
        profile_key = f"{profile.name}_{profile.type}"
        
        # 해당 인물과의 대화 히스토리가 없으면 초기화 (최초 1회만)
        if profile_key not in cls._chat_histories:
            cls._chat_histories[profile_key] = {
                "context": {
                    "role": profile.type,
                    "case": cls._case.outline,
                    "profile": profile.__str__(),
                    "personality": profile.personality,
                    "gender": profile.gender,
                    "age": profile.age

                },
                "messages": []  # 질문-답변 히스토리
            }
            # print(f"[대화 메모리] {profile.name}({profile.type})와의 새로운 심문 시작")
            print(f"{profile.personality}")
        # 이전 대화 히스토리 가져오기
        history_data = cls._chat_histories[profile_key]
        context = history_data["context"]
        messages = history_data["messages"]
        
        # 이전 대화를 텍스트로 포맷팅
        conversation_history = ""
        if messages:
            conversation_history = "\n\n이전 대화 내역:\n"
            for i, msg in enumerate(messages, 1):
                conversation_history += f"Q{i}: {msg['question']}\nA{i}: {msg['answer']}\n"
        
        # ChatPromptTemplate으로 명확하게 system role 지정
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""당신은 재판에 참석한 {context['role']}입니다.
당신의 역할은 사건에 대한 질문에 인간적으로 답변하는 것입니다.

사건 개요:
{context['case']}

당신의 정보:
{context['profile']}

당신의 성격:
{context['personality']}
{context['gender']}
{context['age']}

지침:
- 질문에 최대한 감정을 담아 인간적인 말투로 답변하세요.
- 답변은 4줄을 넘지 않게 간결하게 하고 "제 진술이 사건 해결에 도움이 되기를 바랍니다." 같이 쓸데없는 소리는 하지 마세요.
- 계속 대화를 이어가는 말투로 답변하세요.
- 당신의 프로필 속 성격과 성별, 나이를 반영한 말투로 답변하세요.
- 이전 대화 내용을 참고하여 일관성 있게 답변하세요.{conversation_history}"""),
            ("human", "{question}")
        ])
        
        # LLM 체인 실행
        cls.llm = get_llm()
        chain = prompt | cls.llm | StrOutputParser()
        answer = chain.invoke({"question": question})
        
        # 대화 히스토리에 추가
        messages.append({
            "question": question,
            "answer": answer
        })
        
        print(f"[대화 메모리] 현재 {profile.name}와의 대화 턴: {len(messages)}턴")

        return answer

    @classmethod
    def react_to_evidence(cls, evidence: Evidence, profile: Profile, callback=None):
        """
        증거품을 제시했을 때 심문 대상의 반응을 생성하고 실행
        callback이 제공되면 스트리밍으로 전달
        """
        from tools.service import run_chain_streaming
        import asyncio

        # 프로필 키 생성
        profile_key = f"{profile.name}_{profile.type}"

        # 대화 히스토리 가져오기 (없으면 기본 컨텍스트만 사용)
        history_data = cls._chat_histories.get(profile_key, {
            "context": {
                "role": profile.type,
                "case": cls._case.outline,
                "profile": profile.__str__(),
                "personality": profile.personality,
                "gender": profile.gender,
                "age": profile.age
            },
            "messages": []
        })

        context = history_data["context"]

        # 증거품 정보
        evidence_info = f"""
증거품 이름: {evidence.name}
증거품 설명: {', '.join(evidence.description)}
제출자: {evidence.type}
"""

        # ChatPromptTemplate으로 증거 반응 프롬프트 생성
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""당신은 재판에 참석한 {context['role']}입니다.
방금 심문 중에 다음 증거품이 제시되었습니다.

사건 개요:
{context['case']}

당신의 정보:
{context['profile']}

당신의 성격:
{context['personality']}
{context['gender']}
{context['age']}

제시된 증거품:
{evidence_info}

지침:
- 이 증거품을 보고 당신의 입장에서 짧고 자연스럽게 반응하세요 (1~2줄)
- 증거품이 당신에게 유리하거나 불리한지에 따라 감정을 담아 반응하세요
- 당신의 성격, 성별, 나이를 반영한 말투로 답변하세요
- "이 증거는..." 같은 설명조가 아니라 즉각적인 반응을 하세요
- 예시: "이건... 제가 본 그 칼이 맞습니다!", "그건 제 것이 아닙니다!", "어떻게 이걸...?" 등"""),
            ("human", "이 증거품에 대해 어떻게 생각하십니까?")
        ])

        # LLM 체인 실행
        cls.llm = get_llm()
        chain = prompt | cls.llm | StrOutputParser()

        print(f"[증거 반응] {profile.name}이(가) 증거 '{evidence.name}'에 반응합니다")

        # 비동기로 체인 실행
        if callback:
            asyncio.create_task(run_chain_streaming(chain, callback))
        else:
            # 콜백이 없으면 동기 실행
            return chain.invoke({})

    @classmethod
    async def react_to_evidence_streaming(cls, evidence: Evidence, profile: Profile, callback=None):
        """
        증거품 반응을 스트리밍 방식으로 생성 (비동기)
        GameController에서 호출하는 메서드
        """
        from tools.service import run_chain_streaming

        # 프로필 키 생성
        profile_key = f"{profile.name}_{profile.type}"

        # 대화 히스토리 가져오기 (없으면 기본 컨텍스트만 사용)
        history_data = cls._chat_histories.get(profile_key, {
            "context": {
                "role": profile.type,
                "case": cls._case.outline,
                "profile": profile.__str__(),
                "personality": profile.personality,
                "gender": profile.gender,
                "age": profile.age
            },
            "messages": []
        })

        context = history_data["context"]

        # 증거품 정보
        evidence_info = f"""
증거품 이름: {evidence.name}
증거품 설명: {', '.join(evidence.description)}
제출자: {evidence.type}
"""

        # ChatPromptTemplate으로 증거 반응 프롬프트 생성
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""당신은 재판에 참석한 {context['role']}입니다.
방금 심문 중에 다음 증거품이 제시되었습니다.

사건 개요:
{context['case']}

당신의 정보:
{context['profile']}

당신의 성격:
{context['personality']}
{context['gender']}
{context['age']}

제시된 증거품:
{evidence_info}

지침:
- 이 증거품을 보고 당신의 입장에서 짧고 자연스럽게 반응하세요 (1~2줄)
- 증거품이 당신에게 유리하거나 불리한지에 따라 감정을 담아 반응하세요
- 당신의 성격, 성별, 나이를 반영한 말투로 답변하세요
- "이 증거는..." 같은 설명조가 아니라 즉각적인 반응을 하세요
- 예시: "이건... 제가 본 그 칼이 맞습니다!", "그건 제 것이 아닙니다!", "어떻게 이걸...?" 등"""),
            ("human", "이 증거품에 대해 어떻게 생각하십니까?")
        ])

        # LLM 체인 실행
        cls.llm = get_llm()
        chain = prompt | cls.llm | StrOutputParser()

        print(f"[증거 반응 스트리밍] {profile.name}이(가) 증거 '{evidence.name}'에 반응합니다")

        # 스트리밍으로 반응 생성
        full_response = await run_chain_streaming(chain, callback)
        return full_response

    @classmethod
    def reset_conversation(cls, profile: Profile = None):
        """
        대화 히스토리를 초기화
        - profile이 주어지면 해당 인물과의 대화만 초기화
        - profile이 None이면 모든 대화 초기화
        """
        if profile:
            profile_key = f"{profile.name}_{profile.type}"
            if profile_key in cls._chat_histories:
                del cls._chat_histories[profile_key]
                print(f"[대화 메모리] {profile.name}({profile.type})와의 대화 히스토리 초기화됨")
        else:
            cls._chat_histories = {}
            print(f"[대화 메모리] 모든 대화 히스토리 초기화됨")
    
    @classmethod
    def get_conversation_history(cls, profile: Profile) -> List[Dict]:
        """특정 인물과의 대화 히스토리를 반환합니다."""
        profile_key = f"{profile.name}_{profile.type}"
        history_data = cls._chat_histories.get(profile_key, None)
        if history_data:
            return history_data.get("messages", [])
        return []
    
    @classmethod
    def get_conversation_turn_count(cls, profile: Profile) -> int:
        """특정 인물과의 대화 턴 수를 반환합니다."""
        messages = cls.get_conversation_history(profile)
        return len(messages)
    
    @classmethod
    def check_request(cls, user_input: str) -> Optional[Dict]:
        """사용자의 심문 요청을 분석하여 JSON 형식으로 반환합니다."""
        prompt = PromptTemplate.from_template("""
        당신은 법정 역할극을 조정하는 AI입니다. 사용자가 심문을 진행하려고 합니다.
        사용자 발언: {user_input}
        프로필 : {profile_data}
        
        사용자가 요청하는 심문 유형과 대상을 파악하여 JSON 형식으로 출력하세요. 
        사용자가 이름을 입력한 경우 프로필과 일치하는 이름인지 반드시 확인하세요.
        이름 출력은 오로지 프로필에 있는 이름만을 출력하세요.
                                            
        1. 피고, 피해자, 목격자, 참고인 등 역할이 명시되어 있거나 이름이 일치하는 경우
            - 피고인 심문: {{"type": "defendant", "answer": "피고에 대한 심문을 진행하십시오."}}
            - 피해자 심문: {{"type": "victim", "answer": "피해자에 대한 심문을 진행하십시오."}}
            - 목격자 심문: {{"type": "witness", "answer": "목격자에 대한 심문을 진행하십시오."}}
            - 참고인 심문: {{"type": "reference", "answer": "참고인에 대한 심문을 진행하십시오."}}
                                            
        2. 이름이 틀린 경우 
            - 오타로 예상됨: {{"type": "retry", "answer": "OOO 씨에 대해 얘기하시는 겁니까?"}}
            - 전혀 다른 이름 : {{"type": "retry", "answer": "그런 인물은 없습니다"}}
        """)

        llm = get_llm()
        chain = prompt | llm | JsonOutputParser()
        result = chain.invoke({"profile_data": cls._profiles.__str__(), "user_input": user_input})
        type = result.get("type")

        if type != "retry":
            # 심문 요청이 유효한 경우, 프로필 리스트에서 해당 타입과 일치하는 프로필 찾기
            target_profile = None
            
            # 사용자가 이름을 직접 언급했는지 확인
            for profile in cls._profiles:
                if profile.name in user_input:
                    target_profile = profile
                    break
            
            # 이름이 없으면 타입으로 찾기
            if not target_profile:
                for profile in cls._profiles:
                    if profile.type == type:
                        target_profile = profile
                        break
            
            cls._current_profile = target_profile

        return result


# 싱글톤 인스턴스 생성
    
it = Interrogator()
