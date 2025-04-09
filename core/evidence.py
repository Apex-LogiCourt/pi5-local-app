from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.output_parsers import (
    JsonOutputParser,
    StrOutputParser
)
from pydantic import BaseModel, Field
from data_models import Case, Profile, Evidence, CaseData
from typing import List, Literal
from dotenv import load_dotenv
load_dotenv()

CREATE_EVIDENCE_TEMPLATE = """
다음의 사건 개요를 바탕으로 재판에 필요한 증거를 제공해주세요.
{case_data}
참여자 목록: {profile}

단, 모든 증거는 재판에 참석한 인원과 연관이 있어야 합니다.
증거품의 종류에는 제한이 없으나 답변은 다음의 형식을 따라야 합니다.

name: 증거품 이름(명사), "한 단어"만 사용하세요. (예시: 카세트 테이프, 식칼 등)
type: 증거 제출 주체(attorney, prosecutor)
description: 증거에 대한 설명. 한 문장으로 설명하세요.

제공된 세 개의 키워드명을 기준으로 JSON 형식으로 답하세요.
"""

## make_evidence(Case, List[Profile]) -> List[Evidence]: 최초 증거 생성, 3개 생성되는 듯.
## update_evidence_description(Evidence, CaseData) -> Evidence: 넘겨준 Evidence의 설명 추가

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
    evidences = convert_data_class(response)

    for e in evidences:
        e.picture = make_evidence_image(e.name)

    return evidences

def update_evidence_description(evidence: Evidence, casedata: CaseData) -> Evidence:
    llm = get_llm()
    prompt = ChatPromptTemplate.from_messages([
        ("system",
        """
        주어진 증거품 데이터와 상황을 바탕으로 증거품의 설명을 추가하세요.
        증거품명: {evidence_name}
        증거 제출 주체: {evidence_type}
        증거품 설명: {evidence_description}

        {case_data}

        추가될 증거품의 설명을 한 문장으로 대답하세요.
        기존의 증거품 설명과 동일한 내용은 제외하고, 추가될 내용만 대답하세요.
        """)
    ])
    chain = prompt | llm | StrOutputParser()

    res = chain.invoke({
        "evidence_name": evidence.name,
        "evidence_type": evidence.type,
        "evidence_description": evidence.description,
        "case_data": format_case_data(casedata)
    })

    evidence.description.append(res)
    return evidence

def format_case_data(casedata: CaseData):
    f_case = format_case(casedata.case)
    f_profiles = format_profiles(casedata.profiles)
    return (f_case + "\n" + f_profiles)

def format_case(case: Case) -> str:
    return f"""사건 개요: {case.outline} 사건 내막: {case.behind}"""

def format_profiles(raw_profiles):
    profiles = "\n".join([f"- {p}" for p in raw_profiles])
    return profiles

def convert_data_class(data: List[dict]) -> List[Evidence]:
    import ast
    if "evidence" in data:
        data = data["evidence"]

    result = []
    for item in data:
        desc = item["description"]
        if isinstance(desc, str):
            desc = [desc] #str to List
        result.append(Evidence(
            name=item["name"],
            type=item["type"],
            picture=None,
            description=desc
        ))
    return result

def make_evidence_image(name):
    try:
        path = get_naver_image(name)
        resize_img(path, path, 200)
    except:
        return -1
    return path

def get_naver_image(name): #이미지 처리 로직 개선 필요... 엉뚱한 이미지는 어떻게 처리??
    import urllib.parse
    import urllib.request
    import requests
    import xml.etree.ElementTree as xmlET
    import os

    client_id = os.environ.get("X-Naver-Client-Id")
    client_secret = os.environ.get("X-Naver-Client-Secret")

    params = {
        'query': name,
        'display': "10",
    }
    query_string = urllib.parse.urlencode(params)
    url = "https://openapi.naver.com/v1/search/image.xml?" + query_string
    urlRequest = urllib.request.Request(url)
    urlRequest.add_header("X-Naver-Client-Id", client_id)
    urlRequest.add_header("X-Naver-Client-Secret", client_secret)
    
    response = urllib.request.urlopen(urlRequest)
    res_code = response.getcode()
    if(res_code == 200):
        response_body = response.read().decode('UTF-8')
    else:
        print("Error Code: " + res_code)
        return -1
    img_urls = xmlET.fromstring(response_body).findall('channel/item/link')
    
    for i in range(10):
        my_save_path = "data/evidence_resource/" + name + ".jpg"
        img_res = requests.get(img_urls[i].text, stream=True)

        with open(my_save_path, "wb") as file:
            for chunk in img_res.iter_content(1024):
                file.write(chunk)
            try:
                f = open(my_save_path, "rt")
                c = f.readlines()
                continue
            except:
                f.close()
                return my_save_path
    return img_res

def resize_img(input_path, output_path, target_size):
    from PIL import Image
    try:
        with Image.open(input_path) as img:
            img = img.resize((target_size, target_size))
            img.save(output_path)
    except:
        return -1
    return 0



### TEST CODE ###
c = Case(
    outline="""
    피해자 김현수는 성공한 사업가로, 최근 은퇴 후 유산을 정리하고 있었습니다. 그의 조카 김민준은 김현수와 가까운 사이였으며, 유산 상속에 큰 관심을 보이고 있었습니다.
    김현수는 자신의 저택에서 의식불명 상태로 발견되었고, 이틀 후 사망했습니다. 경찰은 김현수의 죽음이 단순한 사고가 아니라 누군가에 의해 계획된 범죄일 가능성을 제기했습니다. 사건 당일, 김민준은 저택을 방문했던 것으로 확인되었으며, 김현수의 유산에 관한 논의가 있었던 것으로 밝혀졌습니다.
    """,
    behind=""
)
plist = []
plist.append(
    Profile(
        name="김민준",
        type="suspect",
        context="32세, 김현수의 조카로 현재 중소기업에서 근무 중입니다. 그는 평소 삼촌의 유산을 통해 사업 확장을 꿈꾸고 있었습니다. 사건 발생 시점에 김민준은 저택을 방문했으나 이후 친구들과 저녁 식사 모임이 있었다고 주장합니다."
    )
)
plist.append(
    Profile(
        name="이상훈",
        type="witness",
        context="사건 당일 저녁, 김민준이 친구와 함께 있었으며, 그의 행동에 의심스러운 점이 없었다는 증언입니다."
    )
)
cd = CaseData(
    case = c,
    profiles=plist,
    evidences=None
)
res = make_evidence(case_data=c, profiles=plist)
print(res)
print("\n\n")
update_evidence_description(res[0], cd)
print(res[0].description)