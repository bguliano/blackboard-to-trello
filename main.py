from operator import attrgetter

import arrow
import requests
from arrow import Arrow
from ics import Calendar

from objects import Assignment
from trello_manager import TrelloManager


def request_course_names() -> list[str]:
    courses = []
    while (inpt := input('Enter course name (or "done" to finish): ')) != 'done':
        courses.append(inpt.upper())
    return courses


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
    raw = [
        Assignment(
            title=ics_event.name,
            course=None,
            due=ics_event.end
        )
        for ics_event in calendar.events
        if ics_event.end > start_date
    ]
    return sorted(raw, key=attrgetter('due'))


def main() -> None:
    # first, request courses
    courses = request_course_names()
    print()

    # next, request ics url
    ics_url = input('Enter ICS URL: ')

    # next, request start date for courses in this semester
    str_date = input('Enter semester start date (MM-DD-YYYY): ')
    start_date = arrow.get(str_date, 'MM-DD-YYYY')
    print()

    # convert ics events to assignments
    print('Getting ICS events...', end='', flush=True)
    assignments = ics_to_assignments(ics_url, start_date)
    print('Done.\n')

    # set up the trello manager
    trello_manager = TrelloManager('School', 'Backlog', courses)

    # iterate over each event and ask for course assignment. then, add to trello
    for i, assignment in enumerate(assignments, 1):
        assignment.course = request_course_for_assignment(courses, assignment.title)
        trello_manager.add_assignment_card(assignment)
        print(f'Added assignment ({i}/{len(assignments)}): {assignment.title}\n')


if __name__ == '__main__':
    main()
