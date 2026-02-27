import logging
from pathlib import Path
from typing import Any, Dict

from reachy_mini_conversation_app.tools.core_tools import Tool, ToolDependencies

logger = logging.getLogger(__name__)

ALLOWED_ROOTS = ["/home/pollen", "/venvs/src"]


class ReadFile(Tool):
    """Read a file from the filesystem."""

    name = "read_file"
    description = (
        "Read a file from the robot's filesystem. Use this to look at code Matt is working on, "
        "config files, logs, etc. Returns the file contents (truncated if large)."
    )
    parameters_schema = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Absolute or home-relative path to the file (e.g. ~/project/main.py)",
            },
            "lines": {
                "type": "integer",
                "description": "Max number of lines to return (default 100).",
            },
        },
        "required": ["path"],
    }

    async def __call__(self, deps: ToolDependencies, **kwargs: Any) -> Dict[str, Any]:
        raw_path = kwargs.get("path", "")
        max_lines = min(int(kwargs.get("lines", 100)), 500)

        path = Path(raw_path).expanduser().resolve()
        logger.info("Tool call: read_file path=%s", path)

        # Safety: only allow reads from permitted roots
        if not any(str(path).startswith(root) for root in ALLOWED_ROOTS):
            return {"error": f"Path not allowed. Must be under: {ALLOWED_ROOTS}"}

        if not path.exists():
            return {"error": f"File not found: {path}"}
        if not path.is_file():
            return {"error": f"Not a file: {path}"}

        try:
            text = path.read_text(errors="replace")
            lines = text.splitlines()
            truncated = len(lines) > max_lines
            content = "\n".join(lines[:max_lines])
            return {
                "path": str(path),
                "lines_returned": min(len(lines), max_lines),
                "total_lines": len(lines),
                "truncated": truncated,
                "content": content,
            }
        except Exception as e:
            return {"error": str(e)}
