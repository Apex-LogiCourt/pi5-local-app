from dotenv import load_dotenv
load_dotenv()

from .case_generation.case_builder import make_case_summary, make_witness_profiles

def __init__():
    # 사건 요약 생성
    case_summary = make_case_summary()
    # 증인 프로필 생성
    witness_profiles = make_witness_profiles(case_summary)
    return case_summary, witness_profiles

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

def ask_witness_wrapper(question, name, wtype, case_summary):
    from interrogation.interrogator import ask_witness
    return ask_witness(question, name, wtype, case_summary)


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


case_summary, witness_profiles = __init__()
print(case_summary)
print(witness_profiles)
