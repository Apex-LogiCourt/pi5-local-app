from data_models import CaseData, Case, Profile, Evidence
from typing import Dict, List, Optional


def handler_send_initial_evidence(evidences : List[Evidence]) -> None:
    """초기 증거 데이터를 WebSocket을 통해 전송하는 함수"""
    from api.manager import sse_manager
    import asyncio
    from dataclasses import asdict
    
    for e in evidences:
        evidence_dict = asdict(e)
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



def handler_record_start() -> None :
    """녹음 시작 명령을 WebSocket을 통해 전송하는 함수"""
    from api.manager import websocket_manager
    import asyncio
    print("[handler_record_start] 녹음 시작 명령 전송")
    asyncio.create_task(websocket_manager.send_record_start())

def handler_record_stop() -> None :
    """녹음 종료 명령을 WebSocket을 통해 전송하는 함수"""
    from api.manager import websocket_manager
    import asyncio
    asyncio.create_task(websocket_manager.send_record_stop())

    
def handler_question(question: str, profile : Profile) :
    from interrogation.interrogator import it
    chain = it.build_ask_chain(question, profile)
    pass    