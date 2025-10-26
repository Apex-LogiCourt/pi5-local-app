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

# from controller import CaseDataManager #테스트 할 때만 돌려보세용 
# import asyncio #여기도 주석해제

CREATE_EVIDENCE_TEMPLATE = """
다음의 사건 개요를 바탕으로 재판에 필요한 증거를 제공해주세요.
{case_data}
참여자 목록: {profile}

단, 모든 증거는 재판에 참석한 인원과 연관이 있어야 합니다.
증거품의 종류에는 제한이 없으나 답변은 다음의 형식을 따라야 합니다.

기본 증거품의 형식: {format_instructions}

다음 형식의 JSON 배열로 4개의 증거를 출력하세요:
[
  {{ "name": "증거명", "type": "attorney", "description": ["한 문장 설명"] }},
  ...
]

"type" 필드를 기준으로 attorney 2개, prosecutor 2개를 포함해야 합니다.
그러나 출력은 하나의 리스트 형태로 제공해야 하며, "attorney": [...], "prosecutor": [...] 같은 형식은 사용하지 마세요.
"""

## make_evidence(Case, List[Profile]) -> List[Evidence]: 최초 증거 생성
## update_evidence_description(Evidence, CaseData) -> Evidence: 넘겨준 Evidence의 설명 추가

class EvidenceModel(BaseModel):
    name: str = Field(description="한 단어의 증거품 이름(명사형)")
    type: Literal["attorney", "prosecutor"] = Field(description="제출 주체")
    description: List[str] = Field(description="한 문장의 증거 설명")

def get_llm():
    # return ChatOpenAI(model="gpt-4o-mini", temperature=1.0)
    return ChatOpenAI(model="gpt-4o-mini")

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
        "case_data": str_case_data,
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
    # 데이터 형식 검증 
    """
    evidences = convert_data_class(response)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    File "D:\WS\pi5-local-app\core\evidence.py", line 111, in convert_data_class
    return [Evidence.from_dict(item) for item in data]
            ^^^^^^^^^^^^^^^^^^^^^^^^
    File "D:\WS\pi5-local-app\core\data_models.py", line 28, in from_dict       
    desc = data.get("description", [])
           ^^^^^^^^
    AttributeError: 'str' object has no attribute 'get'
    이 부분에서 가끔씩 뻑남 에러처리 해줘야 할듯 data가 리스트 타입이 아니고 str로 잡히네 
    data 찍어보니까 data["증거품"] 이렇게 내려올 때가 있음 계속 테스팅 하면서 예외처리 잡아줘야 될듯 
    
    >> 2025-05-04::youngho
    메인 템플릿 수정 후 혼자 테스트 보았을 때 문제없이 동작.
    그러나 LLM 특성상 100% 보장은 없으므로, data 타입 확인하고 케이스별 수동 예외처리 필요
    혹은 이 부분에서 에러 발생시 컨트롤러 측에서 다시 generate_evidences 하는 식으로 처리도 가능해 보임(높은 확률로 정상 동작하므로).
    """
    print("[Debug/Evidence] type(data): "+ str(type(data)))
    print("[Debug/Evidence] convert_data_class의 data:", data)
    if isinstance(data, dict):
        if "증거품" in data:
            data = data["증거품"]
        elif "evidence" in data:
            data = data["evidence"]
    return [Evidence.from_dict(item) for item in data]

def make_evidence_image(name):
    try:
        path = create_image_by_ai(name)
        resize_img(path, path, 200)
    except:
        return -1
    return path

def resize_img(input_path, output_path, target_size):
    from PIL import Image
    try:
        with Image.open(input_path) as img:
            img = img.resize((target_size, target_size))
            img.save(output_path)
    except:
        return -1
    return 0

def get_evidence_name_for_prompt(name):
    llm = get_llm()
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a language assistant that rewrites Korean terms into simple English phrases or keywords that can be visualized easily as pictograms. Avoid literal translation and aim for intuitive, visual concepts. Output only 1–3 words with no explanations."),
        ("human", "input: {evidence_name}")
    ])
    chain = prompt | llm | StrOutputParser()
    res = chain.invoke({
        "evidence_name": name,
    })
    return res

def create_image_by_ai(name: str):
    import json
    import requests
    import datetime
    from dotenv import dotenv_values
    
    env = dotenv_values()
    # key = "Token " + env.get("REPLICATE_API_KEY") # 직접 요청시 사용하는 키
    key = env.get("REPLICATE_API_KEY")
    today = datetime.datetime.now()
    formatted_date = today.strftime("%y-%m-%d")
    new_name = name.replace(" ", "-")

    prompt_name = get_evidence_name_for_prompt(name)
    save_path = "data/evidence_resource/" + formatted_date + "-" + new_name + ".png"

    import replicate
    client = replicate.Client(api_token=key)
    model = "stability-ai/stable-diffusion-3.5-large"
    inputs = {
        "prompt": "A vector-style black and white pictogram of " + prompt_name + ", clean and black outlines, white background, minimal detail, symbol-like, high contrast, centered subject, flat design, no shading, no gradients, icon format, simple geometric shapes, digital vector art, Adobe Illustrator style",
        "aspect_ratio": "1:1",
        "output_format": "png",
        # "cfg": 6,                 #TEST
        # "steps": 40,              #TEST
        # "output_quality": 95,     #TEST
        # "prompt_strength": 0.85   #TEST
    }
    output = client.run(model, input=inputs)

    print(output)
    try:
        with open(save_path, "wb") as file:
            file.write(output.read())
            print(f"[{name}] 이미지 저장 성공: {save_path}")
    except:
        print(f"[{name}] 이미지 저장 실패: {output}")

    # if output and isinstance(output, list):
    #     image_url = output[0]
    #     print(f"[{name}] 이미지 URL: {image_url}")

    #     response = requests.get(image_url)
    #     if response.status_code == 200:
    #         with open(save_path, "wb") as f:
    #             f.write(response.content)
    #         print(f"[{name}] 이미지 저장 성공: {save_path}")
    #     else:
    #         print(f"[{name}] 이미지 저장 실패: {response.status_code}")
    # else:
    #     print(f"[{name}] 이미지 요청 실패")


    # JSON 필요시 아래 코드로 사용
    # payload = {
    #     "input": {
    #         "prompt": "A simple black and white pictogram of a " + prompt_name + ", minimalist design, vector art, flat colors, clean lines, white background, high contrast, clear shapes, centered, bold outline, outlined",
    #         "aspect_ratio": "1:1",
    #         "output_format": "png",
    #         "cfg": 6,
    #         "prompt_strength": 0.85,
    #         "output_quality": 95
    #     }
    # }

    # response = requests.post(
    #     "https://api.replicate.com/v1/models/stability-ai/stable-diffusion-3.5-large/predictions",
    #     headers={
    #         "Authorization": key,
    #         "Content-Type": "application/json",
    #         "Prefer": "wait"
    #     },
    #     json=payload
    # )

    # if response.status_code in [200, 201]:
    #     output = response.json()
    #     print(json.dumps(output, indent=4))  # TEST
    #     with open(save_path + ".json", "w") as f:
    #         json.dump(output, f, indent=4)

    #     if "output" in output and output["output"]:
    #         image_url = output["output"][0]
    #         image_data = requests.get(image_url).content
    #         with open(save_path, 'wb') as file:
    #             file.write(image_data)
    # else:
    #     print(f"Error {response.status_code}: {response.text}")
    #     return response.status_code
    return save_path


### TEST CODE ###
if __name__ == "__main__":
    # res = create_image_by_ai("메시지 기록")
    # print(res)
    print("start")
    t = make_evidence_image("a simple car")
    print(t)

    # CaseDataManager import 한 뒤에 테스트 할 때만 돌려보세용  
    # from controller import CaseDataManager #테스트 할 때만 돌려보세용 
    # import asyncio #여기도 주석해제
    # asyncio.run(CaseDataManager.initialize())  # CaseDataManager 초기화 
    # asyncio.run(CaseDataManager.generate_case_stream())  # case 생성 
    # asyncio.run(CaseDataManager.generate_profiles_stream())  # 프로필 생성
    # res = make_evidence(case_data=CaseDataManager.get_case(), 
    #                     profiles=CaseDataManager.get_profiles())
    # print("\n\n", res)


    # c = Case(
    #     outline="""
    #     피해자 김현수는 성공한 사업가로, 최근 은퇴 후 유산을 정리하고 있었습니다. 그의 조카 김민준은 김현수와 가까운 사이였으며, 유산 상속에 큰 관심을 보이고 있었습니다.
    #     김현수는 자신의 저택에서 의식불명 상태로 발견되었고, 이틀 후 사망했습니다. 경찰은 김현수의 죽음이 단순한 사고가 아니라 누군가에 의해 계획된 범죄일 가능성을 제기했습니다. 사건 당일, 김민준은 저택을 방문했던 것으로 확인되었으며, 김현수의 유산에 관한 논의가 있었던 것으로 밝혀졌습니다.
    #     """,
    #     behind=""
    # )
    # plist = []
    # plist.append(
    #     Profile(
    #         name="김민준",
    #         type="suspect",
    #         context="32세, 김현수의 조카로 현재 중소기업에서 근무 중입니다. 그는 평소 삼촌의 유산을 통해 사업 확장을 꿈꾸고 있었습니다. 사건 발생 시점에 김민준은 저택을 방문했으나 이후 친구들과 저녁 식사 모임이 있었다고 주장합니다."
    #     )
    # )
    # plist.append(
    #     Profile(
    #         name="이상훈",
    #         type="witness",
    #         context="사건 당일 저녁, 김민준이 친구와 함께 있었으며, 그의 행동에 의심스러운 점이 없었다는 증언입니다."
    #     )
    # )
    # cd = CaseData(
    #     case = c,
    #     profiles=plist,
    #     evidences=None
    # )
    # res = make_evidence(case_data=c, profiles=plist)
    # print("\n\n")
    # update_evidence_description(res[0], cd)
    # print(res[0].description)

