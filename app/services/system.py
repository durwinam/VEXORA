import shutil, subprocess
from dataclasses import dataclass

@dataclass
class CommandResult:
    returncode: int
    stdout: str
    stderr: str

def command_exists(name: str) -> bool:
    return shutil.which(name) is not None

def run(command: list[str], timeout: int = 120) -> CommandResult:
    p = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    return CommandResult(p.returncode, p.stdout, p.stderr)
