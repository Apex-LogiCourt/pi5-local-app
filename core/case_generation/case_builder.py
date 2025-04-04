import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from core.data_models import CaseData, Case, Profile, Evidence

from dotenv import load_dotenv
load_dotenv()

#==============================================
# 템플릿 갈아끼면 쉽게 사용 가능
# username_case_templates.py 와 같은 형식으로 사용 가능
#============================================== 
# from .prompt_templates.gunrein_case_templates import (
#     CASE_SUMMARY_TEMPLATE,
#     WITNESS_PROFILES_TEMPLATE,
# )

from .prompt_templates.gunrein_case_templates import (
    CASE_SUMMARY_TEMPLATE,
    WITNESS_PROFILES_TEMPLATE,
    CHARACTER_EXTRACTION_TEMPLATE,
)


# def get_llm(model="gpt-4o"):
def get_llm(model="gpt-4o-mini"):
    llm = ChatOpenAI(model=model, temperature=1.0)  
    """    
    temperature 값의 의미:
    0: 가장 결정적이고 예측 가능한 응답 (항상 가장 가능성이 높은 토큰 선택)
    0.7: ChatGPT의 기본값 (적당한 창의성과 안정성)
    ~1.0 : 창의적이지만 안정성 떨어짐
    """
    return llm

def make_case_summary():
    """사건 개요와 등장인물 정보를 생성하는 함수"""
    llm = get_llm()
    prompt = ChatPromptTemplate.from_template(CASE_SUMMARY_TEMPLATE)
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({})

def extract_characters(case_summary):
    """사건 개요에서 등장인물 이름을 추출하는 함수"""
    llm = get_llm()
    prompt = ChatPromptTemplate.from_template(CHARACTER_EXTRACTION_TEMPLATE)
    chain = prompt | llm | StrOutputParser()
    
    try:
        response = chain.invoke({"case_summary": case_summary})
        print("\n[등장인물 추출 응답]")
        print(response)
        
        # JSON 응답을 파싱하여 등장인물 이름 추출
        characters = json.loads(response)
        
        # 필수 키가 있는지 확인
        required_keys = ["defendant", "victim", "witness", "reference"]
        missing_keys = [key for key in required_keys if key not in characters]
        if missing_keys:
            raise ValueError(f"필수 키가 누락되었습니다: {', '.join(missing_keys)}")
            
        # 빈 문자열이나 None 값 체크
        for key, value in characters.items():
            if not value or value.strip() == "":
                raise ValueError(f"{key}의 이름이 비어있습니다")
                
        return characters
        
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        print(f"등장인물 추출 에러: {str(e)}")
        # 파싱 실패시 기본 이름 반환
        return {
            "defendant": "김철수",
            "victim": "이영희",
            "witness": "정하늘",
            "reference": "최교수"
        }

def make_witness_profiles(case_summary):
    """사건 개요에서 등장인물 정보를 추출하여 Profile 객체 리스트로 변환하는 함수"""
    # 등장인물 이름 추출
    characters = extract_characters(case_summary)
    
    llm = get_llm()
    prompt = ChatPromptTemplate.from_template(WITNESS_PROFILES_TEMPLATE)
    
    # 추출한 이름을 변수로 제공
    chain = prompt | llm | StrOutputParser()
    response = chain.invoke({
        "case_summary": case_summary,
        "defendant_name": characters["defendant"],
        "victim_name": characters["victim"],
        "witness_name": characters["witness"],
        "reference_name": characters["reference"]
    })
    
    try:
        # JSON 응답을 파싱하여 Profile 객체 리스트로 변환
        profiles_data = json.loads(response)
        # 필수 키가 있는지 확인
        required_keys = ["name", "type", "context"]
        for profile in profiles_data:
            if not all(key in profile for key in required_keys):
                raise ValueError("프로필에 필수 키가 누락되었습니다")
        profiles = [Profile(**profile) for profile in profiles_data]
        return profiles
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        print("JSON 파싱 에러:", str(e))
        # 파싱 실패시 기본 프로필 반환
        return [
            Profile(name=characters["defendant"], type="defendant", context="피고인으로서 출석"),
            Profile(name=characters["victim"], type="victim", context="피해자로서 출석"),
            Profile(name=characters["witness"], type="witness", context="사건 목격자로서 출석"),
            Profile(name=characters["reference"], type="reference", context="참고인으로서 출석")
        ]

# 여기다가 Case, Profile, Evidence CaseData에 넣어서 반환해주세요
def create_case_data():
    case = Case(    
        outline="",
        behind=""
    )
    profiles = []
    evidences = []
    return CaseData(case, profiles, evidences)

if __name__ == "__main__":
    print("사건 개요 생성 중...")
    case_summary = make_case_summary()
    print("\n[생성된 사건 개요]")
    print(case_summary)
    
    print("\n등장인물 추출 중...")
    characters = extract_characters(case_summary)
    print("\n[추출된 등장인물]")
    for role, name in characters.items():
        print(f"- {role}: {name}")
    
    print("\n등장인물 프로필 생성 중...")
    profiles = make_witness_profiles(case_summary)
    print("\n[생성된 등장인물 프로필]")
    for profile in profiles:
        print(f"- {profile.name} ({profile.type}): {profile.context}")
    
    