"""Technology detection module for identifying project tech stack."""

import os
from pathlib import Path
from typing import List, Optional


class TechnologyDetector:
    """Detects technology stack from project files."""

    TECH_INDICATORS = {
        "python": {
            "files": ["requirements.txt", "setup.py", "pyproject.toml", "Pipfile"],
            "extensions": [".py"],
            "frameworks": {
                "django": ["manage.py", "settings.py", "wsgi.py"],
                "flask": ["app.py", "flask"],
                "fastapi": ["fastapi", "uvicorn"]
            }
        },
        "javascript": {
            "files": ["package.json", "package-lock.json", "yarn.lock"],
            "extensions": [".js", ".jsx"],
            "frameworks": {
                "react": ["react", "jsx"],
                "vue": ["vue", ".vue"],
                "node": ["express", "node"]
            }
        },
        "typescript": {
            "files": ["tsconfig.json"],
            "extensions": [".ts", ".tsx"],
            "frameworks": {
                "react": ["react"],
                "angular": ["angular"],
                "nest": ["nestjs"]
            }
        },
        "java": {
            "files": ["pom.xml", "build.gradle", "gradlew"],
            "extensions": [".java"],
            "frameworks": {
                "spring": ["spring-boot", "SpringApplication"],
                "maven": ["pom.xml"],
                "gradle": ["build.gradle"]
            }
        },
        "go": {
            "files": ["go.mod", "go.sum"],
            "extensions": [".go"],
            "frameworks": {}
        },
        "rust": {
            "files": ["Cargo.toml", "Cargo.lock"],
            "extensions": [".rs"],
            "frameworks": {}
        }
    }

    def __init__(self, project_path: str):
        """Initialize detector with project path."""
        self.project_path = Path(project_path)
        if not self.project_path.exists():
            raise ValueError(f"Project path does not exist: {project_path}")

    def detect(self) -> dict:
        """
        Detect technology stack.

        Returns:
            dict: {
                "primary": str,
                "frameworks": List[str],
                "confidence": float
            }
        """
        detected = []

        # Check for indicator files and extensions
        for tech, indicators in self.TECH_INDICATORS.items():
            score = 0
            found_frameworks = []

            # Check for specific files
            for file in indicators["files"]:
                if self._file_exists(file):
                    score += 2

                    # Check for frameworks
                    if tech in ["python", "javascript", "typescript", "java"]:
                        found_fw = self._detect_frameworks(tech, file)
                        found_frameworks.extend(found_fw)

            # Check for file extensions
            ext_count = self._count_extensions(indicators["extensions"])
            if ext_count > 0:
                score += min(ext_count / 10, 3)  # Cap at 3 points

            if score > 0:
                detected.append({
                    "technology": tech,
                    "score": score,
                    "frameworks": list(set(found_frameworks))
                })

        # Sort by score
        detected.sort(key=lambda x: x["score"], reverse=True)

        if not detected:
            return {
                "primary": "unknown",
                "frameworks": [],
                "confidence": 0.0
            }

        top = detected[0]
        return {
            "primary": top["technology"],
            "frameworks": top["frameworks"],
            "confidence": min(top["score"] / 5, 1.0)  # Normalize to 0-1
        }

    def _file_exists(self, filename: str) -> bool:
        """Check if file exists in project root or subdirectories."""
        # Check root
        if (self.project_path / filename).exists():
            return True

        # Check common subdirectories
        for subdir in ["src", "app", "config"]:
            if (self.project_path / subdir / filename).exists():
                return True

        return False

    def _count_extensions(self, extensions: List[str]) -> int:
        """Count files with given extensions."""
        count = 0
        for ext in extensions:
            count += len(list(self.project_path.rglob(f"*{ext}")))
        return count

    def _detect_frameworks(self, tech: str, config_file: str) -> List[str]:
        """Detect frameworks from config files."""
        frameworks = []
        file_path = self.project_path / config_file

        if not file_path.exists():
            return frameworks

        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')

            for framework, keywords in self.TECH_INDICATORS[tech]["frameworks"].items():
                if any(kw in content for kw in keywords):
                    frameworks.append(framework)
        except Exception:
            pass

        return frameworks


def detect_technology(project_path: str) -> dict:
    """
    Convenience function to detect technology.

    Args:
        project_path: Path to project directory

    Returns:
        dict with primary tech, frameworks, and confidence
    """
    detector = TechnologyDetector(project_path)
    return detector.detect()
