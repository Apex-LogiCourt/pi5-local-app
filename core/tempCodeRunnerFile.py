if __name__ == "__main__":
    # asyncio.run(CaseDataManager.initialize())  # 비동기 호출
    # asyncio.run(CaseDataManager.generate_case_stream())  # 비동기 호출
    # asyncio.run(CaseDataManager.generate_profiles_stream())  # 비동기 호출  
    # asyncio.run(CaseDataManager.generate_evidences())  # 비동기 호출
    # print(CaseDataManager.get_case_data())

    # 케이스 빌더의 더미체인 활용 테스트 코드
    from case_generation.case_builder import build_case_chain, build_character_chain, build_case_behind_chain
    
    # 1. 사건 개요 생성
    print("===== 사건 개요 생성 =====")
    case_chain = build_case_chain()
    case_result = ""
    for chunk in case_chain.stream({}):
        case_result += chunk
    print(case_result)
    print("\n" + "="*50 + "\n")
    
    # 2. 등장인물 생성
    print("===== 등장인물 생성 =====")
    character_chain = build_character_chain(case_result)
    character_result = ""
    for chunk in character_chain.stream({}):
        character_result += chunk
    print(character_result)
    print("\n" + "="*50 + "\n")
    
    # 3. 파싱 테스트
    print("===== 파싱 결과 =====")
    profiles = CaseDataManager._parse_character_template(character_result)
    
    # 파싱된 프로필 정보 출력
    for profile in profiles:
        print(f"이름: {profile.name}")
        print(f"유형: {profile.type}")
        print(f"성별: {profile.gender}")
        print(f"나이: {profile.age}")
        print(f"성격: {profile.personality}")
        print(f"배경: {profile.context}")
        print(f"음성: {profile.voice}")
        print("-" * 40)
    
    # 4. 사건의 진실 생성
    print("===== 사건의 진실 =====")
    behind_chain = build_case_behind_chain(case_result, character_result)
    behind_result = ""
    for chunk in behind_chain.stream({}):
        behind_result += chunk
    print(behind_result)