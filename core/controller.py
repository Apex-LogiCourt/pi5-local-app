from dotenv import load_dotenv
load_dotenv()

from typing import List, Dict
from .case_generation.case_builder import build_case_chain, build_character_chain,build_case_behind_chain
from .evidence import make_evidence
from .data_models import CaseData, Case, Profile, Evidence
import asyncio
from core.verdict import get_judge_result


# 싱글톤 패턴 적용
# 자꾸 코드가 길어지고 예외처리 같은 거 하면서 복잡해지니까 class를 나누고 싶단 생각도 듦
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
        await CaseDataManager.generate_case_stream()  # 비동기 호출
        await CaseDataManager.generate_profiles_stream()  # 비동기 호출  
        await CaseDataManager.generate_evidences()  # 비동기 호출
        return cls._case_data
    
    #==============================================
    # case_builder에서 chain을 받아오고 실행 -> chat.py에서 호출됨 

    @classmethod
    async def generate_case_stream(cls, callback=None):
        chain = build_case_chain()
        result = cls._handle_stream(chain, callback)
        cls._case = Case(outline=result, behind="")
        return result
    
    @classmethod
    async def generate_profiles_stream(cls, callback=None):
        chain = build_character_chain(cls._case.outline)
        result = cls._handle_stream(chain, callback)
        
        asyncio.create_task(cls._parse_and_store_profiles(result))
        return result
    
    @classmethod 
    async def generate_evidences(cls, callbacks=None):
        # 데이터가 준비된 경우 바로 처리
        if cls._case is not None and cls._profiles is not None:
            evidences = make_evidence(case_data=cls._case, profiles=cls._profiles)
            cls._evidences = evidences 
            cls._case_data = CaseData(cls._case, cls._profiles, cls._evidences)
            
            if callbacks:
                for callback in callbacks:
                    callback(evidences)
                    
            return evidences
            
        return await cls._wait_for_data(callbacks) #데이터가 제대로 안 담긴 경우 대기하거나 재시도 
    
    # 호출 시점 : 최종 판결과 함께 또는 최종 판결을 읽고 있을 때 
    # 매개변수로 변경된 증거 리스트도 포함 
    @classmethod
    async def generate_case_behind(cls, callback=None):
        chain = build_case_behind_chain(cls._case.outline, cls._profiles) 
        result = cls._handle_stream(chain, callback)
        return result
    
    # 프로필 파싱 및 저장하는 내부 메소드 
    @classmethod
    async def _parse_and_store_profiles(cls, result: str):
        # print("parse_and_store_profiles 실행")
        profiles = cls._parse_character_template(result)
        cls.set_profiles(profiles)
        # print(profiles)

    @staticmethod
    def _parse_character_template(template: str) -> List[Profile]:
        profiles = []
        profile_path = Path(__file__).parent / "assets" / "profile" / "profil.json"
        with open(profile_path, 'r', encoding='utf-8') as f:
            profile_data = json.load(f)
            characters = profile_data['characters']

        character_blocks = template.strip().split('--------------------------------')
        for block in character_blocks:
            lines = [line.strip() for line in block.strip().split('\n') if line.strip()]
            if not lines:
                continue

            # 첫 줄에서 이름, 나이, 성별 추출
            m = re.match(r'(피고|피해자|목격자|참고인) *: *([^(]+) *\(나이: *([0-9]+)세?, *성별: *([^)]+)\)', lines[0])
            if not m:
                continue
            role_kor, name, age, gender = m.groups()
            profile_type = {
                "피고": "defendant",
                "피해자": "victim",
                "목격자": "witness",
                "참고인": "reference"
            }[role_kor]

            # 배경 추출
            context = ""
            for line in lines:
                if line.startswith("- 배경") or line.startswith("배경"):
                    context = line.split(":", 1)[1].strip()
                    break

            # profil.json에서 정보 보정
            character_info = next((char for char in characters if char['name'] == name), None)
            if character_info:
                gender = character_info['gender']
                age = character_info['age']

            profiles.append(Profile(
                type=profile_type,
                name=name,
                gender=gender,
                age=int(age),
                context=context
            ))
        return profiles
    
    @staticmethod
    def _handle_stream(chain, callback=None):
        result = ""
        for chunk in chain.stream({}):
            content = chunk.content if hasattr(chunk, 'content') else chunk
            result += content
            
            if callback:
                callback(content, result)
        return result
    
    # 증거 만들기 전에 데이터가 없다면 준비될 때까지 대기
    @classmethod
    async def _wait_for_data(cls, callbacks=None):
        MAX_RETRIES = 5
        retry_count = 0
        
        while retry_count < MAX_RETRIES:
            print(f"데이터 준비 중... (시도: {retry_count + 1})")
            await asyncio.sleep(0.5)
            retry_count += 1
            
            if cls._case is not None and cls._profiles is not None:
                return await cls.generate_evidences(callbacks)
                
        print("데이터 준비 실패")
        return None
    
    
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
    from .interrogation.interrogator import ask_witness
    return ask_witness(question, name, type, case_summary)

# def ask_witness_wrapper(question: str, name: str, wtype: str, case_summary: str) -> str:
# from interrogation.interrogator import ask_witness
# return ask_witness(question, name, wtype, case_summary)

def ask_defendant_wrapper(question, defendant_name, case_summary):
    from .interrogation.interrogator import ask_defendant
    return ask_defendant(question, defendant_name, case_summary)


#==============================================
# verdict.py의 함수
# 단순히 함수 호출 목적
# verdict.py -> chat.py로 넘겨줌
# 삭제 예정 
#==============================================  

def get_judge_result_wrapper(message_list):
    from core.verdict import get_judge_result 
    return get_judge_result(message_list)


if __name__ == "__main__":
    # asyncio.run(CaseDataManager.initialize())  # 비동기 호출
    # asyncio.run(CaseDataManager.generate_case_stream())  # 비동기 호출
    # asyncio.run(CaseDataManager.generate_profiles_stream())  # 비동기 호출  
    # asyncio.run(CaseDataManager.generate_evidences())  # 비동기 호출
    # print(CaseDataManager.get_case_data())

    asyncio.run(CaseDataManager.initialize())