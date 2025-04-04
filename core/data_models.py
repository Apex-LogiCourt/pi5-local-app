from dataclasses import dataclass
from typing import List, Literal

#==============================================
# 데이터만 저장하기 위한 데이터클래스 선언 
#==============================================

@dataclass
class Case:
    outline: str  # 사건 개요
    behind : str

@dataclass
class Profile:
    name: str  # 사람 이름
    type: Literal["witness", "reference", "defendant"]  # 참고인 유형
    context: str  # 출석 맥락

@dataclass
class Evidence:
    name: str  # 증거품 이름
    type: Literal["attorney", "prosecutor"]  # 제출 주체
    description: List[str]  # 증거 설명 (추가 가능)
    # picture: str  # 내부 사진 경로 (향후 구현)

@dataclass
class CaseData:
    case: Case
    profiles: List[Profile]
    evidences: List[Evidence]