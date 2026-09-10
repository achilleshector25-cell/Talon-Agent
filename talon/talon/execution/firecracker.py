"""Execution boundary.

The production implementation must call a Firecracker/gVisor service. Host
execution is disabled by default. When explicitly enabled for development,
commands run through a real host shell as the Replit workspace user.
"""
import asyncio
import os
import signal

class FirecrackerExecutor:
    def __init__(self, allow_host_execution: bool | None = None):
        self.allow_host_execution = (
            os.getenv("TALON_ALLOW_HOST_EXECUTION") == "1"
            if allow_host_execution is None
            else allow_host_execution
        )

    async def run(self, cmd: str, network: str = "none", timeout: int = 10) -> dict:
        if not self.allow_host_execution:
            return {"error": "host_execution_disabled", "vm": "unavailable"}
        if network != "none":
            return {"error": "network_access_denied", "vm": "host-exec"}
        if not isinstance(cmd, str) or not cmd.strip() or len(cmd) > 2_000:
            return {"error": "invalid_command", "vm": "host-exec"}
        env = {"PATH": "/usr/bin:/bin", "LANG": "C", "HOME": "/tmp"}
        proc = await asyncio.create_subprocess_shell(
            cmd,
            executable="/bin/bash",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=os.getenv("TALON_HOST_CWD", os.getcwd()),
            env=env,
            start_new_session=True,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=min(timeout, 30))
            return {
                "exit_code": proc.returncode,
                "stdout": stdout.decode(errors="replace")[:5000],
                "stderr": stderr.decode(errors="replace")[:2000],
                "vm": "host-exec-dev-only",
            }
        except asyncio.TimeoutError:
            os.killpg(proc.pid, signal.SIGKILL)
            await proc.wait()
            return {"error": "timeout", "vm": "host-exec-dev-only"}
