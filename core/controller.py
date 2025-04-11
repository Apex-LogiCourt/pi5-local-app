from dotenv import load_dotenv
load_dotenv()


from typing import List, Dict
from .case_generation.case_builder import make_case_summary, make_witness_profiles
from .data_models import CaseData, WitnessProfile

def __init__() -> CaseData:
    print("contoller.__init__ 실행")
    # 사건 요약 생성
    case_summary = make_case_summary()
    # 증인 프로필 생성
    witness_profiles = make_witness_profiles(case_summary)
    return CaseData(case_summary=case_summary, witness_profiles=witness_profiles)

#==============================================
# case_generation.py의 함수
# 사건 생성 및 요약
# case_generation.py -> chat.py로 넘겨줌
#============================================== 
def get_case_summary_wrapper():
    return make_case_summary()

def get_witness_profiles_wrapper():
    return make_witness_profiles()

#==============================================
# interrogator.py의 함수
# 단순히 함수 호출 목적
# interrogator.py -> chat.py로 넘겨줌
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
#==============================================  

def get_judge_result_wrapper(message_list):
    from verdict import get_judge_result
    return get_judge_result(message_list)


if __name__ == "__main__":
    print("main 실행")
    case_data = __init__()
    print(case_data.case_summary)
    print(case_data.witness_profiles)

