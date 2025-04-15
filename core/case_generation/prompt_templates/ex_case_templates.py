#==============================================
# 템플릿 갈아끼면 쉽게 사용 가능
# 원하는 형식으로 템플릿 만들어서 사용 가능
#============================================== 

# 사건 생성 관련 프롬프트 템플릿
CASE_SUMMARY_TEMPLATE = """
다음 형식에 맞춰 재판 게임을 위한 사건 개요를 생성해주세요.
사건 개요는 구체적으로 작성해주세요.
피고와 피해자가 분명히 드러나야 합니다.
피고의 유무죄를 판단하는 게임입니다.

[사건 제목]: (간단한 제목)
[사건 배경]: (사건 발생 이전의 상황, 인물들의 관계 등 2-3문장)
[사건 개요]: (3-4문장으로 상세한 사건 설명)
"""

# 등장인물 생성을 위한 템플릿
CREATE_CHARACTER_TEMPLATE = """
생성된 사건에 맞춰 등장인물 4명을 생성해주세요.
현장은 법원입니다.
목격자, 참고인은 피고, 피해자와 관련된 사람이어야 합니다.
목격자, 참고인은 법정에서 증인역할을 합니다.

피고 : OOO 
    - 직업 : (OOO의 직업)
    - 성격 : (OOO의 성격 1줄로 간략하게)
    - 배경 : (OOO의 재판 출석 배경을 2줄로 간략하게)

--------------------------------
    
피해자 : OOO
    - 직업 : (OOO의 직업)
    - 성격 : (OOO의 성격 1줄로 간략하게)
    - 배경 : (OOO의 배경을 2줄로 간략하게)

--------------------------------
    
목격자 : OOO
    - 직업 : (OOO의 직업)
    - 성격 : (OOO의 성격 1줄로 간략하게)
    - 배경 : (OOO의 재판 출석 배경을 2줄로 간략하게)

--------------------------------
    
참고인 : OOO
    - 직업 : (OOO의 직업)
    - 성격 : (OOO의 성격 1줄로 간략하게)
    - 배경 : (OOO의 재판 출석 배경을 2줄로 간략하게)

사건 개요:
{case_summary}
"""
CASE_BEHIND_TEMPLATE = """
당신은 모든 사실을 알고 있는 나레이터 입니다. 
아래 사건 개요에 대한 '사건의 진실'을 작성해주세요.

사건 개요:
{case_summary}

등장인물:
{character}

다음 조건을 따라야 합니다:
- 범인은 등장인물 중 한 명이어야 합니다.
- 현실적인 내용이여야 합니다.
- 범인의 동기와 사건의 진실을 작성해주세요.
[사건의 진실]:
- 피고 : 유죄? 무죄?
- 범인 : 누구?
"""