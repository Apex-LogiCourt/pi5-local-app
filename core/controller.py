from dotenv import load_dotenv
load_dotenv()


from typing import List, Dict
from .case_generation.case_builder import make_case_summary, make_witness_profiles
from .data_models import CaseData, Case, Profile, Evidence


# 싱글톤 패턴 적용
class CaseDataManager:
    _instance = None
    # 이 부분은 이해를 위한 선언이라 나중에는 다 삭제할 것임
    _case = Case(
        outline="",
        behind=""
    )
    _evidences = [Evidence(
        name="",
        type="",
        background="",
        description="" 
    )]
    _profiles = [Profile(
        name="",
        type="",
        background="",
        description=""
    )]
    _case_data : CaseData = None
    
    def __init__(self):
        # 새로운 인스턴스 생성 방지
        raise RuntimeError('이 클래스의 인스턴스를 직접 생성할 수 없습니다다ㅋ')
    
    @classmethod
    def initialize(cls) -> CaseData:
        if cls._case_data is None:
            print("controller 초기화 실행")
            cls._case_data = CaseData(cls._case, cls._profiles, cls._evidences)
            print(cls._case_data)
            # 이 부분에서 각각 사건 개요, 참고인, 증거 데이터를 case_builder에서 가져와서 호출할 예정
            # 출력 결과에 따라 JSON 형태로 구조화 하기 위한 파싱 작업 필요 
        return cls._case_data

    # getter 메소드 추가 
    # 호출 방식 예시 : CaseDataManager.get_case_data()

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
# case_generation.py의 함수
# 사건 생성 및 요약
# case_generation.py -> chat.py로 넘겨줌
# 삭제 예정 
#============================================== 
def get_case_summary_wrapper():
    return make_case_summary()

def get_witness_profiles_wrapper():
    return make_witness_profiles()

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
    print("main 실행")
    case_data = __init__()
    print(case_data.case_summary)
    print(case_data.witness_profiles)

