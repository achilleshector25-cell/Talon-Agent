"""Explicit command parsing for the Telegram connector."""


def parse_tool_request(text: str) -> tuple[str | None, dict]:
    """Parse Telegram tool commands without guessing user intent."""
    parts = text.split(maxsplit=1)
    if not parts or parts[0].lower() != "/shell":
        return None, {}
    return "shell", {"cmd": parts[1].strip() if len(parts) == 2 else ""}