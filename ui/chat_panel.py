#chainlit run ui/chat_panel.py 으로 실행테스트
import chainlit as cl

case_summary = """
### 파이널로 생성된 사건 개요

[사건 제목]: 도심 오피스 괴한 치명 사건

[사건 배경]:
서울 강남의 한 대형 IT 기업 부산에서 야간 관리자가 고도 사무실에서 당황한 사건이 발생했습니다. 피해자는 심각한 발생을 계단하여 보통용용을 받았고, 용의자는 전 연인으로 지르어진 된 사인이었습니다.

[사건 개요]:
지난 그림 금요일 달리 간 사건이 발생했고, 피해자는 그 시간에 자녀 중 가편에 당황 받았습니다. CCTV에는 어느 인물이 등장한 기록이 보여 용의자가 유력한 효율성을 가지고 있다고 나열하고 있습니다.

[용의자 정보]:
박정우, 남성, 32세, 프리랜서 개발자. 피해자의 전 연인으로, 최근 이발 후 개인적인 가령과 감염이 있었다는 정보가 드디는 것으로 확인되었습니다.
"""

witness_profiles = [
    {"name": "이지은", "type": "character", "background": "피해자"},
    {"name": "최민석", "type": "character", "background": "목격자, 같은 건물에서 야근 중이었음"},
    {"name": "이정수 박사", "type": "expert", "background": "법의학자, 피해자의 부상 상태 분석"}
]

turn_order = ["검사", "변호사"]

@cl.on_chat_start
async def start():
    cl.user_session.set("turn", "검사")
    cl.user_session.set("done_flags", {"검사": False, "변호사": False})
    await cl.Message(content=case_summary, author="system").send()
    await show_witness_buttons()

async def show_witness_buttons():
    witness_md = "\n".join([f"**👤 {w['name']}** ({w['type']}) - {w['background']}" for w in witness_profiles])
    await cl.Message(
        content=f"### 👥 참고인 목록\n{witness_md}", author="system"
    ).send()

    actions = [
        cl.Action(
            name=w["name"],
            label=f"{w['name']} 심문하기",
            type="button",
            payload={"name": w["name"]}
        )
        for w in witness_profiles
    ]
    await cl.Message(content="👥 참고인 중 누구를 심문하시겠습니까?", actions=actions).send()

@cl.action_callback("이지은")
async def on_lee_clicked(action):
    cl.user_session.set("selected_witness", action.name)
    await cl.Message(content=f"{action.name} 참고인을 선택하셨습니다. 질문을 입력해주세요.").send()

@cl.action_callback("최민석")
async def on_choi_clicked(action):
    cl.user_session.set("selected_witness", action.name)
    await cl.Message(content=f"{action.name} 참고인을 선택하셨습니다. 질문을 입력해주세요.").send()

@cl.action_callback("이정수 박사")
async def on_dr_lee_clicked(action):
    cl.user_session.set("selected_witness", action.name)
    await cl.Message(content=f"{action.name} 참고인을 선택하셨습니다. 질문을 입력해주세요.").send()

@cl.on_message
async def handle_message(msg: cl.Message):
    selected = cl.user_session.get("selected_witness")
    turn = cl.user_session.get("turn")
    done_flags = cl.user_session.get("done_flags")

    if selected:
        await cl.Message(
            content=f"[검사] {selected}에게 질문: {msg.content}", author=turn.lower()
        ).send()

        await cl.Message(
            content=f"[답변] {selected}의 답변입니다. (여기에는 추후 AI 답변이 들어갑니다)",
            author=selected
        ).send()

        cl.user_session.set("selected_witness", None)
        await show_witness_buttons()
    else:
        await cl.Message(
            content=f"[{turn}] {msg.content}", author=turn.lower()
        ).send()

        if msg.content.strip() == "이상입니다":
            done_flags[turn] = True
            cl.user_session.set("done_flags", done_flags)

            if all(done_flags.values()):
                await cl.Message(
                    content="📜 모든 발언이 완료되었습니다. AI 판사의 판결이 시작됩니다...",
                    author="system"
                ).send()
                await cl.Message(
                    content="⚖️ AI 판사: 본 사건에 대해 양측의 주장을 고려한 결과, 피고인은 무죄입니다. (더미 데이터)",
                    author="판사"
                ).send()
                return

        # 다음 턴으로 전환
        next_turn = "변호사" if turn == "검사" else "검사"
        cl.user_session.set("turn", next_turn)
        await cl.Message(
            content=f"🌀 {next_turn}의 차례입니다.",
            author="system"
        ).send()
        await show_witness_buttons()