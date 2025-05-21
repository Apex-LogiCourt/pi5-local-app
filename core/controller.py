from dotenv import load_dotenv
load_dotenv()

from typing import List, Dict
from case_generation.case_builder import build_case_chain, build_character_chain,build_case_behind_chain
from evidence import make_evidence
from data_models import CaseData, Case, Profile, Evidence
import asyncio


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
    from verdict import get_judge_result
    return get_judge_result(message_list)


if __name__ == "__main__":
    asyncio.run(CaseDataManager.initialize())  # 비동기 호출
    asyncio.run(CaseDataManager.generate_case_stream())  # 비동기 호출
    asyncio.run(CaseDataManager.generate_profiles_stream())  # 비동기 호출  
    asyncio.run(CaseDataManager.generate_evidences())  # 비동기 호출
    print(CaseDataManager.get_case_data())


if __name__ == "__main__":
    print("\n===== 법정 시뮬레이터 테스트 =====")
    
    # 초기화
    print("\n[1] 컨트롤러 초기화 중...")
    asyncio.run(CaseDataManager.initialize())
    print("✅ 초기화 완료")
    
    # 사건 생성 테스트
    print("\n[2] 사건 생성 테스트 중...")
    try:
        case_summary = asyncio.run(CaseDataManager.generate_case_stream())
        print("✅ 사건 생성 성공")
        print("\n📄 생성된 사건:")
        print("-" * 50)
        print(case_summary)
        print("-" * 50)
    except Exception as e:
        print(f"❌ 사건 생성 실패: {e}")
    
    # 프로필 생성 테스트
    print("\n[3] 프로필 생성 테스트 중...")
    try:
        profiles_text = asyncio.run(CaseDataManager.generate_profiles_stream())
        print("✅ 프로필 생성 성공")
        print("\n📄 생성된 프로필 텍스트:")
        print("-" * 50)
        print(profiles_text)
        print("-" * 50)
    except Exception as e:
        print(f"❌ 프로필 생성 실패: {e}")
    
    # 프로필 파싱 테스트
    print("\n[4] 프로필 파싱 테스트 중...")
    try:
        profiles = CaseDataManager.get_profiles()
        if profiles and len(profiles) > 0:
            print(f"✅ 프로필 파싱 성공: {len(profiles)}개의 프로필 발견")
            print("\n📄 파싱된 프로필:")
            print("-" * 50)
            for i, profile in enumerate(profiles):
                print(f"프로필 {i+1}:")
                print(f"  이름: {profile.name}")
                print(f"  유형: {profile.type}")
                print(f"  맥락: {profile.context[:50]}..." if len(profile.context) > 50 else f"  맥락: {profile.context}")
                if hasattr(profile, 'gender'):
                    print(f"  성별: {profile.gender}")
                if hasattr(profile, 'age'):
                    print(f"  나이: {profile.age}")
                print()
            print("-" * 50)
        else:
            print("❌ 프로필 파싱 실패: 프로필이 없거나 비어 있습니다")
    except Exception as e:
        print(f"❌ 프로필 파싱 실패: {e}")
    
    # 증거 생성 테스트
    print("\n[5] 증거 생성 테스트 중...")
    try:
        evidences = asyncio.run(CaseDataManager.generate_evidences())
        if evidences and len(evidences) > 0:
            print(f"✅ 증거 생성 성공: {len(evidences)}개의 증거 발견")
            print("\n📄 생성된 증거:")
            print("-" * 50)
            for i, evidence in enumerate(evidences):
                print(f"증거 {i+1}:")
                print(f"  이름: {evidence.name}")
                print(f"  유형: {evidence.type}")
                print(f"  설명: {evidence.description}")
                print()
            print("-" * 50)
        else:
            print("❌ 증거 생성 실패: 증거가 없거나 비어 있습니다")
    except Exception as e:
        print(f"❌ 증거 생성 실패: {e}")
    
    # 종합 데이터 테스트
    print("\n[6] 종합 데이터 테스트 중...")
    try:
        case_data = CaseDataManager.get_case_data()
        if case_data:
            print("✅ 종합 데이터 생성 성공")
            print("\n📄 종합 데이터 요약:")
            print("-" * 50)
            
            # 문제가 되는 f-string 부분을 별도 변수로 분리
            newline = "\n"
            title_marker = "[사건 제목]:"
            
            # 사건 제목 추출
            if title_marker in case_data.case.outline:
                title_part = case_data.case.outline.split(title_marker)[1]
                title = title_part.split(newline)[0].strip()
            else:
                title = "제목 없음"
                
            print(f"사건 제목: {title}")
            print(f"프로필 수: {len(case_data.profiles)}")
            print(f"증거 수: {len(case_data.evidences)}")
            print("-" * 50)
        else:
            print("❌ 종합 데이터 생성 실패: 데이터가 없습니다")
    except Exception as e:
        print(f"❌ 종합 데이터 생성 실패: {e}")
    
    print("\n===== 테스트 완료 =====")