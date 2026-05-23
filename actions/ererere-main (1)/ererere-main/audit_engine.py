import json
import re
from dataclasses import dataclass
from pathlib import Path


AUDIT_REPORT_NAME = "project_audit_report.json"
EXCLUDED_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    "vosk-model-small-tr-0.3",
    "Backups",
}
SCANNED_EXTENSIONS = {".py", ".json", ".md"}
PATTERNS = {
    "blocking_sleep": re.compile(r"\btime\.sleep\("),
    "hard_exit": re.compile(r"\bos\._exit\("),
    "infinite_loop": re.compile(r"^\s*while\s+True\s*:", re.MULTILINE),
}
MOJIBAKE_MARKERS = ("Ã", "Å", "â€", "ðŸ", "\ufffd")


@dataclass
class AuditFinding:
    kind: str
    path: str
    line: int
    excerpt: str

    def as_dict(self):
        return {
            "kind": self.kind,
            "path": self.path,
            "line": self.line,
            "excerpt": self.excerpt,
        }


class ProjectAuditEngine:
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.report_path = self.base_dir / "memory" / AUDIT_REPORT_NAME

    def _should_skip(self, path: Path) -> bool:
        return any(part in EXCLUDED_DIRS for part in path.parts)

    def _iter_files(self):
        for path in self.base_dir.rglob("*"):
            if not path.is_file():
                continue
            if self._should_skip(path):
                continue
            if path.suffix.lower() not in SCANNED_EXTENSIONS:
                continue
            yield path

    def _scan_text(self, path: Path, text: str):
        findings = []
        lines = text.splitlines()

        for kind, pattern in PATTERNS.items():
            for match in pattern.finditer(text):
                line_no = text.count("\n", 0, match.start()) + 1
                excerpt = lines[line_no - 1].strip() if 0 < line_no <= len(lines) else ""
                findings.append(
                    AuditFinding(
                        kind=kind,
                        path=str(path.relative_to(self.base_dir)),
                        line=line_no,
                        excerpt=excerpt,
                    )
                )

        for index, line in enumerate(lines, start=1):
            if any(marker in line for marker in MOJIBAKE_MARKERS):
                findings.append(
                    AuditFinding(
                        kind="text_encoding",
                        path=str(path.relative_to(self.base_dir)),
                        line=index,
                        excerpt=line.strip(),
                    )
                )
        return findings

    def run(self):
        findings = []
        scanned_files = 0

        for path in self._iter_files():
            scanned_files += 1
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                try:
                    text = path.read_text(encoding="utf-8-sig")
                except Exception:
                    continue
            except Exception:
                continue

            findings.extend(self._scan_text(path, text))

        summary = {
            "scanned_files": scanned_files,
            "total_findings": len(findings),
            "by_kind": {},
            "findings": [finding.as_dict() for finding in findings[:250]],
        }

        for finding in findings:
            summary["by_kind"][finding.kind] = summary["by_kind"].get(finding.kind, 0) + 1

        self.report_path.parent.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return summary
