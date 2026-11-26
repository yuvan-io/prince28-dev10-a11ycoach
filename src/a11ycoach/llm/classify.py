"""Route a question before answering it."""

import re

from a11ycoach.llm.gateway import LLMGateway, LLMResult

LABELS = ("docs", "personal", "off_topic")


def build_messages(prompt: str, question: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": prompt},
        {
            "role": "user",
            "content": f"<question>\n{question.strip()}\n</question>",
        },
    ]


def parse_label(reply: str, labels: tuple[str, ...] = LABELS) -> str:
    text = re.sub(r"off[\s-]+topic", "off_topic", reply.lower())
    found = {label for label in labels if re.search(rf"(?<![a-z_]){label}(?![a-z_])", text)}
    return found.pop() if len(found) == 1 else "invalid"


async def classify(
    gateway: LLMGateway,
    prompt: str,
    version: str,
    question: str,
) -> tuple[str, LLMResult]:
    result = await gateway.generate(
        build_messages(prompt, question),
        purpose="classify",
        prompt_version=version,
        temperature=0,
    )
    return parse_label(result.text), result


def accuracy(rows: list[dict]) -> float:
    return sum(row["got"] == row["label"] for row in rows) / len(rows) if rows else 0.0


def find_leaks(prompt: str, questions: list[str]) -> list[str]:
    text = " ".join(prompt.lower().split())
    return [q for q in questions if " ".join(q.lower().split()) in text]
