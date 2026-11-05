from abc import ABC, abstractmethod
from dataclasses import dataclass

from ..rubric import Criterion


@dataclass
class CriterionResult:
    name: str
    score: float
    max_score: float
    feedback: str = ""


class GradingEngine(ABC):
    """Implement ``grade`` to plug in any model and register it in ``engines/__init__.py``."""

    name: str

    @abstractmethod
    def grade(self, code: str, text: str, rubric: list[Criterion]) -> list[CriterionResult]:
        """Return one result per rubric criterion."""
