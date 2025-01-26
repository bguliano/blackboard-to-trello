from dataclasses import dataclass

from arrow import Arrow


@dataclass
class Assignment:
    title: str
    course: str | None
    due: Arrow

    def due_date_string(self) -> str:
        return self.due.to('UTC').isoformat(timespec='milliseconds').replace('+00:00', 'Z')
