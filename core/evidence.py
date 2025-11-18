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
검사에게 유리한 증거를 2개, 변호사에게 유리한 증거를 2개 제공해주세요.
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

    # 이미지는 나중에 병렬로 생성 (일단 None으로 설정)
    for e in evidences:
        e.picture = None

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
        if path == -1 or path is None:
            print(f"[{name}] 이미지 생성 실패")
            return None

        # resize 실패해도 원본 경로 반환
        result = resize_img(path, path, 200)
        if result == -1:
            print(f"[{name}] 이미지 리사이즈 실패, 원본 사용")

        return path
    except Exception as e:
        print(f"[{name}] 이미지 생성 중 예외 발생: {e}")
        import traceback
        traceback.print_exc()
        return None

def generate_evidence_images_parallel(evidences: List[Evidence]) -> List[Evidence]:
    """증거품 이미지를 병렬로 생성"""
    import concurrent.futures

    def generate_single_image(evidence):
        """단일 증거품의 이미지 생성"""
        try:
            evidence.picture = make_evidence_image(evidence.name)
            print(f"[Evidence] {evidence.name} 이미지 생성 완료: {evidence.picture}")
        except Exception as e:
            print(f"[Evidence] {evidence.name} 이미지 생성 실패: {e}")
            evidence.picture = None
        return evidence

    # ThreadPoolExecutor로 병렬 처리
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(generate_single_image, e) for e in evidences]
        # 모든 작업이 완료될 때까지 대기
        concurrent.futures.wait(futures)

    return evidences

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

def get_generic_evidence_name(name):
    """사람 이름이 포함된 증거품 이름을 일반화된 이름으로 변환"""
    llm = get_llm()
    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 증거품 이름을 일반화하는 어시스턴트입니다.
        증거품 이름에서 사람 이름(고유명사)을 제거하고 일반적인 증거품 명칭으로 변환하세요.
        
        예시:
        - "안기효의 증언" → "목격자 진술서"
        - "김민수의 일기장" → "개인 일기장"
        - "이영희의 편지" → "편지"
        - "박철수의 통화기록" → "통화기록"
        - "CCTV 영상" → "CCTV 영상" (사람 이름이 없으면 그대로)
        
        출력은 간결한 명사형으로만 작성하고, 설명이나 부가 정보는 포함하지 마세요."""),
        ("human", "증거품 이름: {evidence_name}")
    ])
    chain = prompt | llm | StrOutputParser()
    res = chain.invoke({
        "evidence_name": name,
    })
    return res.strip()

def create_image_by_ai(name: str):
    import json
    import requests
    import datetime
    from dotenv import dotenv_values
    import os
    import re

    env = dotenv_values()
    # key = "Token " + env.get("REPLICATE_API_KEY") # 직접 요청시 사용하는 키
    key = env.get("REPLICATE_API_KEY")
    today = datetime.datetime.now()
    formatted_date = today.strftime("%y-%m-%d")
    timestamp = today.strftime("%Y-%m-%d %H:%M:%S")

    # 사람 이름이 포함된 경우 일반화된 이름으로 변환
    generic_name = get_generic_evidence_name(name)
    # 모든 공백을 하이픈으로 변환 (여러 공백도 처리)
    new_name = re.sub(r'\s+', '-', generic_name.strip())

    prompt_name = get_evidence_name_for_prompt(generic_name)
    save_path = "data/evidence_resource/" + formatted_date + "-" + new_name + ".png"

    # 기존 파일이 있으면 재사용
    if os.path.exists(save_path):
        print(f"[{name}] 기존 이미지 파일 재사용: {save_path}")
        return save_path

    # 디렉토리가 없으면 생성
    os.makedirs("data/evidence_resource", exist_ok=True)

    import replicate
    import time
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

    # 재시도 로직 (최대 3번)
    max_retries = 3
    for attempt in range(max_retries):
        try:
            output = client.run(model, input=inputs)
            print(output)

            with open(save_path, "wb") as file:
                file.write(output.read())
                print(f"[{name}] 이미지 저장 성공: {save_path}")
            break  # 성공하면 루프 종료
        except Exception as e:
            print(f"[{name}] 이미지 생성 시도 {attempt + 1}/{max_retries} 실패: {e}")
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2  # 2초, 4초, 6초 대기
                print(f"[{name}] {wait_time}초 후 재시도...")
                time.sleep(wait_time)
            else:
                print(f"[{name}] 모든 재시도 실패, 기본 이미지 사용")
                import traceback
                traceback.print_exc()
                # 기본 placeholder 이미지 경로 반환
                return "core/assets/evidence_icon.png"
    
    # JSON 로그 파일에 메타데이터 저장
    log_json_path = "data/evidence_resource/evidence_log.json"
    evidence_data = {
        "timestamp": timestamp,
        "original_name": name,
        "generic_name": generic_name,
        "prompt_name": prompt_name,
        "file_path": save_path
    }
    
    # 기존 JSON 파일이 있으면 읽어오기
    if os.path.exists(log_json_path):
        try:
            with open(log_json_path, "r", encoding="utf-8") as f:
                log_data = json.load(f)
        except:
            log_data = []
    else:
        log_data = []
    
    # 새 데이터 추가
    log_data.append(evidence_data)
    
    # JSON 파일에 저장
    try:
        os.makedirs(os.path.dirname(log_json_path), exist_ok=True)
        with open(log_json_path, "w", encoding="utf-8") as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
        print(f"[{name}] JSON 로그 저장 성공: {log_json_path}")
    except Exception as e:
        print(f"[{name}] JSON 로그 저장 실패: {e}")

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

