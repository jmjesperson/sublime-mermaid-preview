"""Find and run mmdc (mermaid-cli) to render a PNG, never touching the target on failure."""

import os
import shutil
import stat
import subprocess
import tempfile
from dataclasses import dataclass
from typing import Callable

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
SYSTEM_DIRS = ("/opt/homebrew/bin", "/usr/local/bin")
MISE_SHIMS = os.path.join(".local", "share", "mise", "shims")


def _is_executable_file(path: str) -> bool:
    return os.path.isfile(path) and os.access(path, os.X_OK)


def find_mmdc(
    setting_path: str,
    which: Callable[[str], str | None] = shutil.which,
    home: str = os.path.expanduser("~"),
    system_dirs: tuple[str, ...] = SYSTEM_DIRS,
) -> tuple[str | None, str]:
    """Return (path, how_found). A set mmdc_path is used as-is, with no fallback search."""
    if setting_path:
        path = os.path.expanduser(setting_path)
        if _is_executable_file(path):
            return path, "mmdc_path setting"
        return None, "mmdc_path setting: {} is not an executable file".format(path)

    found = which("mmdc")
    if found:
        return found, "PATH"
    candidates = [os.path.join(d, "mmdc") for d in system_dirs]
    candidates.append(os.path.join(home, MISE_SHIMS, "mmdc"))
    for candidate in candidates:
        if _is_executable_file(candidate):
            return candidate, candidate
    return None, "mmdc not found on PATH or in " + ", ".join(candidates)


def build_mmdc_command(mmdc: str, scale: int, background: str, config_path: str) -> list[str]:
    """mmdc reading the source on stdin and writing the PNG to stdout."""
    return [mmdc, "-i", "-", "-o", "-", "-e", "png", "-s", str(scale), "-b", background,
            "-c", config_path, "-q"]


def build_env(base_env: dict[str, str], mmdc: str, node_path: str) -> dict[str, str]:
    """Copy of base_env with node_path (if set), then mmdc's directory, at the front of PATH.

    mmdc starts with `#!/usr/bin/env node`, so node must be findable on PATH. Sublime launched
    from the Dock doesn't inherit the shell's PATH.
    """
    env = dict(base_env)
    front = [p for p in (node_path, os.path.dirname(mmdc)) if p]
    env["PATH"] = os.pathsep.join(front + [env.get("PATH", "")]).rstrip(os.pathsep)
    return env


@dataclass
class MmdcResult:
    ok: bool
    png: bytes
    message: str
    returncode: int | None


def run_mmdc(cmd: list[str], source: str, env: dict[str, str], cwd: str, timeout: float) -> MmdcResult:
    """Run mmdc; ok only when it exits 0 and stdout is a PNG."""
    try:
        proc = subprocess.run(cmd, input=source.encode("utf-8"), capture_output=True,
                              env=env, cwd=cwd, timeout=timeout)
    except subprocess.TimeoutExpired:
        return MmdcResult(False, b"", "mmdc timed out after {:g} seconds".format(timeout), None)
    except OSError as e:
        return MmdcResult(False, b"", "could not start mmdc: {}".format(e), None)
    message = proc.stderr.decode("utf-8", errors="replace")
    if proc.returncode == 0 and proc.stdout.startswith(PNG_SIGNATURE):
        return MmdcResult(True, proc.stdout, message, 0)
    if proc.returncode == 0:
        message = (message + "\nmmdc exited 0 but did not write a PNG").strip()
    return MmdcResult(False, b"", message, proc.returncode)


def write_atomically(path: str, data: bytes) -> None:
    """Write data to path via a temp file in the same directory and os.replace.

    The result keeps an existing file's mode, or gets the umask default for a new file;
    NamedTemporaryFile alone would leave it owner-only (0600).
    """
    try:
        mode = stat.S_IMODE(os.stat(path).st_mode)
    except FileNotFoundError:
        umask = os.umask(0)
        os.umask(umask)
        mode = 0o666 & ~umask
    tmp = tempfile.NamedTemporaryFile(dir=os.path.dirname(path) or ".", prefix=".mermaid-preview-",
                                      suffix=".tmp", delete=False)
    try:
        with tmp:
            tmp.write(data)
        os.chmod(tmp.name, mode)
        os.replace(tmp.name, path)
    except BaseException:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass
        raise
