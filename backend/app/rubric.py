from dataclasses import dataclass


@dataclass(frozen=True)
class Criterion:
    name: str
    description: str
    max_score: float


DEFAULT_RUBRIC = [
    Criterion("Correctness", "Code is syntactically valid, complete and solves the task.", 40),
    Criterion("Code quality", "Readable structure, functions, naming, no excessive duplication.", 20),
    Criterion("Documentation", "Comments, docstrings and explanatory markdown.", 20),
    Criterion("Analysis", "Results are evaluated, visualised and interpreted.", 20),
]
