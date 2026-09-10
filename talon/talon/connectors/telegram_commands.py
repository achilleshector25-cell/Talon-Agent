"""Explicit command parsing for the Telegram connector."""


def parse_tool_request(text: str) -> tuple[str | None, dict]:
    """Parse Telegram tool commands without guessing user intent."""
    parts = text.split(maxsplit=1)
    if not parts:
        return None, {}
    command = parts[0].split("@", 1)[0].lower()
    if command != "/shell":
        return None, {}
    return "shell", {"cmd": parts[1].strip() if len(parts) == 2 else ""}