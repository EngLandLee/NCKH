import json
import os
from typing import Dict, Any, List

class RufloAgentMemory:
    """Bridge for cross-session AgentDB and learning memory."""
    def __init__(self, storage_path: str = "data/agentdb_memory.json"):
        self.storage_path = storage_path
        os.makedirs(os.path.dirname(storage_path), exist_ok=True)
        self.memory = self._load()

    def _load(self) -> Dict[str, Any]:
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {"learned_rules": {}, "execution_logs": []}
        return {"learned_rules": {}, "execution_logs": []}

    def record_decision(self, task_type: str, input_summary: str, decision: str, confidence: float):
        log_entry = {
            "task_type": task_type,
            "input": input_summary[:200],
            "decision": decision,
            "confidence": confidence
        }
        self.memory["execution_logs"].append(log_entry)
        if len(self.memory["execution_logs"]) > 1000:
            self.memory["execution_logs"] = self.memory["execution_logs"][-1000:]
        self._save()

    def _save(self):
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(self.memory, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
