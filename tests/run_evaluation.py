from __future__ import annotations

import csv
from pathlib import Path

from app.core import load_knowledge, retrieve, sensitive_route

ROOT = Path(__file__).resolve().parents[1]
knowledge = load_knowledge(ROOT / "data" / "knowledge_base.csv")


def predicted(question: str) -> tuple[str, str]:
    department = sensitive_route(question)
    if department:
        return "escalated", department
    if retrieve(question, knowledge):
        return "answered", ""
    return "not_found", "HR"


def main() -> int:
    with (ROOT / "data" / "evaluation_cases.csv").open(encoding="utf-8-sig", newline="") as handle:
        cases = list(csv.DictReader(handle))

    failures = []
    for case in cases:
        actual_status, actual_department = predicted(case["question"])
        if actual_status != case["expected_status"]:
            failures.append(f"{case['id']}: ожидался {case['expected_status']}, получен {actual_status}")
        expected_department = case["expected_department"]
        if expected_department and actual_department != expected_department:
            failures.append(f"{case['id']}: ожидался отдел {expected_department}, получен {actual_department}")

    print(f"Проверено сценариев: {len(cases)}")
    print(f"Успешно: {len(cases) - len({line.split(':')[0] for line in failures})}")
    if failures:
        print("Ошибки:")
        print("\n".join(failures))
        return 1
    print("Все сценарии прошли проверку.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

