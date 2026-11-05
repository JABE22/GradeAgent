import ast
import re

from ..rubric import Criterion
from .base import CriterionResult, GradingEngine


class HeuristicEngine(GradingEngine):
    """Dependency-free baseline so the app works without any model."""

    name = "heuristic"

    def grade(self, code, text, rubric):
        try:
            tree = ast.parse(code)
            syntax_ok = True
        except SyntaxError:
            tree, syntax_ok = None, False
        lines = [l for l in code.splitlines() if l.strip()]
        funcs = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.ClassDef))] if tree else []
        comments = sum(1 for l in lines if l.strip().startswith("#"))
        docstrings = sum(1 for n in funcs if ast.get_docstring(n))
        markdown = max(len(text) - len(code), 0)
        long_lines = sum(1 for l in lines if len(l) > 100)
        analysis_hits = len(re.findall(r"plt\.|\.plot|accuracy|score|metric|confusion|print\(|conclusion", text, re.I))

        ratios = {
            "Correctness": (0.0 if not syntax_ok else min(1.0, 0.5 + len(lines) / 40), "Syntax error." if not syntax_ok else f"{len(lines)} code lines parse correctly."),
            "Code quality": (0 if not lines else max(0.0, min(1.0, 0.4 + 0.15 * len(funcs) - long_lines / len(lines))), f"{len(funcs)} functions/classes, {long_lines} long lines."),
            "Documentation": (min(1.0, comments / 5 * 0.5 + docstrings * 0.2 + min(markdown, 600) / 600 * 0.5), f"{comments} comments, {docstrings} docstrings, {markdown} chars of prose."),
            "Analysis": (min(1.0, analysis_hits / 5), f"{analysis_hits} evaluation/visualisation markers."),
        }
        results = []
        for c in rubric:
            ratio, fb = ratios.get(c.name, (0.5, "Not assessed by heuristic engine."))
            results.append(CriterionResult(c.name, round(ratio * c.max_score, 1), c.max_score, fb))
        return results
