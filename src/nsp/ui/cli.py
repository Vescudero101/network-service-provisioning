"""The plain command-line UI: the only place (besides the TUI) that prints or asks."""


def report(phase, message):
    print(f"[{phase}] {message}")


def ask_confirm():
    # The plan was already printed by the PLAN phase, so only ask here
    answer = input("Push this change? (yes/no): ")
    return answer.strip().lower() == "yes"
