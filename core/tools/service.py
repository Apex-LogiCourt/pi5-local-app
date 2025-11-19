from data_models import CaseData, Case, Profile, Evidence
from typing import Dict, List, Optional


def handler_send_initial_evidence(evidences : List[Evidence]) -> None:
    """초기 증거 데이터를 WebSocket을 통해 전송하는 함수"""
    from api.manager import sse_manager
    import asyncio
    from dataclasses import asdict
    
    for e in evidences:
        evidence_dict = asdict(e)
        # picture가 None이면 loading.png 경로로 설정
        if evidence_dict.get("picture") is None:
            evidence_dict["picture"] = "data/evidence_resource/loading.png"
        asyncio.create_task(sse_manager.add_evidence(evidence_dict))

def handler_send_updated_evidence(evidence: Evidence) -> None:
    """증거 업데이트 시 WebSocket을 통해 전송하는 함수"""
    from api.manager import sse_manager
    import asyncio
    from dataclasses import asdict
    
    evidence_dict = asdict(evidence)
    payload = {
        "id": evidence_dict.get("id"),
        "description": evidence_dict.get("description"),
    }

    asyncio.create_task(sse_manager.broadcast("evidence_update", payload))



#============================================
# 웹 소켓 사용하는 함수 
#============================================

async def handler_tts_service(text: str, voice: str = "nraewon"):
    from api.manager import websocket_manager
    await websocket_manager.send_tts_request(text, voice)

async def handler_record_start():
    from api.manager import websocket_manager
    await websocket_manager.send_record_start()  

async def handler_record_stop():
    from api.manager import websocket_manager
    await websocket_manager.send_record_stop()  


#============================================

    
def handler_question(question: str, profile : Profile) :
    from interrogation.interrogator import it
    chain = it.build_ask_chain(question, profile)
    pass    



#============================================

# def run_chain_streaming(chain):
#     stream = chain.stream({})
    
#     def on_sentence_ready(sentence):
#         print(f"[문장 수신] {sentence}")
    
#     sentence_streamer(stream, on_sentence_ready)


def run_chain_invoke(chain, as_markdown=False):
    """
    chain.invoke({})를 호출해서 결과를 문자열로 반환하는 함수.
    
    Args:
        chain: LangChain chain 객체
        as_markdown: True이면 마크다운을 HTML로 변환해서 반환
    """
    result = chain.invoke({})
    # LangChain 최신 base_chain은 invoke가 반환 값을 직접 리턴함 (대개 str 또는 dict)
    # 만약 dict처럼 나오면 str로 변환
    if not isinstance(result, str):
        result = str(result)
    
    # 마크다운을 HTML로 변환
    if as_markdown:
        result = markdown_to_html(result)
    
    return result


def markdown_to_html(markdown_text: str) -> str:
    """
    마크다운 텍스트를 HTML로 변환
    QTextEdit에서 볼드, 이탤릭, 줄바꿈 등 서식이 적용되도록 처리
    """
    try:
        import markdown
        # nl2br: 줄바꿈을 <br>로 변환
        # extra: 표, 펜스 코드블록 등 확장 기능
        # sane_lists: 리스트 처리 개선
        html = markdown.markdown(
            markdown_text,
            extensions=['nl2br', 'extra', 'sane_lists']
        )
        return html
    except ImportError:
        print("[WARNING] markdown 라이브러리가 없습니다. pip install markdown")
        return markdown_text



async def run_chain_streaming(chain, callback=None):
    full_text = ""
    # chain이 문자열인 경우 run_str_streaming 사용
    if isinstance(chain, str):
        run_str_streaming(chain, callback)
        return
    
    # chain이 None인 경우 처리
    if chain is None:
        print("[WARNING] Chain is None, skipping")
        return
    
    try:
        stream = chain.stream({})
        
        def on_sentence_ready(sentence):
            nonlocal full_text
            full_text += sentence
            if callback:
                callback(sentence)
            return sentence
        
        sentence_streamer(stream, on_sentence_ready)
        return full_text.strip()  # 전체 텍스트 반환

    except Exception as e:
        print(f"[ERROR] Failed to stream chain: {e}")
        if callback:
            callback(f"스트리밍 중 오류가 발생했습니다: {str(e)}")


def run_str_streaming(text: str, callback=None):
    def text_generator():
        yield str(text)  # ensure always yields string

    def on_sentence_ready(sentence):
        if callback:
            callback(sentence)
    
    sentence_streamer(text_generator(), on_sentence_ready)

import re
from typing import AsyncGenerator, Callable

def sentence_streamer(
    stream: AsyncGenerator[str, None],
    callback: Callable[[str], None],
    sentence_endings: str = r"[.!?。！？]"
):
    """
    chain.stream() 결과를 문장 단위로 쪼개어 callback에 전달하는 스트리밍 헬퍼.

    Args:
        stream: AsyncGenerator yielding string chunks
        callback: 문장이 완성될 때마다 호출될 콜백 함수
        sentence_endings: 종결 문자 정규표현식
    """
    buffer = ""

    for chunk in stream:
        content = getattr(chunk, "content", chunk)
        buffer += content

        # 문장 끝 기준으로 분리
        sentences = re.split(f"({sentence_endings})", buffer)

        # 짝수 인덱스는 문장 앞부분, 홀수는 종결문자
        complete_sentences = []
        temp = ""
        for i, part in enumerate(sentences):
            temp += part
            if i % 2 == 1:  # 종결자 포함 시점
                complete_sentences.append(temp.strip())
                temp = ""

        # 아직 끝나지 않은 문장은 버퍼에 다시 저장
        buffer = temp

        # 콜백 호출
        for sent in complete_sentences:
            if sent:
                callback(sent)

    # 스트림 종료 시 버퍼가 남아있다면 보냄
    if buffer.strip():
        callback(buffer.strip())



    
#=============================================
# post 요청에 대한 핸들러
#=============================================
def handler_tagged_evidence(id: int) -> None:
    """
    게임 컨트롤러의 `tagged_evidence`를 업데이트하고 signal을 보냄
    """
    from game_controller import GameController
    gc = GameController.get_instance()
    for evidence in gc._case_data.evidences:
        if evidence.id == id:
            gc._state.tagged_evidence = evidence
            gc._send_signal("evidence_tagged", evidence)
            return
