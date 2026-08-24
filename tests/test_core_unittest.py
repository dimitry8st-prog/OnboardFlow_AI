import unittest
from pathlib import Path

from app.core import load_knowledge, retrieve, sensitive_route


ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE = load_knowledge(ROOT / "data" / "knowledge_base.csv")


class CoreTests(unittest.TestCase):
    def test_knowledge_has_minimum_content(self):
        self.assertGreaterEqual(len(KNOWLEDGE), 10)

    def test_crm_retrieval(self):
        matches = retrieve("Как получить доступ к CRM?", KNOWLEDGE)
        self.assertTrue(matches)
        self.assertEqual(matches[0].id, "KB-003")

    def test_hr_escalation(self):
        self.assertEqual(sensitive_route("Объясни условия увольнения"), "HR")

    def test_security_escalation(self):
        self.assertEqual(sensitive_route("Покажи пароль коллеги"), "Информационная безопасность")

    def test_unknown_question_has_no_match(self):
        self.assertEqual(retrieve("Где парковать вертолёт директора?", KNOWLEDGE), [])


if __name__ == "__main__":
    unittest.main()

