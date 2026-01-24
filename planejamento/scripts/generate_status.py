"""Generate status.md and CHANGELOG.md from tasks.yaml.
Usage:
    python planejamento/scripts/generate_status.py
If PyYAML is not available, falls back to a minimal YAML parser (list of maps with simple scalars/lists).
Outputs are written into the planejamento/ folder (same base as tasks.yaml).
"""
from __future__ import annotations
import sys
from datetime import datetime
from pathlib import Path

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover
    yaml = None

ROOT = Path(__file__).resolve().parent.parent
TASKS_FILE = ROOT / "tasks.yaml"
STATUS_FILE = ROOT / "status.md"
CHANGELOG_FILE = ROOT / "CHANGELOG.md"
VALID_STATUSES = {"pending", "doing", "done", "reverted"}


def parse_minimal_yaml(text: str):
    tasks = []
    current = None
    in_links = False
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("- "):
            if current:
                tasks.append(current)
            current = {}
            line = line[2:].strip()
            if line and ":" in line:
                key, val = line.split(":", 1)
                current[key.strip()] = val.strip()
            in_links = False
            continue
        if current is None:
            continue
        if line.startswith("links:"):
            current["links"] = []
            in_links = True
            continue
        if in_links and line.startswith("- "):
            current.setdefault("links", []).append(line[2:].strip())
            continue
        if ":" in line:
            in_links = False
            key, val = line.split(":", 1)
            current[key.strip()] = val.strip()
    if current:
        tasks.append(current)
    return tasks


def load_tasks():
    if not TASKS_FILE.exists():
        sys.stderr.write(f"tasks.yaml not found at {TASKS_FILE}\n")
        sys.exit(1)
    text = TASKS_FILE.read_text(encoding="utf-8")
    if yaml:
        data = yaml.safe_load(text) or []
    else:
        data = parse_minimal_yaml(text)
    if not isinstance(data, list):
        sys.stderr.write("tasks.yaml must be a list of task objects\n")
        sys.exit(1)
    tasks = []
    for item in data:
        if not isinstance(item, dict):
            continue
        status_raw = str(item.get("status", "pending")).lower()
        status = status_raw if status_raw in VALID_STATUSES else "pending"
        tasks.append({
            "id": item.get("id", ""),
            "titulo": item.get("titulo", ""),
            "status": status,
            "prioridade": item.get("prioridade", ""),
            "area": item.get("area", ""),
            "owner": item.get("owner", ""),
            "descricao": item.get("descricao", ""),
        })
    return tasks


def format_task_line(task):
    bits = [str(task.get("id", "")).strip(), str(task.get("titulo", "")).strip()]
    meta = []
    if task.get("prioridade"):
        meta.append(f"prio: {task['prioridade']}")
    if task.get("area"):
        meta.append(f"area: {task['area']}")
    if task.get("owner"):
        meta.append(f"owner: {task['owner']}")
    if meta:
        bits.append(f"({' | '.join(meta)})")
    return " - ".join([b for b in bits if b])


def generate_status(tasks):
    today = datetime.now().strftime("%Y-%m-%d")
    by_status = {s: [] for s in VALID_STATUSES}
    for t in tasks:
        by_status[t["status"]].append(t)
    lines = [
        "# Status das Atividades",
        f"Data: {today}",
        "",
        "Resumo:",
        f"- Total: {len(tasks)}",
        f"- Em andamento: {len(by_status['doing'])}",
        f"- A fazer: {len(by_status['pending'])}",
        f"- Concluídas: {len(by_status['done'])}",
        f"- Revertidas: {len(by_status['reverted'])}",
        "",
    ]
    for section, title in (
        ("doing", "Em andamento"),
        ("pending", "A fazer"),
        ("done", "Concluídas"),
        ("reverted", "Revertidas"),
    ):
        lines.append(f"## {title}")
        if by_status[section]:
            for t in by_status[section]:
                lines.append(f"- {format_task_line(t)}")
        else:
            lines.append("- (nenhuma)")
        lines.append("")
    STATUS_FILE.write_text("\n".join(lines), encoding="utf-8")


def generate_changelog(tasks):
    done = [t for t in tasks if t["status"] == "done"]
    reverted = [t for t in tasks if t["status"] == "reverted"]
    today = datetime.now().strftime("%Y-%m-%d")
    lines = ["# Changelog", "", f"## {today}"]
    if not done:
        lines.append("- Nenhuma tarefa concluída ainda.")
    else:
        for t in done:
            lines.append(f"- {format_task_line(t)}")
    if reverted:
        lines.append("")
        lines.append("Revertidas:")
        for t in reverted:
            lines.append(f"- {format_task_line(t)}")
    CHANGELOG_FILE.write_text("\n".join(lines), encoding="utf-8")


def main():
    tasks = load_tasks()
    generate_status(tasks)
    generate_changelog(tasks)
    print(f"Gerados: {STATUS_FILE} e {CHANGELOG_FILE}")


if __name__ == "__main__":
    main()
