"""Pattern-based validator for regex pattern matching."""

import re
from typing import List, Dict, Any
from pathlib import Path
from .base_validator import BaseValidator, ValidationResult


class PatternValidator(BaseValidator):
    """Validates code using regex patterns."""

    def validate(self, check: Dict[str, Any]) -> List[ValidationResult]:
        """
        Validate using regex patterns.

        Args:
            check: Check definition with 'patterns' key

        Returns:
            List of validation results
        """
        results = []

        patterns = check.get('patterns', [])
        if not patterns:
            return [ValidationResult(
                check_id=check['id'],
                passed=True,
                message="No patterns defined"
            )]

        # Get file extensions based on technology
        extensions = self._get_extensions(check.get('technology', 'python'))
        files = self.get_files_to_check(extensions)

        if not files:
            return [ValidationResult(
                check_id=check['id'],
                passed=True,
                message="No files found to check"
            )]

        # Check each file
        for file_path in files:
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                lines = content.split('\n')

                for pattern_str in patterns:
                    pattern = re.compile(pattern_str, re.IGNORECASE | re.MULTILINE)

                    for line_num, line in enumerate(lines, start=1):
                        if pattern.search(line):
                            results.append(ValidationResult(
                                check_id=check['id'],
                                passed=False,
                                message=f"Pattern match: {check['description']}",
                                file_path=str(file_path.relative_to(self.project_path)),
                                line_number=line_num,
                                severity=check.get('severity', 'info')
                            ))

            except Exception as e:
                results.append(ValidationResult(
                    check_id=check['id'],
                    passed=False,
                    message=f"Error reading file: {str(e)}",
                    file_path=str(file_path.relative_to(self.project_path)),
                    severity='error'
                ))

        # If no issues found, mark as passed
        if not results:
            results.append(ValidationResult(
                check_id=check['id'],
                passed=True,
                message=check['description']
            ))

        return results

    def _get_extensions(self, technology: str) -> List[str]:
        """Get file extensions for technology."""
        ext_map = {
            'python': ['.py'],
            'javascript': ['.js', '.jsx'],
            'typescript': ['.ts', '.tsx'],
            'java': ['.java'],
            'go': ['.go'],
            'rust': ['.rs']
        }
        return ext_map.get(technology, ['.py'])
