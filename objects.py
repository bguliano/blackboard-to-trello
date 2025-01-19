from dataclasses import dataclass

from arrow import Arrow


@dataclass
class Assignment:
    title: str
    course: str | None
    due: Arrow
