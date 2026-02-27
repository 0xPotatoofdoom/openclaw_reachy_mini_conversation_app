import logging
import subprocess
from pathlib import Path
from typing import Any, Dict

from reachy_mini_conversation_app.tools.core_tools import Tool, ToolDependencies

logger = logging.getLogger(__name__)


class GitStatus(Tool):
    """Check git status and recent commits for a repo."""

    name = "git_status"
    description = (
        "Check the git status and recent commits of a repository. "
        "Use this to stay aware of what Matt is working on and what's changed."
    )
    parameters_schema = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the git repo (default: /home/pollen)",
            },
            "log_count": {
                "type": "integer",
                "description": "Number of recent commits to show (default 5).",
            },
        },
        "required": [],
    }

    async def __call__(self, deps: ToolDependencies, **kwargs: Any) -> Dict[str, Any]:
        repo_path = kwargs.get("path", "/home/pollen")
        log_count = min(int(kwargs.get("log_count", 5)), 20)
        path = Path(repo_path).expanduser().resolve()

        logger.info("Tool call: git_status path=%s", path)

        def run(cmd: str) -> str:
            try:
                r = subprocess.run(
                    cmd, shell=True, capture_output=True, text=True,
                    timeout=10, cwd=str(path)
                )
                return r.stdout.strip() or r.stderr.strip()
            except Exception as e:
                return str(e)

        status = run("git status --short")
        branch = run("git rev-parse --abbrev-ref HEAD")
        log = run(f"git log --oneline -{log_count}")
        diff_stat = run("git diff --stat HEAD")

        return {
            "branch": branch,
            "status": status or "clean",
            "recent_commits": log,
            "diff_stat": diff_stat or "no uncommitted changes",
        }
