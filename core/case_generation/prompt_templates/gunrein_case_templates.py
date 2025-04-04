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

# 증거 생성을 위한 템플릿
EVIDENCE_TEMPLATE = """
위 사건 개요를 바탕으로 검사측과 변호사측의 증거를 생성해주세요.
각각 2개씩의 증거를 생성하고, 증거는 명사 형태로 작성해주세요.
반드시 아래 형식의 JSON만 출력해주세요. 다른 설명이나 텍스트는 포함하지 마세요.

{{
    "prosecution": [
        {{
            "name": "검사측 증거1",
            "description": "증거1에 대한 설명"
        }},
        {{
            "name": "검사측 증거2",
            "description": "증거2에 대한 설명"
        }}
    ],
    "defense": [
        {{
            "name": "변호사측 증거1",
            "description": "증거1에 대한 설명"
        }},
        {{
            "name": "변호사측 증거2",
            "description": "증거2에 대한 설명"
        }}
    ]
}}

사건 개요:
{case_summary}
"""

# 사건 내막 생성을 위한 템플릿
CASE_BEHIND_TEMPLATE = """
주어진 사건 개요와 증거를 바탕으로 사건의 내막을 생성해주세요.
내막은 사건의 진실과 그 배경, 그리고 핵심 포인트를 포함해야 합니다.

사건 개요:
{case_summary}

증거:
{evidence}

다음 JSON 형식으로 응답해주세요:
{{
    "truth": "피고인의 유무죄 여부 (유죄/무죄)",
    "explanation": "사건의 진실에 대한 상세 설명 (3-4문장)",
    "key_points": [
        "핵심 포인트 1",
        "핵심 포인트 2",
        "핵심 포인트 3"
    ]
}}

주의사항:
1. JSON 형식만 출력하고 다른 텍스트는 포함하지 마세요.
2. 진실은 반드시 "유죄" 또는 "무죄"로만 표시해주세요.
3. 설명은 3-4문장으로 간단명료하게 작성해주세요.
4. 핵심 포인트는 3개 이상 작성해주세요.
5. 모든 내용은 사건 개요와 증거를 기반으로 합리적으로 작성해주세요.
"""
