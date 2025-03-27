from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

def get_llm(model="gpt-4o"):
    """LLM 모델 가져오기"""
    llm = ChatOpenAI(model=model)  
    return llm

def get_full_case_story():
    """완전한 범죄 스토리 생성"""
    llm = get_llm()
    prompt = ChatPromptTemplate.from_template("""
        다음 형식에 맞춰 재판 게임을 위한 완전한 범죄 스토리를 생성해주세요.
        이 스토리는 게임 종료 후 실제 사건의 진실을 공개하는 데 사용됩니다.
        범죄 스토리는 범인이 누구인지, 실제로 어떤 일이 일어났는지, 증거가 어떻게 해석되는지 등 모든 진실을 담아야 합니다.

        등장인물들은 다양한 이름을 가져야 합니다. 모든 등장인물의 이름은 완전히 달라야 합니다.
        흔한 이름(홍길동, 김철수 등)은 사용하지 말고 독특하고 현실적인 이름을 사용해주세요.
        피해자, 용의자, 목격자, 관련자 등 모든 등장인물의 이름은 서로 달라야 합니다.
        성씨도 다양하게 사용해주세요. 특히 관련자1과 관련자2, 그리고 용의자의 이름은 서로 완전히 달라야 합니다.
        절대로 강민준, 정하늘 같은 이름은 사용하지 마세요(실제 사건과 혼동될 수 있음).
        사망한 피해자와 생존한 목격자/관련자의 이름이 같으면 안 됩니다.
        
        독특한 이름을 사용해주세요. 모든 등장인물의 이름은 성과 이름을 모두 포함해야 합니다.
        예시 이름: 백도현, 임지은, 손예진, 오현우, 노은서, 진승호, 권나라, 류태민, 장서윤 등
        
        [사건 제목]: (간단한 제목)
        [전체 스토리]: (사건의 실제 진실을 모두 담은 상세한 설명, 5-6문장)
        [진범]: (실제 범인이 누구인지, 만약 용의자가 범인이 아니라면 누가 범인인지)
        [동기]: (범행의 동기)
        [결정적 증거]: (범인을 가리키는 결정적 증거와 그 의미)
        [피해자 정보]: (이름=피해자이름 | 설명=피해자에 대한 설명)
        [용의자 정보]: (이름:고유한용의자이름 | 나이=?? | 직업=??)
        [관련자1]: (이름=고유한이름1|관계=목격자 또는 기타 관계|나이=??|비밀=...)
        [관련자2]: (이름=고유한이름2|관계=목격자 또는 기타 관계|나이=??|비밀=...)
        
        관련자들은 사건과 밀접한 관계가 있으며, 각자 숨기고 있는 비밀이나 동기가 있어야 합니다.
        용의자가 실제 범인일 수도 있고, 무고할 수도 있습니다.
        모든 등장인물의 이름은 성과 이름을 모두 포함하고 서로 완전히 달라야 합니다.
        피해자가 관련자로 중복 등장하지 않도록 해주세요. 특히 피해자가 사망한 경우 참고인으로 등장할 수 없습니다.
    """)

    chain = prompt | llm | StrOutputParser()
    return chain.invoke({})

def get_case_overview(full_story):
    """전체 스토리에서 게임 시작용 개요만 추출합니다."""
    llm = get_llm()
    
    # 피해자 정보 추출
    victim_info = ""
    for line in full_story.split("\n"):
        if line.startswith("[피해자 정보]:"):
            victim_info = line
            break
    
    # 피해자 정보가 없으면 전체 스토리에서 찾기
    if not victim_info:
        for line in full_story.split("\n"):
            if "피해자" in line and ("이름=" in line or "|이름=" in line):
                victim_info = line
                break
    
    prompt = ChatPromptTemplate.from_template("""
        다음 전체 스토리를 바탕으로 게임 시작을 위한 간략한 사건 개요를 생성해주세요.
        개요는 범인이 누구인지 확실히 드러나지 않도록 중립적으로 작성되어야 합니다.
        
        전체 스토리:
        {full_story}
        
        피해자 정보:
        {victim_info}
        
        다음 형식으로 사건 개요를 작성해주세요:
        
        [사건 제목]: (간단한 제목)
        [사건 배경]: (사건 발생 이전의 상황, 인물들의 관계 등 2-3문장)
        [사건 개요]: (3-4문장으로 상세한 사건 설명)
        [피해자 정보]: (피해자의 정보, 피해 상황 등)
        [용의자 정보]: (용의자의 신상정보, 동기, 알리바이 등)
        [검사 측 증거]:
        1. (검사 측 증거 1과 이 증거가 사건과 어떻게 연결되는지)
        2. (검사 측 증거 2와 이 증거가 사건과 어떻게 연결되는지)
        3. (검사 측 증거 3와 이 증거가 사건과 어떻게 연결되는지)
        [변호사 측 증거]:
        1. (변호사 측 증거 1과 이 증거가 용의자의 무죄를 어떻게 뒷받침하는지)
        2. (변호사 측 증거 2과 이 증거가 용의자의 무죄를 어떻게 뒷받침하는지)
        3. (변호사 측 증거 3와 이 증거가 용의자의 무죄를 어떻게 뒷받침하는지)
        [핵심 쟁점]: (이 사건의 핵심 쟁점 2-3가지)
        
        참고: 피해자가 사망한 경우, 사망 사실을 명확히 기록해 주세요. 피해자와 관련자들의 관계를 명확히 설명해주세요.
    """)
    
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"full_story": full_story, "victim_info": victim_info})

def get_related_characters(full_story):
    """전체 스토리에서 관련자 정보를 추출합니다. 피해자는 제외합니다."""
    llm = get_llm()
    
    # 먼저 피해자 정보 추출
    victim_name = ""
    victim_status = "unknown"
    for line in full_story.split("\n"):
        if line.startswith("[피해자 정보]:"):
            victim_info = line.split(":", 1)[1].strip()
            if "이름=" in victim_info:
                try:
                    name_part = victim_info.split("이름=")[1]
                    victim_name = name_part.split("|")[0] if "|" in name_part else name_part
                except:
                    pass
            if "상태=" in victim_info:
                try:
                    status_part = victim_info.split("상태=")[1]
                    victim_status = status_part.split("|")[0] if "|" in status_part else status_part
                except:
                    pass
            break
            
    # 피해자 정보가 없을 경우 전체 스토리에서 피해자 찾기 시도
    if not victim_name:
        for line in full_story.split("\n"):
            if "피해자" in line and ("이름=" in line or "|이름=" in line):
                try:
                    name_part = line.split("이름=")[1]
                    victim_name = name_part.split("|")[0] if "|" in name_part else name_part
                    if "사망" in line:
                        victim_status = "사망"
                    elif "생존" in line:
                        victim_status = "생존"
                    break
                except:
                    pass
    
    prompt = ChatPromptTemplate.from_template("""
        다음 전체 스토리에서 관련자 정보를 추출해주세요.
        피해자가 이미 확인되었으므로 피해자는 제외하고 다른 관련자만 추출해주세요.
        
        전체 스토리:
        {full_story}
        
        피해자 정보:
        이름: {victim_name}
        상태: {victim_status}
        
        다음 형식으로만 출력해주세요:
        
        관련자1:이름=스토리의관련자1|관계=목격자 또는 기타 관계|배경=...
        관련자2:이름=스토리의관련자2|관계=목격자 또는 기타 관계|배경=...
        
        특히 다음 조건을 반드시 지켜주세요:
        1. 피해자 {victim_name}을(를) 관련자 목록에 포함하지 마세요
        2. 피해자가 사망한 경우, 생존한 다른 인물만 포함해야 합니다
        3. 모든 관련자는 용의자가 아닌 다른 인물이어야 합니다
        4. 각 관련자는 현재 살아있고 증언이 가능한 사람이어야 합니다
        
        다른 설명 없이 위 형식의 응답만 제공해주세요.
        전체 스토리에 있는 실제 관련자 이름을 그대로 사용하세요.
        모든 이름은 성과 이름을 모두 포함해야 합니다.
    """)
    
    chain = prompt | llm | StrOutputParser()
    response = chain.invoke({"full_story": full_story, "victim_name": victim_name, "victim_status": victim_status})
    
    # 텍스트 파싱
    related_characters = []
    try:
        lines = [line.strip() for line in response.split("\n") if line.strip()]
        for line in lines:
            if not line.startswith("관련자") or "|" not in line:
                continue
                
            parts = line.split(":", 1)[1].split("|")
            profile = {"type": "character"}
            
            for part in parts:
                if "=" not in part:
                    continue
                key, value = part.split("=", 1)
                if key == "이름":
                    profile["name"] = value
                elif key == "관계":
                    profile["role"] = value
                elif key == "배경":
                    profile["background"] = value
            
            # 피해자와 같은 이름인 경우 건너뛰기
            if "name" in profile and profile["name"] != victim_name:
                related_characters.append(profile)
    except Exception as e:
        print(f"관련자 추출 오류: {e}")
        # 파싱에 실패한 경우 기본 프로필 사용
        related_characters = [
            {"name": "백도현", "type": "character", "role": "목격자", "background": "현장 근처에서 중요한 정보를 목격한 인물"},
            {"name": "임지은", "type": "character", "role": "관계자", "background": "사건과 관련된 중요 인물"}
        ]
    
    # 피해자와 이름이 같은 경우 다른 이름으로 변경
    for i in range(len(related_characters)):
        if related_characters[i]["name"] == victim_name:
            backup_names = [
                "백도현", "임지은", "손예진", "오현우", "노은서", "진승호", 
                "권나라", "류태민", "장서윤", "홍태경", "송민아", "윤도현"
            ]
            for new_name in backup_names:
                if new_name != victim_name:
                    related_characters[i]["name"] = new_name
                    break
    
    # 프로필이 2개 미만이면 기본 프로필로 보충
    if len(related_characters) < 2:
        default_profiles = [
            {"name": "백도현", "type": "character", "role": "목격자", "background": "현장 근처에서 중요한 정보를 목격한 인물"},
            {"name": "임지은", "type": "character", "role": "관계자", "background": "사건과 관련된 중요 인물"}
        ]
        
        # 피해자와 같은 이름이 있으면 변경
        for profile in default_profiles:
            if profile["name"] == victim_name:
                profile["name"] = "한수민" if victim_name != "한수민" else "박태준"
        
        # 모자란 수만큼 추가
        needed = 2 - len(related_characters)
        for i in range(needed):
            # 이미 있는 이름과 중복되지 않게 추가
            existing_names = [char["name"] for char in related_characters]
            if default_profiles[i]["name"] not in existing_names and default_profiles[i]["name"] != victim_name:
                related_characters.append(default_profiles[i])
    
    return related_characters[:2]  # 최대 2개만 반환

def extract_victim_info(full_story):
    """피해자 정보 추출"""
    victim_name = ""
    victim_status = "unknown"
    victim_desc = ""
    for line in full_story.split("\n"):
        if line.startswith("[피해자 정보]:"):
            victim_info = line.split(":", 1)[1].strip()
            if "이름=" in victim_info:
                try:
                    name_part = victim_info.split("이름=")[1]
                    victim_name = name_part.split("|")[0] if "|" in name_part else name_part.strip()
                except:
                    pass
            if "상태=" in victim_info:
                try:
                    status_part = victim_info.split("상태=")[1]
                    victim_status = status_part.split("|")[0] if "|" in status_part else status_part.strip()
                except:
                    pass
            if "설명=" in victim_info:
                try:
                    desc_part = victim_info.split("설명=")[1]
                    victim_desc = desc_part.split("|")[0] if "|" in desc_part else desc_part.strip()
                except:
                    pass
            break
    
    # 피해자 정보가 없을 경우 검색 시도
    if not victim_name:
        for line in full_story.split("\n"):
            if "피해자" in line and ("이름=" in line or "|이름=" in line):
                try:
                    name_part = line.split("이름=")[1]
                    victim_name = name_part.split("|")[0] if "|" in name_part else name_part.strip()
                    if "사망" in line:
                        victim_status = "사망"
                    elif "생존" in line:
                        victim_status = "생존"
                    break
                except:
                    pass
    
    return {
        "name": victim_name,
        "status": victim_status,
        "desc": victim_desc if victim_desc else "피해자"
    }

def extract_suspect_info(full_story):
    """용의자 정보 추출"""
    suspect_name = ""
    suspect_desc = ""
    for line in full_story.split("\n"):
        if "[용의자 정보]:" in line:
            try:
                # 용의자 정보에서 이름 및 설명 추출
                info_text = line.split(":", 1)[1].strip()
                
                # 이름 추출
                if "이름=" in info_text:
                    name_part = info_text.split("이름=")[1]
                    suspect_name = name_part.split("|")[0] if "|" in name_part else name_part.strip()
                else:
                    # 이름이 명시적으로 없는 경우 첫 단어를 이름으로 가정
                    name_parts = info_text.split()[:2]  # 성과 이름 추출 시도 (성 + 이름)
                    if len(name_parts) >= 1:
                        suspect_name = ' '.join(name_parts[:2]) if len(name_parts) >= 2 else name_parts[0]
                        
                # 설명 추출
                if "설명=" in info_text:
                    desc_part = info_text.split("설명=")[1]
                    suspect_desc = desc_part.split("|")[0] if "|" in desc_part else desc_part.strip()
                else:
                    # 설명이 명시적으로 없는 경우 전체 정보를 설명으로 사용
                    suspect_desc = info_text
                
                break
            except:
                pass
    
    # 용의자 이름을 찾지 못한 경우
    if not suspect_name:
        suspect_name = "용의자"
        suspect_desc = "주요 용의자"
    
    return {
        "name": suspect_name,
        "desc": suspect_desc
    }
