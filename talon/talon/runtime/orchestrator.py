"""Orchestrator — ReAct with verification"""
import hashlib
import json
from .taint_graph import TaintGraph
from .guardrails import Guardrail
from .token_budget import TokenBucket
from ..tools.registry import ToolRegistry

class Orchestrator:
    def __init__(self, memory, policy_engine):
        self.memory = memory
        self.policy = policy_engine
        self.guard = Guardrail()
        self.budget = TokenBucket()
        self.tools = ToolRegistry()

    async def run(
        self,
        message: str,
        identity,
        channel: str,
        client_ip: str,
        requested_tool: str | None = None,
        requested_args: dict | None = None,
    ):
        taint = TaintGraph()
        # 1. Taint incoming message
        node = taint.add_content(message, source=f"{channel}:untrusted_user", trust=0.0)
        # 2. Guardrail scan
        scan = self.guard.scan(message)
        if scan["blocked"]:
            return {"error":"blocked_by_guardrail","hits":scan["hits"],"taint":node.id}

        # 3. Token budget check
        est = self.budget.estimate(message)
        if not self.budget.consume(est):
            return {"error":"token_budget_exhausted","remaining":self.budget.remaining}

        # 4. Check cache.  Use a stable, identity-scoped digest instead of
        # Python's process-randomized hash() and never share results cross-user.
        cache_key = hashlib.sha256(
            json.dumps(
                {
                    "identity": identity.spiffe_id,
                    "channel": channel,
                    "message": message,
                    "tool": requested_tool,
                    "args": requested_args or {},
                },
                sort_keys=True,
                default=str,
            ).encode()
        ).hexdigest()
        cached = self.budget.get_cached(cache_key)
        if cached:
            return {"cached":True, **cached}

        # 5. Plan (in prod: LLM call with taint-rendered prompt)
        rendered = taint.render_for_llm(message, node)
        # Simulated planning — in prod calls Claude/LLM with structured output
        plan = self._mock_plan(message, identity, requested_tool, requested_args or {})

        # 6. Verification + policy + execution
        results = []
        for step in plan:
            tool = step["tool"]
            args = step["args"]
            if not self.policy.evaluate(identity, tool, args):
                results.append({"tool":tool,"error":"policy_denied"})
                continue
            # Execute in sandbox
            out = await self.tools.execute(tool, args, identity)
            results.append(out)

        final = {
            "message": message,
            "plan": plan,
            "results": results,
            "taint_graph": len(taint.nodes),
            "identity": identity.spiffe_id,
            "taint_type": "DATA",
        }
        self.budget.set_cached(cache_key, final)
        # 7. Episodic memory append (encrypted)
        await self.memory.append_episodic(final)
        return final

    def _mock_plan(self, msg: str, ident, requested_tool: str | None = None, requested_args: dict | None = None):
        if requested_tool:
            return [{"tool": requested_tool, "args": dict(requested_args or {})}]
        msg_l = msg.lower()
        if "read" in msg_l or "file" in msg_l:
            return [{"tool":"file_read","args":{"path":"/workspace/README.md"}}]
        if "search" in msg_l:
            return [{"tool":"web_search","args":{"query":msg[:100]}}]
        return [{"tool":"web_search","args":{"query":msg[:80]}}]
