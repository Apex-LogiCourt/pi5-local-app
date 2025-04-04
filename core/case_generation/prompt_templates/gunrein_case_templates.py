#==============================================
# 템플릿 갈아끼면 쉽게 사용 가능
# 원하는 형식으로 템플릿 만들어서 사용 가능
#============================================== 

# 사건 생성 관련 프롬프트 템플릿
CASE_SUMMARY_TEMPLATE = """
다음 형식에 맞춰 재판 게임을 위한 사건 개요를 생성해주세요.
사건 개요는 더 구체적이고 현실적이며, 피고인, 피해자, 목격자, 참고인의 관계를 포함해주세요.
피고의 유무죄를 판단하는 게임입니다.

[사건 제목]: (간단한 제목)
[사건 배경]: (사건 발생 이전의 상황, 인물들의 관계 등 2-3문장)
[사건 개요]: (3-4문장으로 상세한 사건 설명)
[등장 인물]: 피고인, 피해자, 목격자, 참고인
"""

# 등장인물 추출을 위한 템플릿
CHARACTER_EXTRACTION_TEMPLATE = """
위 사건 개요에서 등장인물들의 이름을 추출하여 JSON 형식으로 변환해주세요.
반드시 아래 형식의 JSON만 출력해주세요. 다른 설명이나 텍스트는 포함하지 마세요.

{{
    "defendant": "피고인 이름",
    "victim": "피해자 이름",
    "witness": "목격자 이름",
    "reference": "참고인 이름"
}}

사건 개요:
{case_summary}
"""

# 등장인물 프로필 생성을 위한 템플릿
WITNESS_PROFILES_TEMPLATE = """
위 사건 개요에서 등장인물들의 정보를 추출하여 JSON 형식으로 변환해주세요.
반드시 아래 형식의 JSON만 출력해주세요. 다른 설명이나 텍스트는 포함하지 마세요.

[
    {{
        "name": "{defendant_name}",
        "type": "defendant",
        "context": "피고인으로서의 역할과 배경"
    }},
    {{
        "name": "{victim_name}",
        "type": "victim",
        "context": "피해자로서의 역할과 배경"
    }},
    {{
        "name": "{witness_name}",
        "type": "witness",
        "context": "목격자로서의 역할과 배경"
    }},
    {{
        "name": "{reference_name}",
        "type": "reference",
        "context": "참고인으로서의 역할과 배경"
    }}
]

사건 개요:
{case_summary}
"""
