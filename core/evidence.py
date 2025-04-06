from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.pydantic_v1 import Field
from langchain_core.output_parsers import (
    JsonOutputParser
)
from pydantic import BaseModel
from data_models import Case, Profile, Evidence
from typing import List, Literal
from dotenv import load_dotenv
load_dotenv()

CREATE_EVIDENCE_TEMPLATE = """
다음의 사건 개요를 바탕으로 재판에 필요한 증거를 제공해주세요.
{case_data}
참여자 목록: {profile}

단, 모든 증거는 재판에 참석한 인원과 연관이 있어야 합니다.
증거품의 종류에는 제한이 없으나 답변은 다음의 형식을 따라야 합니다.

name: 증거품 이름(명사)
type: 증거 제출 주체(attorney, prosecutor)
description: 증거에 대한 설명. 한 문장으로 설명하세요.

제공된 세 개의 키워드명을 기준으로 JSON 형식으로 답하세요.
"""


class EvidenceModel(BaseModel):
    name: str = Field(description="증거품 이름(명사형)")
    type: Literal["attorney", "prosecutor"] = Field(description="제출 주체")
    description: List[str] = Field(description="증거 설명")

def get_llm():
    return ChatOpenAI(model="gpt-4o-mini", temperature=1.0)


def make_evidence(case_data: Case, profiles: List[Profile]) -> List[Evidence]:
    str_case_data = format_case(case_data)
    str_profiles_data = format_profiles(profiles)

    llm = get_llm()
    parser = JsonOutputParser(pydantic_object=EvidenceModel)
    prompt = PromptTemplate(
        template = CREATE_EVIDENCE_TEMPLATE,
        input_variables=["case_data", "profile"],
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    chain = prompt | llm | parser

    response = chain.invoke({
        "case_data":str_case_data,
        "profile": str_profiles_data
    })
    return convert_data_class(response)


def format_case(case: Case) -> str:
    return f"""사건 개요: {case.outline} 사건 내막: {case.behind}"""

def format_profiles(raw_profiles):
    profiles = "\n".join([f"- {p}" for p in raw_profiles])
    return profiles

def convert_data_class(data: List[dict]) -> List[Evidence]:
    result = []
    for item in data:
        desc = item["description"]
        if isinstance(desc, str):
            desc = [desc] #str to List
        result.append(Evidence(
            name=item["name"],
            type=item["type"],
            description=desc
        ))
    return result