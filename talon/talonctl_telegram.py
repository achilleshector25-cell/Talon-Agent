
import os, asyncio
from talon.connectors.telegram_live import run_telegram_bot

if __name__ == "__main__":
    print("TALON Telegram Bridge — secure wiring")
    print("Owner-only shell, taint graph active, policy default-deny")
    asyncio.run(run_telegram_bot())
