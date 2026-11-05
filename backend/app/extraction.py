"""Extract code and metadata (student, group, course, workshop) from uploads.

Metadata is read from "Key: value" lines in the header of the file (first
markdown cell / leading comments), falling back to the file name
``course_workshop_group_student.ext`` and finally to defaults.
"""
import json
import os
import re
from dataclasses import dataclass

FIELDS = {
    "student": "student", "name": "student", "author": "student",
    "group": "group", "class": "group",
    "course": "course", "subject": "course",
    "workshop": "workshop", "lab": "workshop", "assignment": "workshop",
}
_LINE = re.compile(r"^[\s#>*_-]*\**(\w+)\**\s*[:=]\s*\**\s*(.+?)\s*\**\s*$")


@dataclass
class Extracted:
    code: str
    text: str  # code + markdown, as shown to the grader
    student: str = ""
    group: str = ""
    course: str = ""
    workshop: str = ""


def _parse_notebook(raw: str):
    nb = json.loads(raw)
    code, text, header = [], [], []
    for i, cell in enumerate(nb.get("cells", [])):
        src = cell.get("source", "")
        src = "".join(src) if isinstance(src, list) else src
        if i < 3:
            header.append(src)
        if cell.get("cell_type") == "code":
            code.append(src)
            text.append("```python\n" + src + "\n```")
        else:
            text.append(src)
    return "\n\n".join(code), "\n\n".join(text), "\n".join(header)


def extract(filename: str, raw: bytes) -> Extracted:
    decoded = raw.decode("utf-8", errors="replace")
    if filename.lower().endswith(".ipynb"):
        try:
            code, text, header = _parse_notebook(decoded)
        except (ValueError, AttributeError) as exc:
            raise ValueError(f"Invalid notebook: {exc}") from exc
    elif filename.lower().endswith(".py"):
        code = text = header = decoded
        header = "\n".join(decoded.splitlines()[:30])
    else:
        raise ValueError("Only .ipynb and .py files are supported")

    result = Extracted(code=code, text=text)
    for line in header.splitlines():
        m = _LINE.match(line)
        if m and m.group(1).lower() in FIELDS:
            attr = FIELDS[m.group(1).lower()]
            if not getattr(result, attr):
                setattr(result, attr, m.group(2).strip())

    parts = os.path.splitext(os.path.basename(filename))[0].split("_")
    if len(parts) >= 4:
        for attr, value in zip(("course", "workshop", "group", "student"), parts):
            if not getattr(result, attr):
                setattr(result, attr, " ".join(parts[3:]) if attr == "student" else value)
    return result


def normalise_name(name: str) -> str:
    """Case/spacing/punctuation-insensitive and order-insensitive key for matching students."""
    words = re.findall(r"\w+", name.lower().replace(",", " "))
    return " ".join(sorted(words))
