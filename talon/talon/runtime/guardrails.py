"""Multilingual injection classifier — replaces English-only regex"""
import re

# Fallback regex + heuristic multilingual (in prod: DeBERTa model)
PATTERNS = [
    r"ignore.*previous.*instructions",
    r"you are now.*unrestricted",
    r"ne plus suivre", r"ignorer les instructions",  # fr
    r"忽略.*指令", r"无视.*提示",  # zh
    r"игнорируй.*инструкции",  # ru
]

class Guardrail:
    def __init__(self):
        self.re = [re.compile(p, re.I) for p in PATTERNS]

    def scan(self, text: str) -> dict:
        score = 0
        hits = []
        for rx in self.re:
            if rx.search(text):
                hits.append(rx.pattern)
                score+=0.8
        # Heuristic: instruction-like imperative in untrusted block
        if "SYSTEM:" in text.upper() and "DATA" in text.upper():
            score+=0.5
        return {"score": min(1.0, score), "hits": hits, "blocked": score>=0.8}
