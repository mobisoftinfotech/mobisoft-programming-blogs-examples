"""MCP code review server (MCP Python SDK v2).

A standalone, simplified server. It does not import the Part 1 modules.
"""

import json
import os
import re
import time
import uuid
from pathlib import Path

import yaml
from mcp.server.mcpserver import Context, MCPServer

mcp = MCPServer(name="Code Reviewer")

CHECKLIST_DIR = Path(__file__).parent / "checklists"
CONFIG_FILES = {
    "package.json": "JavaScript",
    "pyproject.toml": "Python",
    "requirements.txt": "Python",
    "pom.xml": "Java",
}
SKIP_DIRS = {"node_modules", ".git", ".venv", "venv", "__pycache__", "dist"}
SECRET_NAMES = {".env", "id_rsa", "id_ed25519"}
SECRET_SUFFIXES = {".pem", ".key", ".p12"}
SOURCE_SUFFIXES = {".js": "JavaScript", ".py": "Python", ".java": "Java"}
MAX_FILES = 500
MAX_FILE_BYTES = 200_000
MAX_SECONDS = 20

# In-memory state. It disappears on restart and is not shared
# between processes.
active_reviews: dict = {}


def allowed_roots() -> list:
    """Approved folders. Default to the server's own folder."""
    raw = os.getenv("REVIEW_ALLOWED_DIRS", "")
    roots = [Path(p).resolve() for p in raw.split(os.pathsep) if p.strip()]
    return roots or [Path.cwd().resolve()]


def resolve_inside_roots(raw_path: str) -> Path:
    """Resolve symlinks, then require the result inside an approved root."""
    roots = allowed_roots()
    path = Path(raw_path).expanduser().resolve()
    if not any(path.is_relative_to(root) for root in roots):
        raise ValueError("Path is outside the approved project folders.")
    if not path.exists():
        raise ValueError(f"Path does not exist: {raw_path}")
    return path


def is_secret_file(path: Path) -> bool:
    return path.name in SECRET_NAMES or path.suffix in SECRET_SUFFIXES


def collect_files(root: Path, deadline: float):
    """Walk a project without following symlinks. Skip secrets and big files."""
    files, skipped = [], 0
    for folder, dirs, names in os.walk(root, followlinks=False):
        if time.monotonic() > deadline:
            return files, skipped, True
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in names:
            path = Path(folder) / name
            if path.is_symlink() or is_secret_file(path):
                skipped += 1
            elif path.suffix not in SOURCE_SUFFIXES:
                continue
            elif path.stat().st_size > MAX_FILE_BYTES:
                skipped += 1
            elif len(files) >= MAX_FILES:
                return files, skipped + 1, True
            else:
                files.append(path)
    return files, skipped, False


def fail(message: str) -> str:
    return json.dumps({"error": message})


@mcp.tool()
def detect_tech(project_path: str) -> str:
    """
    Detect the technology from a project file such as package.json.

    Args:
        project_path: Absolute path to a project configuration file
            (not a directory)

    Returns:
        JSON string with the detected technology and confidence
    """
    try:
        path = resolve_inside_roots(project_path)
        if path.is_dir():
            return fail("project_path must be a file, not a directory.")
        if path.name not in CONFIG_FILES:
            names = ", ".join(sorted(CONFIG_FILES))
            return fail(f"Unsupported file. Use one of: {names}")
        return json.dumps(
            {
                "technology": CONFIG_FILES[path.name],
                "confidence": 0.9,
                "detected_from": path.name,
            },
            indent=2,
        )
    except ValueError as exc:
        return fail(str(exc))
    except OSError as exc:
        return fail(f"Could not read the path: {type(exc).__name__}")


@mcp.tool()
def get_available_checklists() -> str:
    """List the YAML checklists that this server can apply."""
    names = sorted(p.stem for p in CHECKLIST_DIR.glob("*.yaml"))
    return json.dumps({"checklists": names})


@mcp.tool()
def get_checklist(name: str) -> str:
    """Return the checks in one checklist, such as javascript."""
    if not re.fullmatch(r"[a-z0-9_-]+", name):
        return fail("Checklist names use lowercase letters, digits, - and _.")
    path = CHECKLIST_DIR / f"{name}.yaml"
    if not path.is_file():
        return fail(f"Unknown checklist: {name}")
    return json.dumps(yaml.safe_load(path.read_text(encoding="utf-8")))


@mcp.tool()
async def review_code(project_path: str, ctx: Context) -> str:
    """
    Review a project folder with the checklist for its technology.

    Args:
        project_path: Absolute path to a project folder
    """
    try:
        root = resolve_inside_roots(project_path)
    except ValueError as exc:
        return fail(str(exc))
    if not root.is_dir():
        return fail("project_path must be a folder for a full review.")
    review_id = uuid.uuid4().hex[:8]
    active_reviews[review_id] = {"status": "running", "path": str(root)}
    try:
        deadline = time.monotonic() + MAX_SECONDS
        files, skipped, truncated = collect_files(root, deadline)
        findings = []
        for index, path in enumerate(files, start=1):
            if time.monotonic() > deadline:
                active_reviews[review_id]["status"] = "stopped (time limit)"
                break
            await ctx.report_progress(
                index, len(files), f"Reviewing {path.name}"
            )
            checklist = (
                CHECKLIST_DIR / f"{SOURCE_SUFFIXES[path.suffix].lower()}.yaml"
            )
            rules = yaml.safe_load(checklist.read_text(encoding="utf-8"))
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                skipped += 1
                continue
            for category in rules.get("categories", []):
                for check in category.get("items", []):
                    # Test-file checks hold file-name globs, not regexes.
                    if check.get("validator") == "check_test_files":
                        continue
                    for pattern in check.get("patterns", []):
                        if re.search(pattern, text, re.MULTILINE):
                            findings.append(
                                {
                                    "file": str(path.relative_to(root)),
                                    "check": check["id"],
                                }
                            )
                            break
        status = active_reviews[review_id]["status"]
        if status == "running":
            status = "completed"
        active_reviews[review_id].update(
            status=status, findings=len(findings), skipped=skipped
        )
        return json.dumps(
            {
                "review_id": review_id,
                "status": status,
                "files": len(files),
                "skipped": skipped,
                "truncated": truncated,
                "findings": findings,
            },
            indent=2,
        )
    except Exception as exc:
        active_reviews[review_id]["status"] = "failed"
        return fail(f"Review failed: {type(exc).__name__}")


@mcp.tool()
def get_review_status(review_id: str) -> str:
    """Return the status of a review started in this server session."""
    review = active_reviews.get(review_id)
    if review is None:
        return fail("Unknown review_id. State resets when the server restarts.")
    return json.dumps(review)


if __name__ == "__main__":
    mcp.run()
