from dataclasses import dataclass, asdict
from typing import List, Literal, Dict
from enum import Enum, auto
from pydantic import BaseModel, Field

#==============================================
# 데이터만 저장하기 위한 데이터클래스 선언 
#==============================================

@dataclass
class Case:
    outline: str  # 사건 개요
    behind : str  # 사건 내막 -- 사건의 진실 진짜 피고는 진범이었나?

@dataclass
class Profile:
    type: Literal["witness", "reference", "defendant", "victim"]  # 참고인 유형
    name: str  # 사람 이름
    gender: Literal["남자", "여성"]  # 성별
    age: int                     # 나이
    personality: str             #성격 특성
    context: str  # 출석 맥락 -- 어떤 사연으로 여기 출석하게 되었는지
    voice: str  # 음성
    
@dataclass
class Evidence:
    id: int  # 증거 ID (자동 증가)
    name: str  # 증거품 이름(명사형) 
    type: Literal["attorney", "prosecutor"]  # 제출 주체 
    description: List[str]  # 증거 설명 (추가 가능)
    picture: str  # 사진 경로 (향후 구현)

    _cnt : int = 0  

    @classmethod
    def from_dict(cls, data: dict) -> 'Evidence':
        cls._cnt += 1
        desc = data.get("description", [])
        if isinstance(desc, str):
            desc = [desc]  # str to List
        return cls(
            id=cls._cnt,  # 자동 증가
            name=data["name"],
            type=data["type"],
            description=desc,
            picture=None
        )

@dataclass
class CaseData:
    case: Case
    profiles: List[Profile]
    evidences: List[Evidence]


#==============================================
# 게임 상태 변수
#==============================================

class Phase(Enum):
    INIT = auto()
    DEBATE = auto()
    INTERROGATE = auto()
    JUDGEMENT = auto()
    END = auto()

class Role(Enum):
    PROSECUTOR = "prosecutor"
    ATTORNEY = "attorney"  

    def next(self):
        return Role.ATTORNEY if self == Role.PROSECUTOR else Role.PROSECUTOR

    def label(self) -> str:
        return {
            "prosecutor": "검사",
            "attorney": "변호사"
        }[self.value]


class GameState(BaseModel):
    phase: Phase = Phase.INIT
    turn: Role = Role.PROSECUTOR
    messages: List[Dict] = Field(default_factory=list)
    record_state : bool = False
    done_flags: Dict[Role, bool] = Field(default_factory=lambda: {
        Role.PROSECUTOR: False,
        Role.ATTORNEY: False
    })
    objection_count: Dict[Role, int] = Field(default_factory=lambda: {
        Role.PROSECUTOR: 0,
        Role.ATTORNEY: 0
    })
    current_profile: Profile = Field(default=None)
    tagged_evidence: Evidence = Field(default=None)