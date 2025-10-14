"""Base validator class for all code review checks."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from pathlib import Path


class ValidationResult:
    """Result of a validation check."""

    def __init__(
        self,
        check_id: str,
        passed: bool,
        message: str = "",
        file_path: str = "",
        line_number: int = 0,
        severity: str = "info"
    ):
        self.check_id = check_id
        self.passed = passed
        self.message = message
        self.file_path = file_path
        self.line_number = line_number
        self.severity = severity

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "check_id": self.check_id,
            "passed": self.passed,
            "message": self.message,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "severity": self.severity
        }


class BaseValidator(ABC):
    """Base class for all validators."""

    def __init__(self, project_path: Path):
        """Initialize validator with project path."""
        self.project_path = project_path

    @abstractmethod
    def validate(self, check: Dict[str, Any]) -> List[ValidationResult]:
        """
        Validate a check against the project.

        Args:
            check: Check definition from checklist

        Returns:
            List of validation results
        """
        pass

    def get_files_to_check(self, extensions: List[str]) -> List[Path]:
        """
        Get all files with given extensions in project.

        Args:
            extensions: List of file extensions (e.g., ['.py', '.js'])

        Returns:
            List of file paths
        """
        files = []
        for ext in extensions:
            files.extend(self.project_path.rglob(f"*{ext}"))

        # Filter out common directories to skip
        skip_dirs = {'node_modules', 'venv', '.venv', '__pycache__',
                     'dist', 'build', '.git', 'coverage'}

        return [
            f for f in files
            if not any(skip_dir in f.parts for skip_dir in skip_dirs)
        ]
