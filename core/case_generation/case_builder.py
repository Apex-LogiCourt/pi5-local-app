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
    EVIDENCE_TEMPLATE,
    CASE_BEHIND_TEMPLATE,
)


# def get_llm(model="gpt-4o"):
def get_llm(model="gpt-4o-mini", temperature=1.0):
    llm = ChatOpenAI(model=model, temperature=temperature)  
    """    
    temperature 값의 의미:
    0: 가장 결정적이고 예측 가능한 응답 (항상 가장 가능성이 높은 토큰 선택)
    0.7: ChatGPT의 기본값 (적당한 창의성과 안정성)
    ~1.0 : 창의적이지만 안정성 떨어짐
    """
    return llm

def get_case_summary_chain(model="gpt-4o-mini", temperature=1.0):
    """사건 개요 생성을 위한 체인을 반환하는 함수
    
    Args:
        model (str): 사용할 모델 이름
        temperature (float): 생성 온도 (0~1.0)
        
    Returns:
        chain: 사건 개요 생성 체인
    """
    llm = get_llm(model, temperature)
    prompt = ChatPromptTemplate.from_template(CASE_SUMMARY_TEMPLATE)
    chain = prompt | llm | StrOutputParser()
    return chain

def get_character_extraction_chain(model="gpt-4o-mini", temperature=0.7):
    """등장인물 추출을 위한 체인을 반환하는 함수
    
    Args:
        model (str): 사용할 모델 이름
        temperature (float): 생성 온도 (0~1.0)
        
    Returns:
        chain: 등장인물 추출 체인
    """
    llm = get_llm(model, temperature)
    prompt = ChatPromptTemplate.from_template(CHARACTER_EXTRACTION_TEMPLATE)
    chain = prompt | llm | StrOutputParser()
    return chain

def extract_characters_from_response(response, verbose=False):
    """LLM 응답에서 등장인물 이름을 추출하는 함수
    
    Args:
        response (str): LLM 응답
        verbose (bool): 상세 로그 출력 여부
        
    Returns:
        dict: 추출된 등장인물 이름 (역할별)
    """
    try:
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
        if verbose:
            print(f"등장인물 추출 에러: {str(e)}")
        # 파싱 실패시 기본 이름 반환
        return {
            "defendant": "김철수",
            "victim": "이영희",
            "witness": "정하늘",
            "reference": "최교수"
        }

def get_witness_profiles_chain(model="gpt-4o-mini", temperature=0.7):
    """등장인물 프로필 생성을 위한 체인을 반환하는 함수
    
    Args:
        model (str): 사용할 모델 이름
        temperature (float): 생성 온도 (0~1.0)
        
    Returns:
        chain: 등장인물 프로필 생성 체인
    """
    llm = get_llm(model, temperature)
    prompt = ChatPromptTemplate.from_template(WITNESS_PROFILES_TEMPLATE)
    chain = prompt | llm | StrOutputParser()
    return chain

def process_witness_profiles_response(response, characters, verbose=False):
    """LLM 응답에서 등장인물 프로필을 추출하는 함수
    
    Args:
        response (str): LLM 응답
        characters (dict): 등장인물 이름 딕셔너리
        verbose (bool): 상세 로그 출력 여부
        
    Returns:
        list: Profile 객체 리스트
    """
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
        if verbose:
            print("JSON 파싱 에러:", str(e))
        # 파싱 실패시 기본 프로필 반환
        return [
            Profile(name=characters["defendant"], type="defendant", context="피고인으로서 출석"),
            Profile(name=characters["victim"], type="victim", context="피해자로서 출석"),
            Profile(name=characters["witness"], type="witness", context="사건 목격자로서 출석"),
            Profile(name=characters["reference"], type="reference", context="참고인으로서 출석")
        ]

def get_evidence_chain(model="gpt-4o-mini", temperature=0.7):
    """증거 생성을 위한 체인을 반환하는 함수
    
    Args:
        model (str): 사용할 모델 이름
        temperature (float): 생성 온도 (0~1.0)
        
    Returns:
        chain: 증거 생성 체인
    """
    llm = get_llm(model, temperature)
    prompt = ChatPromptTemplate.from_template(EVIDENCE_TEMPLATE)
    chain = prompt | llm | StrOutputParser()
    return chain

def process_evidence_response(response, verbose=False):
    """LLM 응답에서 증거를 추출하는 함수
    
    Args:
        response (str): LLM 응답
        verbose (bool): 상세 로그 출력 여부
        
    Returns:
        list: Evidence 객체 리스트
    """
    try:
        # JSON 응답을 파싱하여 증거 정보 추출
        evidence_data = json.loads(response)
        
        # 필수 키가 있는지 확인
        required_keys = ["prosecution", "defense"]
        if not all(key in evidence_data for key in required_keys):
            raise ValueError("필수 키가 누락되었습니다")
            
        # 각 증거의 필수 키 확인
        for side in ["prosecution", "defense"]:
            if len(evidence_data[side]) != 2:
                raise ValueError(f"{side}의 증거가 2개가 아닙니다")
            for evidence in evidence_data[side]:
                if not all(key in evidence for key in ["name", "description"]):
                    raise ValueError(f"{side}의 증거에 필수 키가 누락되었습니다")
                    
        # Evidence 객체 리스트로 변환
        evidences = []
        for side in ["prosecution", "defense"]:
            for evidence in evidence_data[side]:
                evidences.append(Evidence(
                    name=evidence["name"],
                    description=evidence["description"],
                    type=side
                ))
        return evidences
        
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        if verbose:
            print(f"증거 생성 에러: {str(e)}")
        # 파싱 실패시 기본 증거 반환
        return [
            Evidence(name="CCTV 영상", description="사건 현장의 CCTV 영상", type="prosecution"),
            Evidence(name="목격자 증언", description="목격자의 증언", type="prosecution"),
            Evidence(name="알리바이", description="피고인의 알리바이 증거", type="defense"),
            Evidence(name="신원조회", description="피고인의 신원조회 결과", type="defense")
        ]

def get_case_behind_chain(model="gpt-4o-mini", temperature=0.7):
    """사건 내막 생성을 위한 체인을 반환하는 함수
    
    Args:
        model (str): 사용할 모델 이름
        temperature (float): 생성 온도 (0~1.0)
        
    Returns:
        chain: 사건 내막 생성 체인
    """
    llm = get_llm(model, temperature)
    prompt = ChatPromptTemplate.from_template(CASE_BEHIND_TEMPLATE)
    chain = prompt | llm | StrOutputParser()
    return chain

def process_case_behind_response(response, verbose=False):
    """LLM 응답에서 사건 내막을 추출하는 함수
    
    Args:
        response (str): LLM 응답
        verbose (bool): 상세 로그 출력 여부
        
    Returns:
        str: 생성된 사건 내막
    """
    try:
        # JSON 응답을 파싱하여 내막 정보 추출
        behind_data = json.loads(response)
        
        # 필수 키가 있는지 확인
        required_keys = ["truth", "explanation", "key_points"]
        if not all(key in behind_data for key in required_keys):
            raise ValueError("필수 키가 누락되었습니다")
            
        # 내막 정보를 문자열로 변환
        behind_str = f"진실: {behind_data['truth']}\n\n"
        behind_str += f"설명: {behind_data['explanation']}\n\n"
        behind_str += "핵심 포인트:\n"
        for point in behind_data["key_points"]:
            behind_str += f"- {point}\n"
            
        return behind_str
        
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        if verbose:
            print(f"사건 내막 생성 에러: {str(e)}")
        # 파싱 실패시 기본 내막 반환
        return "사건의 내막을 생성하는데 실패했습니다."

def prepare_evidence_str_for_behind(evidences):
    """증거 목록을 문자열로 변환하는 함수
    
    Args:
        evidences (list): Evidence 객체 리스트
        
    Returns:
        str: 증거 정보 문자열
    """
    evidence_str = ""
    for evidence in evidences:
        evidence_str += f"- {evidence.name} ({evidence.type}): {evidence.description}\n"
    return evidence_str

def create_case_data(model="gpt-4o-mini", temperature=1.0, verbose=False):
    """사건 데이터를 생성하는 함수
    
    Args:
        model (str): 사용할 모델 이름
        temperature (float): 생성 온도 (0~1.0)
        verbose (bool): 상세 로그 출력 여부
        
    Returns:
        CaseData: 생성된 사건 데이터
    """
    if verbose:
        print("사건 개요 생성 중...")
    
    # 사건 개요 생성
    case_summary_chain = get_case_summary_chain(model, temperature)
    case_summary = case_summary_chain.invoke({})
    
    if verbose:
        print("등장인물 추출 중...")
    
    # 등장인물 추출
    character_chain = get_character_extraction_chain()
    character_response = character_chain.invoke({"case_summary": case_summary})
    characters = extract_characters_from_response(character_response, verbose)
    
    if verbose:
        print("등장인물 프로필 생성 중...")
    
    # 등장인물 프로필 생성
    profile_chain = get_witness_profiles_chain()
    profile_response = profile_chain.invoke({
        "case_summary": case_summary,
        "defendant_name": characters["defendant"],
        "victim_name": characters["victim"],
        "witness_name": characters["witness"],
        "reference_name": characters["reference"]
    })
    profiles = process_witness_profiles_response(profile_response, characters, verbose)
    
    if verbose:
        print("증거 생성 중...")
    
    # 증거 생성
    evidence_chain = get_evidence_chain()
    evidence_response = evidence_chain.invoke({"case_summary": case_summary})
    evidences = process_evidence_response(evidence_response, verbose)
    
    if verbose:
        print("사건 내막 생성 중...")
    
    # 사건 내막 생성
    behind_chain = get_case_behind_chain()
    evidence_str = prepare_evidence_str_for_behind(evidences)
    behind_response = behind_chain.invoke({
        "case_summary": case_summary,
        "evidence": evidence_str
    })
    behind = process_case_behind_response(behind_response, verbose)
    
    # Case 객체 생성
    case = Case(    
        outline=case_summary,
        behind=behind
    )
    
    if verbose:
        print("사건 데이터 생성 완료")
    
    # CaseData 객체 생성 및 반환
    return CaseData(case=case, profiles=profiles, evidences=evidences)

# 테스트 코드 (이 파일을 직접 실행할 때만 실행됨)
if __name__ == "__main__":
    # 체인만 생성하는 테스트
    print("체인 생성 테스트")
    
    # 사건 개요 생성
    case_summary_chain = get_case_summary_chain()
    case_summary = case_summary_chain.invoke({})
    print(case_summary)
    print("사건 개요 체인 생성 완료")
    
    # 등장인물 추출
    character_chain = get_character_extraction_chain()
    character_response = character_chain.invoke({"case_summary": case_summary})
    print(character_response)
    # 추출된 응답 처리
    characters = extract_characters_from_response(character_response)
    print("등장인물 추출 체인 생성 완료")
    
    # 등장인물 프로필 생성
    profile_chain = get_witness_profiles_chain()
    profile_response = profile_chain.invoke({
        "case_summary": case_summary,
        "defendant_name": characters["defendant"],
        "victim_name": characters["victim"],
        "witness_name": characters["witness"],
        "reference_name": characters["reference"]
    })
    print(profile_response)
    print("등장인물 프로필 체인 생성 완료")
    
    # 증거 생성
    evidence_chain = get_evidence_chain()
    evidence_response = evidence_chain.invoke({"case_summary": case_summary})
    print(evidence_response)
    # 증거 응답 처리
    evidences = process_evidence_response(evidence_response)
    print("증거 체인 생성 완료")
    
    # 사건 내막 생성
    behind_chain = get_case_behind_chain()
    evidence_str = prepare_evidence_str_for_behind(evidences)
    behind_response = behind_chain.invoke({
        "case_summary": case_summary,
        "evidence": evidence_str
    })
    print(behind_response)
    print("사건 내막 체인 생성 완료")
    
    print("\n모든 체인 생성 테스트 완료")
    
    