from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

#==============================================
# 템플릿 갈아끼면 쉽게 사용 가능
# username_case_templates.py 와 같은 형식으로 사용 가능
#============================================== 
# from .prompt_templates.gunrein_case_templates import (
#     CASE_SUMMARY_TEMPLATE,
#     WITNESS_PROFILES_TEMPLATE,
# )

from .prompt_templates.ex_case_templates import (
    CASE_SUMMARY_TEMPLATE,
    WITNESS_PROFILES_TEMPLATE,
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
    llm = get_llm()
    prompt = ChatPromptTemplate.from_template(CASE_SUMMARY_TEMPLATE)
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({})


def make_witness_profiles(case_summary):
    llm = get_llm()
    prompt = ChatPromptTemplate.from_template(WITNESS_PROFILES_TEMPLATE)
    
    chain = prompt | llm | StrOutputParser()
    response = chain.invoke({"case_summary": case_summary})
    
    # 여기 이 부분 !!!!!! data_models.py 에 있는 데이터클래스로 변환해서 담아주세요
    # 애초에 출력을 할 때 Json 형태로 출력할 수 있거든요 가능하면 아래처럼 무식하게 파싱하지 마세요 
    # opeonai에서는 아예 자체적으로 json 형태로 출력해주는 기능이 있습니다.

    # 텍스트 파싱
    witness_profiles = []
    try:
        lines = [line.strip() for line in response.split("\n") if line.strip()]
        for line in lines:
            if not line.startswith("참고인") or "=" not in line or "|" not in line:
                continue
                
            parts = line.split(":", 1)[1].split("|")
            profile = {}
            
            for part in parts:
                if "=" not in part:
                    continue
                key, value = part.split("=", 1)
                if key == "이름":
                    profile["name"] = value
                elif key == "유형":
                    profile["type"] = value
                elif key == "배경":
                    profile["background"] = value
            
            if "name" in profile and "type" in profile:
                witness_profiles.append(profile)
    except Exception:
        # 파싱에 실패한 경우 기본 프로필 사용
        witness_profiles = [
            {"name": "김민수", "type": "character", "background": "사건 목격자"},
            {"name": "박지연", "type": "character", "background": "관련자"},
            {"name": "박건우", "type": "expert", "background": "법의학 전문가"}
        ]
    
    # 프로필이 3개 미만이면 기본 프로필로 보충
    if len(witness_profiles) < 3:
        default_profiles = [
            {"name": "김민수", "type": "character", "background": "사건 목격자"},
            {"name": "박지연", "type": "character", "background": "관련자"},
            {"name": "박건우", "type": "expert", "background": "법의학 전문가"}
        ]
        witness_profiles.extend(default_profiles[:(3-len(witness_profiles))])
    
    return witness_profiles[:3]  # 최대 3개만 반환
  
