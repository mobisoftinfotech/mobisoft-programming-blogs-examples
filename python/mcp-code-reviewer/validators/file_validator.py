"""File-based validator for checking file existence and structure."""

from typing import List, Dict, Any
from pathlib import Path
from .base_validator import BaseValidator, ValidationResult


class FileValidator(BaseValidator):
    """Validates project structure and file existence."""

    def validate(self, check: Dict[str, Any]) -> List[ValidationResult]:
        """
        Validate file existence.

        Args:
            check: Check definition with 'files' key

        Returns:
            List of validation results
        """
        results = []

        files_to_check = check.get('files', [])
        if not files_to_check:
            # Check for pattern-based files
            patterns = check.get('patterns', [])
            if patterns:
                return self._check_pattern_files(check, patterns)

            return [ValidationResult(
                check_id=check['id'],
                passed=True,
                message="No files specified"
            )]

        # Check if any of the specified files exist
        found = False
        for filename in files_to_check:
            file_path = self.project_path / filename
            if file_path.exists():
                found = True
                break

        if found:
            results.append(ValidationResult(
                check_id=check['id'],
                passed=True,
                message=check['description']
            ))
        else:
            results.append(ValidationResult(
                check_id=check['id'],
                passed=False,
                message=f"Missing required files: {', '.join(files_to_check)}",
                severity=check.get('severity', 'info')
            ))

        return results

    def _check_pattern_files(self, check: Dict[str, Any], patterns: List[str]) -> List[ValidationResult]:
        """Check for files matching patterns."""
        results = []
        found = False

        for pattern in patterns:
            matching_files = list(self.project_path.rglob(pattern))

            # Filter out common directories to skip
            skip_dirs = {'node_modules', 'venv', '.venv', '__pycache__',
                        'dist', 'build', '.git', 'coverage'}

            matching_files = [
                f for f in matching_files
                if not any(skip_dir in f.parts for skip_dir in skip_dirs)
            ]

            if matching_files:
                found = True
                break

        if found:
            results.append(ValidationResult(
                check_id=check['id'],
                passed=True,
                message=f"{check['description']} - Found {len(matching_files)} file(s)"
            ))
        else:
            results.append(ValidationResult(
                check_id=check['id'],
                passed=False,
                message=f"No files found matching patterns: {', '.join(patterns)}",
                severity=check.get('severity', 'info')
            ))

        return results
