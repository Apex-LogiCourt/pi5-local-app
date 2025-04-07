from dataclasses import dataclass
from typing import List, Literal

#==============================================
# 데이터만 저장하기 위한 데이터클래스 선언 
#==============================================

@dataclass
class Case:
    outline: str  # 사건 개요
    behind : str  # 사건 내막 -- 사건의 진실 진짜 피고는 진범이었나?

@dataclass
class Profile:
    name: str  # 사람 이름
    type: Literal["witness", "reference", "defendant"]  # 참고인 유형
    context: str  # 출석 맥락 -- 어떤 사연으로 여기 출석하게 되었는지

@dataclass
class Evidence:
    name: str  # 증거품 이름(명사형) 
    type: Literal["attorney", "prosecutor"]  # 제출 주체
    description: List[str]  # 증거 설명 (추가 가능)
    picture: str  # 사진 경로 (향후 구현)


# Controller에서 최종적으로 다른 모듈로 념겨줄 데이터 형식이에용
# 아직 구현이 안 됐지만 이렇게 넘어올거라고 믿고 작업해주세요 
@dataclass
class CaseData:
    case: Case
    profiles: List[Profile]
    evidences: List[Evidence]



