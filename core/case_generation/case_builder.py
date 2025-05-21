import json
import random
from pathlib import Path
from typing import List, Dict, Tuple
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from dotenv import load_dotenv
load_dotenv()

#=============더미데이터를 위한 코드 (테스트종류후 삭제)===================
#================================================================
# 더미 체인 클래스 추가
class DummyChain:
    def __init__(self, dummy_data):
        self.dummy_data = dummy_data
    
    def invoke(self, inputs):
        return self.dummy_data
    
    def stream(self, inputs):
        # 스트리밍 효과를 시뮬레이션
        for char in self.dummy_data:
            yield char

#================================================================
#=======================================================(테스트종료후삭제)


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
    CHARACTER_TEMPLATE,
    CASE_BEHIND_TEMPLATE,
)

#=============기존 코드 보관========================
#========================================(테스트종료후 복구)
# def get_llm(model="gpt-4o-mini", temperature=1.0):
#     llm = ChatOpenAI(model=model, temperature=temperature)  
#     return llm

# #----------------------------
# def load_characters() -> List[Dict]:
#     """profil.json에서 캐릭터 정보를 로드"""
#     profile_path = Path(__file__).parent.parent / "assets" / "profile" / "profil.json"
#     with open(profile_path, 'r', encoding='utf-8') as f:
#         data = json.load(f)
#     return data['characters']

# def select_random_characters(num_characters: int = 4) -> List[Dict]:
#     """지정 수의 캐릭터 랜덤 선택"""
#     characters = load_characters()
#     return random.sample(characters, num_characters)

# # ---------------------------- 사건 요약 체인 ----------------------------

# def format_gender(gender: str) -> str:
#     return "남성" if gender == "남자" else "여성"

# def build_case_chain():
#     """
#     캐릭터를 랜덤 선택하고, 사건 개요 생성을 위한 LLM 체인 반환.
#     """
#     selected_characters = select_random_characters(4)

#     # 캐릭터 정보 템플릿 변수에 개별적으로 매핑
#     character_roles = {
#         "피고_이름": selected_characters[0]['name'],
#         "피고_나이": selected_characters[0]['age'],
#         "피고_성별": format_gender(selected_characters[0]['gender']),
        
#         "피해자_이름": selected_characters[1]['name'],
#         "피해자_나이": selected_characters[1]['age'],
#         "피해자_성별": format_gender(selected_characters[1]['gender']),
        
#         "증인1_이름": selected_characters[2]['name'],
#         "증인1_나이": selected_characters[2]['age'],
#         "증인1_성별": format_gender(selected_characters[2]['gender']),
        
#         "증인2_이름": selected_characters[3]['name'],
#         "증인2_나이": selected_characters[3]['age'],
#         "증인2_성별": format_gender(selected_characters[3]['gender']),
#     }

#     formatted_template = CASE_SUMMARY_TEMPLATE.format(**character_roles)
#     llm = get_llm()
#     prompt = ChatPromptTemplate.from_template(formatted_template)
#     chain = prompt | llm | StrOutputParser()

#     return chain



# # ----기존 케이스 빌드---------
# # 사건 개요 생성을 위한 체인을 반환하는 함수
# # def build_case_chain():
# #     llm = get_llm() # 모델선택 / 온도설정
# #     prompt = ChatPromptTemplate.from_template(CASE_SUMMARY_TEMPLATE)
# #     chain = prompt | llm | StrOutputParser()
# #     return chain

# # 등장 인물 생성 | 매개 변수 case_summary(str)


# def build_character_chain(case_summary: str):
#     """
#     사건 개요를 기반으로 인물 소개 생성 체인 반환.
#     """
#     # 캐릭터를 선택하여 정보 가져오기
#     selected_characters = select_random_characters(4)
    
#     # 캐릭터 정보 템플릿 변수에 개별적으로 매핑
#     template_vars = {
#         "case_summary": case_summary,
        
#         "피고_이름": selected_characters[0]['name'],
#         "피고_나이": selected_characters[0]['age'],
#         "피고_성별": format_gender(selected_characters[0]['gender']),
        
#         "피해자_이름": selected_characters[1]['name'],
#         "피해자_나이": selected_characters[1]['age'],
#         "피해자_성별": format_gender(selected_characters[1]['gender']),
        
#         "증인1_이름": selected_characters[2]['name'],
#         "증인1_나이": selected_characters[2]['age'],
#         "증인1_성별": format_gender(selected_characters[2]['gender']),
        
#         "증인2_이름": selected_characters[3]['name'],
#         "증인2_나이": selected_characters[3]['age'],
#         "증인2_성별": format_gender(selected_characters[3]['gender']),
#     }
    
#     formatted_template = CHARACTER_TEMPLATE.format(**template_vars)
#     llm = get_llm(temperature=0.7)
#     prompt = ChatPromptTemplate.from_template(formatted_template)
#     chain = prompt | llm | StrOutputParser()
#     return chain

# # ---------------------------- 사건의 진실 체인 ----------------------------

# def build_case_behind_chain(case_summary: str, character: str):
#     """
#     사건 개요와 특정 인물을 바탕으로 사건의 진실을 생성하는 체인.
#     """
#     # 캐릭터를 선택하여 정보 가져오기
#     selected_characters = select_random_characters(4)
    
#     # 템플릿 변수 준비
#     template_vars = {
#         "case_summary": case_summary,
#         "character": character,
        
#         "피고_이름": selected_characters[0]['name'],
#         "피고_나이": selected_characters[0]['age'],
#         "피고_성별": format_gender(selected_characters[0]['gender']),
        
#         "피해자_이름": selected_characters[1]['name'],
#         "피해자_나이": selected_characters[1]['age'],
#         "피해자_성별": format_gender(selected_characters[1]['gender']),
        
#         "증인1_이름": selected_characters[2]['name'],
#         "증인1_나이": selected_characters[2]['age'],
#         "증인1_성별": format_gender(selected_characters[2]['gender']),
        
#         "증인2_이름": selected_characters[3]['name'],
#         "증인2_나이": selected_characters[3]['age'],
#         "증인2_성별": format_gender(selected_characters[3]['gender']),
#     }
    
#     formatted_template = CASE_BEHIND_TEMPLATE.format(**template_vars)
#     llm = get_llm(temperature=0.5)
#     prompt = ChatPromptTemplate.from_template(formatted_template)
#     chain = prompt | llm | StrOutputParser()
#     return chain

#===================================================
#============================================여기까지 기존코드


#===========더미데이터코드(테스트종료후삭제해야함)============
#===================================================

def build_case_chain():
    """
    캐릭터를 랜덤 선택하고, 사건 개요 생성을 위한 LLM 체인 반환.
    """
    # 원래 코드 대신 더미 데이터 반환
    dummy_chain = DummyChain(
        """[사건 제목]: 술집에서의 비극

[사건 배경]: 최지훈은 지역 술집의 단골손님이었으며, 김소현은 그 술집의 바텐더였다. 두 사람은 평소 친분이 있었으나, 최근 몇 주간 불화가 생겼다. 남기효는 최지훈의 친구로 자주 함께 술집을 방문했으며, 우민영은 그날 밤 우연히 같은 술집에 있었다.

[사건 개요]: 사건 당일, 최지훈은 술에 취해 김소현과 언쟁을 벌였다. 상황이 격해지면서 최지훈이 갑자기 쓰러졌고, 병원으로 이송되었으나 사망했다. 부검 결과 그의 체내에서 독성 물질이 발견되었고, 김소현이 그에게 제공한 음료가 의심받고 있다.

[피고]: 김소현 (나이: 28세, 성별: 여성)
[피해자]: 최지훈 (나이: 42세, 성별: 남성)
[증인1]: 남기효 (나이: 35세, 성별: 남성)
[증인2]: 우민영 (나이: 24세, 성별: 여성)"""
    )
    return dummy_chain

def build_character_chain(case_summary: str):
    """
    사건 개요를 기반으로 인물 소개 생성 체인 반환.
    """
    # 원래 코드 대신 더미 데이터 반환
    dummy_chain = DummyChain(
        """피고 : 김소현 (나이: 28세, 성별: 여성)
- 직업 : 바텐더
- 성격 : 차분하고 책임감이 강한 성격
- 배경 : 3년 동안 술집에서 일해왔으며, 손님들에게 인기가 많았다. 최지훈과는 평소 좋은 관계였으나 최근 그의 과도한 음주로 인해 갈등이 있었다.

--------------------------------

피해자 : 최지훈 (나이: 42세, 성별: 남성)
- 직업 : 회사원
- 성격 : 감정 기복이 심하고 술을 마시면 공격적이 되는 성향
- 배경 : 최근 직장 문제로 스트레스를 받아 술에 의지하는 경향이 있었다. 김소현에게 자신의 고민을 자주 털어놓았으나, 때로는 그녀를 괴롭히기도 했다.

--------------------------------

목격자 : 남기효 (나이: 35세, 성별: 남성)
- 직업 : 영업사원
- 성격 : 사교적이고 활발한 성격
- 배경 : 최지훈의 오랜 친구로, 사건 당일 함께 술집에 방문했다. 최지훈과 김소현의 언쟁을 목격했으나, 중간에 화장실에 갔다 와서 최지훈이 쓰러진 순간은 보지 못했다.

--------------------------------

참고인 : 우민영 (나이: 24세, 성별: 여성)
- 직업 : 대학원생
- 성격 : 관찰력이 뛰어나고 조용한 성격
- 배경 : 술집에서 혼자 조용히 음료를 마시고 있었다. 최지훈과 김소현의 언쟁과 최지훈이 쓰러지는 순간을 목격했으나, 두 사람을 잘 알지는 못한다."""
    )
    return dummy_chain

def build_case_behind_chain(case_summary: str, character: str):
    """
    사건 개요와 특정 인물을 바탕으로 사건의 진실을 생성하는 체인.
    """
    # 원래 코드 대신 더미 데이터 반환
    dummy_chain = DummyChain(
        """사건의 진실은 최지훈이 자신의 음료에 독성 물질을 스스로 넣었다는 것이다. 그는 최근 심각한 우울증을 앓고 있었으며, 회사에서의 실패로 인해 자살을 결심했다. 김소현은 그의 행동을 알지 못했고, 평소처럼 음료를 제공했을 뿐이다. 

최지훈은 자신의 죽음이 타살로 위장되어 김소현이 의심받기를 원했는데, 이는 그녀가 자신의 구애를 거절했기 때문이었다. 남기효는 최지훈의 정신 상태를 알고 있었지만, 그날 밤 심각성을 인지하지 못했다."""
    )
    return dummy_chain

#===================================================
#=======================================여기까지 더미코드

# 테스트 코드 (컨트롤러 호출 예시) 
# if __name__ == "__main__":
#     story = {} # 사건 개요 저장
    
#     # 1. 사건 개요 생성
#     print("사건 개요 생성 중...\n")
#     case_summary_chain = build_case_chain()
#     case_summary = ""
    
#     # 스트리밍으로 사건 개요 생성
#     for chunk in case_summary_chain.stream({}):
#         if hasattr(chunk, 'content'):
#             print(chunk.content, end='', flush=True)
#             case_summary += chunk.content
#         else:
#             print(chunk, end='', flush=True)
#             case_summary += chunk

#     print('\n\n---------------')  
    
#     # 등장인물 추출 테스트
#     character_chain = build_character_chain(case_summary)
#     character = character_chain.invoke({})
#     print(character)
    
    
#     print('\n\n---------------')
#     # 사건의 진실 생성
#     print("사건의 진실 생성 중...\n")

#     case_truth = ""
#     for chunk in build_case_behind_chain(case_summary, character).stream({}):
#         if hasattr(chunk, 'content'):
#             print(chunk.content, end='', flush=True)
#             case_truth += chunk.content
#         else:
#             print(chunk, end='', flush=True)
#             case_truth += chunk

    