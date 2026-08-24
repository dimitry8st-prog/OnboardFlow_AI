from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class KnowledgeItem:
    id: str
    category: str
    question: str
    answer: str
    steps: str
    department: str
    contact: str
    escalation_rule: str
    updated_at: str
    owner: str


TOKEN_RE = re.compile(r"[а-яёa-z0-9]+", re.IGNORECASE)
STOP_WORDS = {"как", "что", "где", "кто", "мне", "для", "это", "если", "или", "на", "в", "и", "по", "с"}
TERM_ALIASES = {
    "адаптацией": "адаптация",
    "адаптации": "адаптация",
    "помогает": "помощь",
    "помощью": "помощь",
}
SENSITIVE_ROUTES = {
    "HR": ("уволь", "зарплат", "оклад", "отпуск", "договор", "перевод", "дискриминац", "конфликт"),
    "Информационная безопасность": ("пароль коллег", "чужой пароль", "паспорт", "банковск", "персональн", "утечк"),
}


def load_knowledge(path: Path) -> list[KnowledgeItem]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return [KnowledgeItem(**row) for row in csv.DictReader(handle)]


def tokens(text: str) -> set[str]:
    result = set()
    for raw_word in TOKEN_RE.findall(text):
        word = raw_word.lower()
        if len(word) > 2 and word not in STOP_WORDS:
            result.add(TERM_ALIASES.get(word, word))
    return result


def sensitive_route(message: str) -> str | None:
    normalized = message.lower()
    for department, markers in SENSITIVE_ROUTES.items():
        if any(marker in normalized for marker in markers):
            return department
    return None


def retrieve(message: str, knowledge: list[KnowledgeItem], limit: int = 3) -> list[KnowledgeItem]:
    query = tokens(message)
    ranked: list[tuple[float, KnowledgeItem]] = []
    for item in knowledge:
        question_tokens = tokens(item.question)
        body_tokens = tokens(f"{item.category} {item.answer} {item.steps}")
        score = len(query & question_tokens) * 3 + len(query & body_tokens)
        if score:
            ranked.append((score / max(len(query), 1), item))
    ranked.sort(key=lambda pair: pair[0], reverse=True)
    return [item for _, item in ranked[:limit]]
