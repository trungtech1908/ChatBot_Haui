"""CLI — đăng nhập trước, mọi truy vấn/Zep gắn với sinh viên đó."""

import argparse

from dotenv import load_dotenv

load_dotenv()


def main() -> None:
    parser = argparse.ArgumentParser(description="Chatbot quy chế sinh viên HaUI (Agentic RAG)")
    parser.add_argument("query", nargs="?", help="Một câu hỏi (bỏ trống = chat liên tục)")
    parser.add_argument(
        "--ma-sv",
        help="Chỉ dev/test: bỏ đăng nhập (production phải login)",
    )
    args = parser.parse_args()

    from chatbot_haui.agent.graph import run_agent
    from chatbot_haui.auth import StudentSession, login_interactive

    if args.ma_sv:
        session = StudentSession(ma_sv=args.ma_sv.strip())
        print(f"(dev) maSV={session.ma_sv}\n")
    else:
        session = login_interactive()

    if args.query:
        result = run_agent(args.query, session=session)
        print(result.get("answer", ""))
        return

    label = session.ho_ten or session.ma_sv
    print(f"Chatbot HaUI | {label} | maSV={session.ma_sv}")
    print("Gõ 'exit' để thoát.\n")
    while True:
        try:
            q = input("Bạn: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not q or q.lower() in ("exit", "quit"):
            break
        result = run_agent(q, session=session)
        print(f"\nBot: {result.get('answer', '')}\n")
