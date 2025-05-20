import json

from dotenv import load_dotenv
load_dotenv()
import time

# 사건 개요 생성을 위한 체인을 반환하는 함수
def build_case_chain():
    class FakeChain:
        def __init__(self):
            self.content = """
[사건 제목]: 피아노 연주회에서의 범죄

[사건 배경]: 피고인은 유명한 피아니스트인 김지훈이며, 피해자는 그의 오랜 친구이자 음악 동료인 이수진이다.  둘은 수년간 함께 연주하며 서로를 지원해왔지만 최근 이수진이 김지훈의 여자친구와 가까워지면서 갈등이 생기기 시작했다.

[사건 개요]: 사건은 대규모 연주회가 열리는 날 밤에 발생했다. 김지훈은 연주를 준비하는 중 이수진과 심한 말다툼을 벌였고, 그 후 이수진이 무대 뒤에서 쓰러진 채 발견된 것이다. 부검 결과 이수진의 사인은 약물 중독으로 밝혀졌으며, 김지훈에게는 사건 발생 시간에 이수진과의 갈등이 있었던 점에서 의심이 제기되고 있다. 김지훈은 범행을 부인하면서도, 이수진의 개인 물품에서 이 약물이 발견된 경위에 대해 불분명한 점이 있다.
"""
        def stream(self, _):
            chunk_size = 10  
            for i in range(0, len(self.content), chunk_size):
                chunk = self.content[i:i + chunk_size]
                time.sleep(0.05)  
                yield chunk

        def invoke(self, _):
            return self.content
        
    return FakeChain()

def build_character_chain(case_summary: str):
    class FakeChain:
        def __init__(self):
            self.content = """ 
피고 : 김지훈
- 직업 : 유명 피아니스트
- 성격 : 자존심이 강하고 열정적인 성격.
- 배경 : 김지훈은 오랜 친구이자 음악 동료인 이수진과의 갈등으로 인해 재판에 출석하게 되었다. 그날 밤, 연주 회 준비 중의 심한 다툼이 사건의 발단이 되었다.

--------------------------------

피해자 : 이수진
- 직업 : 피아니스트
- 성격 : 온화하고 배려가 깊은 성격.
- 배경 : 이수진은 김지훈과 오랜 시간 동안 함께 음악을 해온 친구이자 동료였다. 최근 김지훈의 여자친구와 가까워지면서 그들 사이에 갈등의 씨앗이 생겼다.

--------------------------------

목격자 : 박민수
- 직업 : 연주회 보조 스태프
- 성격 : 소심하지만 관찰력이 뛰어난 성격.
- 배경 : 박민수는 연주회 당일 무대 뒤에서 김지훈과 이수진의 다툼을 목격한 유일한 증인이다. 사건 발생 후, 그는 재판에서 중요한 증언을 하게 되었다.

--------------------------------

참고인 : 정혜린
- 직업 : 음악 기자
- 성격 : 분석적이고 호기심이 많은 성격.
- 배경 : 정혜린은 이수진과 김지훈의 관계를 취재하던 중 사건에 연루되었다. 이수진의 마지막 공연을 다루기 위 해 법정에 출석하게 되었다.

            """
        def stream(self, _):
            chunk_size = 10  
            for i in range(0, len(self.content), chunk_size):
                chunk = self.content[i:i + chunk_size]
                time.sleep(0.05)  
                yield chunk

        def invoke(self, _):
            return self.content
    return FakeChain()

# 사건의 진실(내막) 생성 | 매개 변수 case_summary(str), character(str)
def build_case_behind_chain(case_summary: str, character: str):
    class FakeChain:
        def __init__(self):
            self.content = """
[사건의 진실]:

- 피고 : 유죄
- 범인 : 김지훈

김지훈은 이수진과의 오랜 친구이자 음악 동료로서, 서로의 경력을 지지하며 함께 성장해왔다. 그러나 최근 이수진이 김지훈의 여자친구와 가까워지면서 둘 사이의 갈등이 심화되었고, 결국 연주회 준비 중 심한 말다툼으로 이어졌다. 이 다툼은 단순한 감정의 충돌을 넘어, 김지훈의 자존심과 소유욕을 자극하였다.

김지훈은 이수진과의 갈등으로 인해 극심한 감정적 스트레스를 겪고 있었고, 이수진이 자신의 여자친구와의 관계에 대해 언급하자 분노가 폭발하였다. 사건 당일, 김지훈은 이수진에게 심한 언사를 퍼붓고, 이수진이 무대 뒤에서  쓰러진 후에도 자신의 감정이 통제되지 않았다. 이수진이 쓰러진 이유는 약물 중독으로 밝혀졌지만, 김지훈은 이  약물이 이수진의 개인 물품에서 발견된 경위에 대해 불명확한 설명을 내놓았다.

부검 결과, 이수진의 사인은 특정 약물의 과다 복용으로 확인되었으며, 이 약물은 김지훈이 평소에 사용하던 약물 과 유사한 성분을 가지고 있었다. 김지훈은 이수진의 개인 물품에서 약물이 발견된 것에 대해 알지 못한다고 주장 했지만, 그의 말은 사건의 정황과 맞지 않았다. 특히, 박민수 목격자는 김지훈이 이수진과의 다툼 중 감정적으로  불안정한 상태였음을 증언하였다.

결국, 김지훈은 이수진에게 심한 감정적 상처를 주었고, 그로 인해 이수진이 약물을 복용하게 되는 상황을 초래했 다. 김지훈의 행동은 우연이 아닌, 자신의 자존심과 소유욕에서 비롯된 의도적인 행동으로 볼 수 있으며, 이는 이 수진의 죽음에 직접적인 영향을 미쳤다고 판단된다.

따라서, 김지훈은 유죄로 판단되며, 그의 감정적 갈등과 자존심이 이 사건의 주된 동기임을 알 수 있다.
            """
        def stream(self, _):
            chunk_size = 10 
            for i in range(0, len(self.content), chunk_size):
                chunk = self.content[i:i + chunk_size]
                time.sleep(0.05)  
                yield chunk
        def invoke(self, _):
            return self.content
        
    return FakeChain()

# 테스트 코드 (컨트롤러 호출 예시) 
if __name__ == "__main__":

    def stream_output(chain, initial_string=""):
        """LLM 체인의 출력을 스트리밍하고 결과 텍스트를 반환하는 함수"""
        result = initial_string
        for chunk in chain.stream({}):
            if hasattr(chunk, 'content'):
                print(chunk.content, end='', flush=True)
                result += chunk.content
            else:
                print(chunk, end='', flush=True)
                result += chunk
        return result

    # 1. 사건 개요 생성
    print("사건 개요 생성 중...\n")
    case_summary_chain = build_case_chain()
    case_summary = stream_output(case_summary_chain)

    print('\n\n---------------')  
    
    # 등장인물 추출 테스트
    character_chain = build_character_chain(case_summary)
    character = stream_output(character_chain)
    
    
    print('\n\n---------------')
    # 사건의 진실 생성
    print("사건의 진실 생성 중...\n")

    case_truth_chain = build_case_behind_chain(case_summary, character)
    case_truth = stream_output(case_truth_chain)

    