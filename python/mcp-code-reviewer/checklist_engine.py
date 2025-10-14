"""Checklist engine for executing code review checks."""

import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from validators import PatternValidator, FileValidator
from reporters import ProgressTracker


class ChecklistEngine:
    """Executes code review checklists with progress tracking."""

    def __init__(self, project_path: str, checklist_dir: Optional[str] = None):
        """
        Initialize checklist engine.

        Args:
            project_path: Path to project to review
            checklist_dir: Path to checklist directory (optional)
        """
        self.project_path = Path(project_path)
        if not self.project_path.exists():
            raise ValueError(f"Project path does not exist: {project_path}")

        # Set checklist directory
        if checklist_dir:
            self.checklist_dir = Path(checklist_dir)
        else:
            # Default to checklists/ in same directory as this file
            self.checklist_dir = Path(__file__).parent / "checklists"

        self.progress_tracker = ProgressTracker()
        self.current_checklist = None

    def load_checklist(self, technology: str) -> Dict[str, Any]:
        """
        Load checklist for technology.

        Args:
            technology: Technology name (python, javascript, java, etc.)

        Returns:
            Checklist dictionary

        Raises:
            FileNotFoundError: If checklist doesn't exist
        """
        checklist_path = self.checklist_dir / f"{technology}.yaml"

        if not checklist_path.exists():
            raise FileNotFoundError(
                f"Checklist not found for technology: {technology}"
            )

        with open(checklist_path, 'r') as f:
            checklist = yaml.safe_load(f)

        self.current_checklist = checklist
        return checklist

    def get_available_checklists(self) -> List[str]:
        """
        Get list of available checklists.

        Returns:
            List of technology names
        """
        if not self.checklist_dir.exists():
            return []

        return [
            f.stem for f in self.checklist_dir.glob("*.yaml")
        ]

    def review_code(
        self,
        technology: str,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> Dict[str, Any]:
        """
        Execute code review for technology.

        Args:
            technology: Technology to review (python, javascript, etc.)
            progress_callback: Optional callback for progress updates

        Returns:
            Review results dictionary
        """
        # Load checklist
        checklist = self.load_checklist(technology)

        # Count total checks
        total_checks = sum(
            len(category['items'])
            for category in checklist['categories']
        )

        # Start tracking
        self.progress_tracker.start(total_checks)

        # Execute checks
        all_results = []

        for category in checklist['categories']:
            category_name = category['name']

            for check in category['items']:
                check_id = check['id']
                description = check['description']

                # Update progress
                self.progress_tracker.update_check(check_id, description)

                if progress_callback:
                    progress_callback(self.progress_tracker.get_progress())

                # Execute validation
                results = self._execute_check(check, technology)

                # Record results
                passed = all(r.passed for r in results)

                if passed:
                    self.progress_tracker.record_pass()
                else:
                    # Record each failure
                    for result in results:
                        if not result.passed:
                            self.progress_tracker.record_fail({
                                "check_id": check_id,
                                "category": category_name,
                                "message": result.message,
                                "file_path": result.file_path,
                                "line_number": result.line_number,
                                "severity": result.severity
                            })

                all_results.extend(results)

                if progress_callback:
                    progress_callback(self.progress_tracker.get_progress())

        # Complete tracking
        self.progress_tracker.complete()

        # Return summary
        return self.progress_tracker.get_summary()

    def _execute_check(self, check: Dict[str, Any], technology: str) -> List:
        """
        Execute a single check.

        Args:
            check: Check definition
            technology: Technology name

        Returns:
            List of validation results
        """
        check['technology'] = technology

        # Determine validator type
        if 'patterns' in check:
            validator = PatternValidator(self.project_path)
            return validator.validate(check)
        elif 'files' in check:
            validator = FileValidator(self.project_path)
            return validator.validate(check)
        else:
            # Default: file validator for pattern-based checks
            validator = FileValidator(self.project_path)
            return validator.validate(check)

    def get_progress(self) -> Dict[str, Any]:
        """Get current progress."""
        return self.progress_tracker.get_progress()

    def get_summary(self) -> Dict[str, Any]:
        """Get review summary."""
        return self.progress_tracker.get_summary()

    def format_report(self) -> str:
        """
        Format review report as text.

        Returns:
            Formatted report string
        """
        summary = self.get_summary()

        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("CODE REVIEW REPORT")
        report_lines.append("=" * 60)
        report_lines.append("")

        # Progress
        report_lines.append(self.progress_tracker.format_progress_bar())
        report_lines.append(self.progress_tracker.format_status())
        report_lines.append("")

        # Duration
        if summary.get('duration_seconds'):
            report_lines.append(f"Duration: {summary['duration_seconds']:.2f}s")
            report_lines.append("")

        # Failures
        if summary['failures']:
            report_lines.append("FAILURES:")
            report_lines.append("-" * 60)
            for failure_line in self.progress_tracker.format_failures():
                report_lines.append(failure_line)
        else:
            report_lines.append("✨ All checks passed!")

        report_lines.append("")
        report_lines.append("=" * 60)

        return "\n".join(report_lines)
