"""
main.py — Interactive CLI Application for Member 2 AI Agent
"""

import sys
from agent import run_agent


def main():
    print("=======================================================")
    print("  SIH117 -- Member 2: AI Engineering Assistant CLI")
    print("  Type 'exit', 'quit', or 'q' to end the session.")
    print("=======================================================\n")

    history = []

    while True:
        try:
            user_input = input("You: ").strip()
            if not user_input:
                continue

            if user_input.lower() in ("exit", "quit", "q"):
                print("\nEnding session. Goodbye!")
                break

            response = run_agent(user_input, conversation_history=history)

            print(f"\nAI ({response.status}): {response.answer}\n")
            if response.sources:
                print(f"Sources: {', '.join(response.sources)}\n")

            # Update history for next multi-turn prompt
            history.append({"role": "user", "content": user_input})
            history.append({"role": "assistant", "content": response.answer})
            # Bound history to last 10 messages
            if len(history) > 10:
                history = history[-10:]

        except KeyboardInterrupt:
            print("\nSession interrupted. Goodbye!")
            sys.exit(0)
        except Exception as e:
            print(f"\nError: {e}\n")


if __name__ == "__main__":
    main()
