"""Workspace management: run state persistence and interaction logging."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class RunState:
    run_id: str
    workspace_path: Path
    current_stage: int
    mode: str
    stage_status: dict[int, str]  # {1: "completed", 2: "in_progress", ...}
    retry_counts: dict[int, int]
    requirements_file: str
    config_snapshot: dict
    rollback_guidance: str | None = None  # Mentor guidance for spec rewrite on rollback

    def save(self) -> None:
        data = asdict(self)
        data["workspace_path"] = str(self.workspace_path)
        path = self.workspace_path / "run_state.json"
        path.write_text(json.dumps(data, indent=2))

    @classmethod
    def load(cls, workspace_path: Path) -> RunState:
        data = json.loads((workspace_path / "run_state.json").read_text())
        data["workspace_path"] = Path(data["workspace_path"])
        # JSON keys are strings; convert to int
        data["stage_status"] = {int(k): v for k, v in data["stage_status"].items()}
        data["retry_counts"] = {int(k): v for k, v in data["retry_counts"].items()}
        # Backward compatibility: optional fields added after v0.1.0
        data.setdefault("rollback_guidance", None)
        return cls(**data)

    @classmethod
    def create(
        cls,
        workspace_root: Path,
        requirements_file: Path,
        mode: str,
        config_snapshot: dict | None = None,
    ) -> RunState:
        run_id = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")
        workspace_path = workspace_root / run_id
        workspace_path.mkdir(parents=True, exist_ok=True)

        state = cls(
            run_id=run_id,
            workspace_path=workspace_path,
            current_stage=1,
            mode=mode,
            stage_status={i: "pending" for i in range(1, 6)},
            retry_counts={i: 0 for i in range(1, 6)},
            requirements_file=str(requirements_file),
            config_snapshot=config_snapshot or {},
        )
        state.save()
        return state


class InteractionLog:
    """Append-only JSONL log of all events in a run."""

    def __init__(self, workspace_path: Path):
        self.log_path = workspace_path / "interaction_log.jsonl"

    def _append(self, event: dict) -> None:
        event["ts"] = datetime.now(timezone.utc).isoformat()
        with open(self.log_path, "a") as f:
            f.write(json.dumps(event) + "\n")

    def log_llm_request(self, stage: int, attempt: int, messages: list[dict]) -> None:
        self._append({
            "event": "llm_request",
            "stage": stage,
            "attempt": attempt,
            "message_count": len(messages),
        })

    def log_llm_response(
        self, stage: int, attempt: int, content: str, usage: dict
    ) -> None:
        self._append({
            "event": "llm_response",
            "stage": stage,
            "attempt": attempt,
            "content_length": len(content),
            "usage": usage,
        })

    def log_tool(
        self, stage: int, command: str, exit_code: int, stdout: str, stderr: str
    ) -> None:
        self._append({
            "event": "tool_invocation",
            "stage": stage,
            "command": command,
            "exit_code": exit_code,
            "stdout_length": len(stdout),
            "stderr_length": len(stderr),
        })

    def log_user_decision(self, stage: int, decision: str) -> None:
        self._append({
            "event": "user_decision",
            "stage": stage,
            "decision": decision,
        })

    def log_stage_complete(self, stage: int, outcome: str, output_file: str | None) -> None:
        self._append({
            "event": "stage_complete",
            "stage": stage,
            "outcome": outcome,
            "output_file": output_file,
        })
