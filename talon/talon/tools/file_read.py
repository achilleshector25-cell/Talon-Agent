from pathlib import Path
import os

class Tool:
    name="file_read"
    async def run(self, args, identity, executor=None):
        path = args.get("path", "")
        if not isinstance(path, str) or not path:
            return {"error":"path required"}
        roots = [
            Path(item.strip()).expanduser().resolve()
            for item in os.getenv("TALON_FILE_ROOTS", "/workspace,/mnt/data/talon").split(",")
            if item.strip()
        ]
        try:
            p = Path(path).expanduser()
            if p.is_symlink():
                return {"error":"symbolic links are not allowed"}
            resolved = p.resolve(strict=True)
            if not any(resolved == root or root in resolved.parents for root in roots):
                return {"error":"path denied"}
            if not resolved.is_file():
                return {"error":"path is not a regular file"}
            if resolved.stat().st_size > 5 * 1024 * 1024:
                return {"error":"file too large"}
            content = resolved.read_text(encoding="utf-8", errors="replace")[:2000]
            return {"tool":"file_read","path":str(resolved),"content":content}
        except (FileNotFoundError, PermissionError, OSError, RuntimeError):
            return {"error":"file unavailable"}
