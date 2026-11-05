import os

from .base import GradingEngine
from .heuristic import HeuristicEngine
from .ollama import OllamaEngine

ENGINES = {"heuristic": HeuristicEngine, "ollama": OllamaEngine}


def get_engine(name: str | None = None) -> GradingEngine:
    name = name or os.getenv("GRADEAGENT_ENGINE", "heuristic")
    if name not in ENGINES:
        raise ValueError(f"Unknown engine '{name}'. Available: {', '.join(ENGINES)}")
    return ENGINES[name]()
