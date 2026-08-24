from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.core import KnowledgeItem, load_knowledge, retrieve as core_retrieve, sensitive_route

load_dotenv()

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "knowledge_base.csv"
PROMPT_FILE = ROOT / "docs" / "system_prompt.md"
STATIC_DIR = ROOT / "static"

app = FastAPI(title="OnboardFlow AI", version="1.0.0")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class ChatRequest(BaseModel):
    message: str = Field(min_length=2, max_length=2000)


class Source(BaseModel):
    id: str
    category: str
    title: str
    updated_at: str


class ChatResponse(BaseModel):
    answer: str
    status: str
    escalation: bool
    department: str | None = None
    sources: list[Source] = []
    mode: str


KNOWLEDGE = load_knowledge(DATA_FILE)


def retrieve(message: str, limit: int = 3) -> list[KnowledgeItem]:
    return core_retrieve(message, KNOWLEDGE, limit)


def format_demo_answer(item: KnowledgeItem) -> str:
    parts = [item.answer.strip()]
    if item.steps.strip():
        steps = [step.strip() for step in item.steps.split("|") if step.strip()]
        parts.append("\n\nПорядок действий:\n" + "\n".join(f"{index}. {step}" for index, step in enumerate(steps, 1)))
    if item.contact.strip():
        parts.append(f"\n\nЕсли возникнет проблема: {item.contact}.")
    parts.append(f"\n\nИсточник: {item.category}, актуально на {item.updated_at}.")
    return "".join(parts)


def llm_answer(message: str, matches: list[KnowledgeItem]) -> str | None:
    if not os.getenv("OPENAI_API_KEY"):
        return None
    from openai import OpenAI

    context = "\n\n".join(
        f"ID: {item.id}\nРаздел: {item.category}\nВопрос: {item.question}\n"
        f"Ответ: {item.answer}\nШаги: {item.steps}\nКонтакт: {item.contact}\n"
        f"Актуально: {item.updated_at}"
        for item in matches
    )
    instructions = PROMPT_FILE.read_text(encoding="utf-8")
    client = OpenAI()
    response = client.responses.create(
        model=os.getenv("OPENAI_MODEL", "gpt-5.6-luna"),
        instructions=instructions,
        input=f"ВОПРОС СОТРУДНИКА:\n{message}\n\nРАЗРЕШЁННЫЙ КОНТЕКСТ:\n{context}",
    )
    return response.output_text.strip()


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health() -> dict[str, str | int | bool]:
    return {
        "status": "ok",
        "knowledge_items": len(KNOWLEDGE),
        "openai_enabled": bool(os.getenv("OPENAI_API_KEY")),
    }


@app.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    department = sensitive_route(payload.message)
    if department:
        return ChatResponse(
            answer=(
                "Этот вопрос требует участия профильного специалиста. "
                "Я не принимаю кадровые решения, не раскрываю персональные данные и не даю юридических заключений. "
                f"Передайте запрос в отдел «{department}» через внутренний канал поддержки."
            ),
            status="escalated",
            escalation=True,
            department=department,
            mode="safety-route",
        )

    matches = retrieve(payload.message)
    if not matches:
        return ChatResponse(
            answer=(
                "В базе знаний нет подтверждённой информации по этому вопросу. "
                "Чтобы избежать ошибки, обратитесь к HR-наставнику через внутренний канал поддержки."
            ),
            status="not_found",
            escalation=True,
            department="HR",
            mode="knowledge-fallback",
        )

    answer = llm_answer(payload.message, matches) or format_demo_answer(matches[0])
    return ChatResponse(
        answer=answer,
        status="answered",
        escalation=False,
        sources=[
            Source(id=item.id, category=item.category, title=item.question, updated_at=item.updated_at)
            for item in matches
        ],
        mode="openai" if os.getenv("OPENAI_API_KEY") else "demo",
    )


@app.get("/api/checklists")
def checklists() -> dict[str, list[dict[str, str]]]:
    result: dict[str, list[dict[str, str]]] = {"Первый день": [], "Первая неделя": [], "Первый месяц": []}
    for item in KNOWLEDGE:
        if item.category in result:
            result[item.category].append({"id": item.id, "task": item.answer})
    return result
