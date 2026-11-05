"""Open-source LLM engine served locally by Ollama (https://ollama.com).

Example: ``ollama pull qwen2.5-coder:7b`` then ``GRADEAGENT_ENGINE=ollama``.
"""
import json
import os

import httpx

from .base import CriterionResult, GradingEngine

PROMPT = """You are a strict but fair teaching assistant grading a Python / Jupyter submission.
Grade each rubric criterion. Reply ONLY with JSON: {{"criteria": [{{"name": str, "score": number, "feedback": str}}]}}

Rubric:
{rubric}

Submission:
{submission}
"""


class OllamaEngine(GradingEngine):
    name = "ollama"

    def __init__(self):
        self.url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")

    def grade(self, code, text, rubric):
        rubric_txt = "\n".join(f"- {c.name} (0-{c.max_score:g}): {c.description}" for c in rubric)
        resp = httpx.post(
            f"{self.url}/api/generate",
            json={"model": self.model, "prompt": PROMPT.format(rubric=rubric_txt, submission=text[:20000]), "format": "json", "stream": False},
            timeout=300,
        )
        resp.raise_for_status()
        data = json.loads(resp.json()["response"])
        by_name = {d.get("name"): d for d in data.get("criteria", [])}
        results = []
        for c in rubric:
            d = by_name.get(c.name, {})
            try:
                score = float(d.get("score", 0))
            except (TypeError, ValueError):
                score = 0.0
            results.append(CriterionResult(c.name, max(0.0, min(score, c.max_score)), c.max_score, str(d.get("feedback", ""))))
        return results
