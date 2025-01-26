import json
from pathlib import Path
from typing import Any

import arrow
import requests
from arrow import Arrow
from ics import Calendar

from objects import Assignment
from trello_manager import TrelloManager


def print_courses(courses: list[str]) -> None:
    print('Available courses:')
    for i, course in enumerate(courses, 1):
        print(f'\t{i} - {course}')


def request_course_for_assignment(course_options: list[str], assignment: str) -> str:
    all_course_choices = range(1, len(course_options) + 1)

    def validate_choice(input_str: str) -> int | None:
        try:
            i = int(input_str)
        except ValueError:
            return None
        else:
            return i if i in all_course_choices else None

    print_courses(course_options)
    while (choice := validate_choice(input(f'What course belongs to "{assignment}"?'))) is None:
        print(f'Invalid choice. Please enter a number between 1 and {len(course_options)}.')

    return course_options[choice - 1]


def ics_to_assignments(ics_url: str, start_date: Arrow) -> list[Assignment]:
    response = requests.get(ics_url)
    calendar = Calendar(response.text)
    return [
        Assignment(
            title=ics_event.name,
            course=None,
            due=ics_event.end
        )
        for ics_event in calendar.timeline.start_after(start_date)
    ]


def main() -> None:
    # check if config is available
    if not (config_path := Path('config.json')).exists():
        raise FileNotFoundError('No config file exists. Please create one using the template "config.json.template"')

    # extract config data
    config: dict[str, Any] = json.loads(config_path.read_bytes())
    ics_url = config['ics_url']
    start_date = arrow.get(config['start_date'], 'MM-DD-YYYY')
    courses: list[str] = config['course_names']

    # convert ics events to assignments
    print('Getting ICS events...', end='', flush=True)
    assignments = ics_to_assignments(ics_url, start_date)
    print('Done.\n')

    # set up the trello manager
    trello_manager = TrelloManager('School', 'Backlog', courses)

    # iterate over each event and ask for course assignment. then, add to trello
    # ONLY IF it does not already exist
    for i, assignment in enumerate(assignments, 1):
        if assignment.title in trello_manager.existing_card_names:
            if assignment.due_date_string() != trello_manager.existing_card_names[assignment.title]:
                trello_manager.update_assignment_card(assignment)
                print(f'Updating assignment ({i}/{len(assignments)}): {assignment.title} (new due date)')
            else:
                print(f'Skipping assignment ({i}/{len(assignments)}): {assignment.title} (already exists in Trello)')
            continue

        assignment.course = request_course_for_assignment(courses, assignment.title)
        trello_manager.add_assignment_card(assignment)
        print(f'Added assignment ({i}/{len(assignments)}): {assignment.title}\n')
    print()

    # once done, sort the list by due date
    print('Sorting assignments by due date...', end='', flush=True)
    trello_manager.sort_list()
    print('Done.')


if __name__ == '__main__':
    main()
