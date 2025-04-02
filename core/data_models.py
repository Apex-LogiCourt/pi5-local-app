from dataclasses import dataclass
from typing import List

#==============================================
# 데이터만 저장하기 위한 데이터클래스 선언 
#==============================================
@dataclass
class WitnessProfile:
    name: str
    type: str
    background: str

@dataclass
class CaseData:
    case_summary: str
    witness_profiles: List[WitnessProfile]