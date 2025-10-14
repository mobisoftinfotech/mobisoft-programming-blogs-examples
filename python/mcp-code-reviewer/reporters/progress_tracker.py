"""Progress tracker for real-time code review updates."""

from typing import Dict, Any, List
from datetime import datetime


class ProgressTracker:
    """Tracks and reports progress of code review checks."""

    def __init__(self):
        """Initialize progress tracker."""
        self.total_checks = 0
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.in_progress = 0
        self.current_check = None
        self.failures = []
        self.start_time = None
        self.end_time = None

    def start(self, total_checks: int):
        """Start tracking progress."""
        self.total_checks = total_checks
        self.start_time = datetime.now()
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.in_progress = 0
        self.failures = []

    def update_check(self, check_id: str, description: str):
        """Update current check being processed."""
        self.current_check = {
            "id": check_id,
            "description": description
        }
        self.in_progress = 1

    def record_pass(self):
        """Record a passed check."""
        self.passed += 1
        self.in_progress = 0

    def record_fail(self, failure_info: Dict[str, Any]):
        """Record a failed check."""
        self.failed += 1
        self.in_progress = 0
        self.failures.append(failure_info)

    def record_skip(self):
        """Record a skipped check."""
        self.skipped += 1
        self.in_progress = 0

    def complete(self):
        """Mark review as complete."""
        self.end_time = datetime.now()
        self.in_progress = 0

    def get_progress(self) -> Dict[str, Any]:
        """
        Get current progress.

        Returns:
            Progress dictionary with stats
        """
        completed = self.passed + self.failed + self.skipped
        percentage = (completed / self.total_checks * 100) if self.total_checks > 0 else 0

        return {
            "total": self.total_checks,
            "completed": completed,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "percentage": round(percentage, 1),
            "current_check": self.current_check,
            "in_progress": self.in_progress > 0
        }

    def get_summary(self) -> Dict[str, Any]:
        """
        Get complete summary.

        Returns:
            Complete summary with failures
        """
        progress = self.get_progress()

        duration = None
        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()

        return {
            **progress,
            "failures": self.failures,
            "duration_seconds": duration,
            "status": "completed" if self.end_time else "in_progress"
        }

    def format_progress_bar(self) -> str:
        """
        Format progress as text bar.

        Returns:
            Progress bar string
        """
        progress = self.get_progress()
        percentage = progress['percentage']
        completed = progress['completed']
        total = progress['total']

        # Create progress bar
        bar_length = 20
        filled = int(bar_length * percentage / 100)
        bar = '█' * filled + '░' * (bar_length - filled)

        return f"[{bar}] {percentage}% ({completed}/{total})"

    def format_status(self) -> str:
        """
        Format status with emojis.

        Returns:
            Status string with pass/fail/skip counts
        """
        return f"✅ {self.passed} passed | ❌ {self.failed} failed | ⏭️ {self.skipped} skipped"

    def format_failures(self) -> List[str]:
        """
        Format failures as readable list.

        Returns:
            List of formatted failure strings
        """
        formatted = []

        for failure in self.failures:
            severity_emoji = {
                'critical': '🔴',
                'warning': '🟡',
                'info': '🔵',
                'error': '⚠️'
            }.get(failure.get('severity', 'info'), '•')

            location = ""
            if failure.get('file_path'):
                location = f"{failure['file_path']}"
                if failure.get('line_number'):
                    location += f":{failure['line_number']}"

            formatted.append(
                f"{severity_emoji} {failure['check_id']}: {failure['message']}"
                + (f" ({location})" if location else "")
            )

        return formatted
