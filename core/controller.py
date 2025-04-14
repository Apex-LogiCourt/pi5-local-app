from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI
from typing import List, Dict
from case_generation.case_builder import build_case_chain, build_character_chain,build_case_behind_chain
from evidence import make_evidence, update_evidence
from data_models import CaseData, Case, Profile, Evidence
import asyncio


# 싱글톤 패턴 적용
class CaseDataManager:
    _instance = None
    _case : Case = None
    _evidences : List[Evidence] = None
    _profiles : List[Profile] = None
    _case_data : CaseData = None
    
    def __init__(self):
        # 새로운 인스턴스 생성 방지
        raise RuntimeError('이 클래스의 인스턴스를 직접 생성할 수 없습니다')
    
    @classmethod
    async def initialize(cls) -> CaseData:
        if cls._case_data is None:
            print("controller 초기화 실행")
            # cls._case_data = CaseData(cls._case, cls._profiles, cls._evidences)
            # print('case_data :', cls._case_data)
        return cls._case_data
    
    #==============================================
    # case_builder에서 chain을 받아오고 실행 -> chat.py에서 호출됨 

    @classmethod
    async def generate_case_stream(cls, callback=None):
        chain = build_case_chain()
        result = ""
        
        for chunk in chain.stream({}):
            content = chunk.content if hasattr(chunk, 'content') else chunk
            result += content
            
            if callback:
                callback(content, result)
        
        cls._case = Case(outline=result, behind="")
        return result
    
    @classmethod
    async def generate_profiles_stream(cls, callback=None):
        chain = build_character_chain(cls._case.outline)
        result = ""
        
        for chunk in chain.stream({}):
            content = chunk.content if hasattr(chunk, 'content') else chunk
            result += content
            
            if callback:
                callback(content, result)

        # 비동기 작업 후 다른 함수 호출 (즉시 반환)
        # 내용을 파싱해서 profiles 리스트에 저장 하는 함수를 호출해야함 비동기로 !!
        asyncio.create_task(cls._parse_and_store_profiles(result)) 
        return result
    
    # 호출 시점 : 최종 판결과 함께 또는 최종 판결을 읽고 있을 때 
    # 매개변수로 변경된 증거 리스트도 포함 
    @classmethod
    async def generate_case_behind(cls, callback=None):
        chain = build_case_behind_chain(cls._case.outline, cls._profiles) 
        result = ""
        
        for chunk in chain.stream({}):
            content = chunk.content if hasattr(chunk, 'content') else chunk
            result += content
            
            if callback:
                callback(content, result)
    
        return result
    
    # 프로필 파싱 및 저장하는 내부 메소드 
    @classmethod
    async def _parse_and_store_profiles(cls, result: str):
        print("parse_and_store_profiles 실행")
        profiles = cls._parse_character_template(result)
        cls.set_profiles(profiles)
        print(profiles)

    @staticmethod
    def _parse_character_template(template: str) -> List[Profile]:
        profiles = []
        
        # 각 인물 블록을 분리
        character_blocks = template.strip().split('--------------------------------')
        
        for block in character_blocks:
            lines = block.strip().split('\n')
            if len(lines) < 4: 
                continue
            
            # 이름, 직업, 성격, 배경 추출
            name_line = lines[0].strip()
            background_line = lines[3].strip()
            
            # 이름 추출 (예: "피고: 이정우" -> "이정우")
            name = name_line.split(':')[1].strip()
            
            # 프로필 객체 생성
            profile_type = "defendant" if "피고" in name_line else "victim" if "피해자" in name_line else "witness" if "목격자" in name_line else "reference"
            
            profile = Profile(
                name=name,
                type=profile_type,
                context=background_line.split(':')[1].strip()  # 배경에서 필요한 정보 추출
            )
            
            profiles.append(profile)
        
        return profiles
    
    
    #==============================================
    # getter/ setter 메소드 추가 
    # 호출 방식 예시 : CaseDataManager.get_case_data()

    @classmethod
    def set_case(cls, case: Case):
        cls._case = case

    @classmethod
    def set_profiles(cls, profiles: List[Profile]):
        cls._profiles = profiles

    @classmethod
    def set_evidences(cls, evidences: List[Evidence]):
        cls._evidences = evidences

    #==============================================

    @classmethod
    def get_case(cls) -> Case:
        return cls._case
    
    @classmethod
    def get_profiles(cls) -> List[Profile]:
        return cls._profiles
    
    @classmethod
    def get_evidences(cls) -> List[Evidence]:
        return cls._evidences
    
    @classmethod
    def get_case_data(cls) -> CaseData:
        if cls._case_data is None:
            return cls.initialize()
        return cls._case_data
    

#==============================================
# interrogator.py의 함수
# 단순히 함수 호출 목적
# interrogator.py -> chat.py로 넘겨줌
# 삭제 예정 
#============================================== 

def ask_witness_wrapper(question, name, type, case_summary):
    from interrogation.interrogator import ask_witness
    return ask_witness(question, name, type, case_summary)

# def ask_witness_wrapper(question: str, name: str, wtype: str, case_summary: str) -> str:
# from interrogation.interrogator import ask_witness
# return ask_witness(question, name, wtype, case_summary)

def ask_defendant_wrapper(question, defendant_name, case_summary):
    from interrogation.interrogator import ask_defendant
    return ask_defendant(question, defendant_name, case_summary)


#==============================================
# verdict.py의 함수
# 단순히 함수 호출 목적
# verdict.py -> chat.py로 넘겨줌
# 삭제 예정 
#==============================================  

def get_judge_result_wrapper(message_list):
    from verdict import get_judge_result
    return get_judge_result(message_list)


if __name__ == "__main__":
    asyncio.run(CaseDataManager.initialize())  # 비동기 호출
    asyncio.run(CaseDataManager.generate_case_stream())  # 비동기 호출
    asyncio.run(CaseDataManager.generate_profiles_stream())  # 비동기 호출  
