"""MCP Code Reviewer Server - Technology-aware code review with real-time progress."""

from mcp.server.fastmcp import FastMCP
from pathlib import Path
import json
from technology_detector import detect_technology
from checklist_engine import ChecklistEngine

# Initialize MCP server
mcp = FastMCP(name="Code Reviewer")

# Global state for tracking reviews
active_reviews = {}


@mcp.tool()
def detect_tech(project_path: str) -> str:
    """
    Detect technology stack from a project file (e.g., package.json, pyproject.toml).

    Args:
        project_path: Absolute path to a project configuration file (not a directory)

    Returns:
        JSON string with detected technology, frameworks, and confidence
    """
    try:
        # Validate that it's a file, not a directory
        path = Path(project_path)
        if path.is_dir():
            return json.dumps({
                "error": "project_path must be a file, not a directory. Please provide a path to a specific file like 'package.json' or 'pyproject.toml'",
                "primary": "unknown",
                "frameworks": [],
                "confidence": 0.0
            }, indent=2)

        if not path.exists():
            return json.dumps({
                "error": f"File does not exist: {project_path}",
                "primary": "unknown",
                "frameworks": [],
                "confidence": 0.0
            }, indent=2)

        # Get the parent directory for detection
        project_dir = str(path.parent)
        result = detect_technology(project_dir)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({
            "error": str(e),
            "primary": "unknown",
            "frameworks": [],
            "confidence": 0.0
        }, indent=2)


@mcp.tool()
def get_available_checklists(project_path: str = ".") -> str:
    """
    Get list of available technology checklists.

    Args:
        project_path: Path to any valid directory (default: current)

    Returns:
        JSON string with list of available technologies
    """
    try:
        engine = ChecklistEngine(project_path)
        checklists = engine.get_available_checklists()
        return json.dumps({
            "available_checklists": checklists,
            "count": len(checklists)
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def get_checklist(technology: str, project_path: str = ".") -> str:
    """
    Get checklist items for a specific technology.

    Args:
        technology: Technology name (python, javascript, java, etc.)
        project_path: Path to any valid directory (default: current)

    Returns:
        JSON string with complete checklist
    """
    try:
        engine = ChecklistEngine(project_path)
        checklist = engine.load_checklist(technology)

        # Format for readability
        formatted = {
            "technology": checklist['technology'],
            "description": checklist['description'],
            "categories": []
        }

        for category in checklist['categories']:
            formatted_category = {
                "name": category['name'],
                "checks": []
            }

            for check in category['items']:
                formatted_category['checks'].append({
                    "id": check['id'],
                    "description": check['description'],
                    "severity": check.get('severity', 'info')
                })

            formatted['categories'].append(formatted_category)

        return json.dumps(formatted, indent=2)

    except FileNotFoundError as e:
        return json.dumps({
            "error": str(e),
            "suggestion": "Use get_available_checklists() to see available technologies"
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def review_code(project_path: str, technology: str = None) -> str:
    """
    Execute comprehensive code review with real-time progress tracking.

    This will analyze the project and run all checks from the technology-specific
    checklist, showing pass/fail/skip counts as checks are executed.

    Args:
        project_path: Absolute path to project directory
        technology: Technology name (optional, will auto-detect if not provided)

    Returns:
        JSON string with complete review results including:
        - Progress summary (total, passed, failed, skipped, percentage)
        - Detailed failures with file locations and line numbers
        - Severity levels and recommendations
    """
    try:
        # Auto-detect if not specified
        if not technology:
            detection = detect_technology(project_path)
            technology = detection['primary']

            if technology == 'unknown':
                return json.dumps({
                    "error": "Could not detect technology. Please specify explicitly.",
                    "available": ChecklistEngine(project_path).get_available_checklists()
                }, indent=2)

        # Create engine and execute review
        engine = ChecklistEngine(project_path)

        # Progress updates (for real-time feedback)
        progress_updates = []

        def progress_callback(progress):
            progress_updates.append(progress.copy())

        # Execute review
        summary = engine.review_code(technology, progress_callback=progress_callback)

        # Format result
        result = {
            "project_path": project_path,
            "technology": technology,
            "summary": {
                "total_checks": summary['total'],
                "completed": summary['completed'],
                "passed": summary['passed'],
                "failed": summary['failed'],
                "skipped": summary['skipped'],
                "percentage": summary['percentage'],
                "status": summary['status']
            },
            "duration_seconds": summary.get('duration_seconds'),
            "failures": summary['failures'],
            "status_text": f"✅ {summary['passed']} passed | ❌ {summary['failed']} failed | ⏭️ {summary['skipped']} skipped"
        }

        # Store for later retrieval
        review_id = f"{Path(project_path).name}_{technology}"
        active_reviews[review_id] = result

        return json.dumps(result, indent=2)

    except FileNotFoundError as e:
        return json.dumps({
            "error": str(e),
            "suggestion": "Check that project_path is correct and checklist exists"
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "error": str(e),
            "type": type(e).__name__
        }, indent=2)


@mcp.tool()
def get_review_status(project_path: str, technology: str = None) -> str:
    """
    Get current status of a code review (for in-progress or completed reviews).

    Args:
        project_path: Path to project
        technology: Technology name (optional)

    Returns:
        JSON string with current review status and progress
    """
    try:
        # Generate review ID
        project_name = Path(project_path).name

        if not technology:
            detection = detect_technology(project_path)
            technology = detection['primary']

        review_id = f"{project_name}_{technology}"

        if review_id in active_reviews:
            return json.dumps(active_reviews[review_id], indent=2)
        else:
            return json.dumps({
                "error": "No active review found for this project",
                "suggestion": "Use review_code() to start a new review"
            }, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def add_custom_check(
    technology: str,
    category: str,
    check_id: str,
    description: str,
    severity: str = "info",
    patterns: str = None
) -> str:
    """
    Add a custom check to a technology checklist (advanced feature).

    Args:
        technology: Technology name
        category: Category name (Security, Code Quality, etc.)
        check_id: Unique check ID (e.g., CUSTOM-001)
        description: Check description
        severity: Severity level (critical, warning, info)
        patterns: Comma-separated regex patterns to check (optional)

    Returns:
        Success message or error
    """
    return json.dumps({
        "message": "Custom check addition feature coming soon!",
        "note": "You can manually edit YAML files in checklists/ directory"
    }, indent=2)


# Entry point for running the server
if __name__ == "__main__":
    mcp.run()
