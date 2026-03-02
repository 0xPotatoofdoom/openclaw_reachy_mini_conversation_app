import logging
import subprocess
from typing import Any, Dict

from reachy_mini_conversation_app.tools.core_tools import Tool, ToolDependencies

logger = logging.getLogger(__name__)


class RunShell(Tool):
    """Run a shell command or Python snippet and return the output."""

    name = "run_shell"
    description = (
        "Run a shell command on the robot and return stdout/stderr. "
        "Use this to verify facts, run Python snippets, check system state, or test code. "
        "Keep commands safe and non-destructive."
    )
    parameters_schema = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "Shell command to run. For Python, use: python3 -c 'your code here'",
            },
            "timeout": {
                "type": "integer",
                "description": "Timeout in seconds (default 10, max 30).",
            },
        },
        "required": ["command"],
    }

    async def __call__(self, deps: ToolDependencies, **kwargs: Any) -> Dict[str, Any]:
        command = kwargs.get("command", "")
        timeout = min(int(kwargs.get("timeout", 10)), 30)

        logger.info("Tool call: run_shell command=%r timeout=%d", command, timeout)

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            output = result.stdout.strip()
            err = result.stderr.strip()
            return {
                "returncode": result.returncode,
                "stdout": output[:2000] if output else "",
                "stderr": err[:500] if err else "",
            }
        except subprocess.TimeoutExpired:
            return {"error": f"Command timed out after {timeout}s"}
        except Exception as e:
            return {"error": str(e)}
