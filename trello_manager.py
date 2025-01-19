import math
import random
from operator import itemgetter
from typing import Any

import requests

from objects import Assignment
from secrets import secrets

LABEL_COLORS = [
    "green",
    "yellow",
    "orange",
    "red",
    "purple",
    "blue",
    "sky",
    "lime",
    "pink",
    "black",
    "green_dark",
    "yellow_dark",
    "orange_dark",
    "red_dark",
    "purple_dark",
    "blue_dark",
    "sky_dark",
    "lime_dark",
    "pink_dark",
    "black_dark",
    "green_light",
    "yellow_light",
    "orange_light",
    "red_light",
    "purple_light",
    "blue_light",
    "sky_light",
    "lime_light",
    "pink_light",
    "black_light"
]


class TrelloManager:
    def __init__(self, board_name: str, list_name: str, courses: list[str]):
        self._base_url = 'https://api.trello.com/1'
        self._base_headers = {'Accept': 'application/json'}
        self._base_query = {'key': secrets['api_key'], 'token': secrets['token']}
        self._session = requests.Session()

        self.active_board_id: str | None = None
        self.register_board_id(board_name)

        self.active_list_id: str | None = None
        self.register_list_id(list_name)

        self.course_label_ids: dict[str, str] | None = None
        self.register_course_label_ids(courses)

    def _get_request(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any] | list[
        dict[str, Any]]:
        url = f'{self._base_url}/{endpoint}'
        new_params = {**self._base_query, **params} if params else self._base_query
        response = self._session.get(url, headers=self._base_headers, params=new_params)
        if response.status_code == 200:
            return response.json()
        else:
            raise requests.exceptions.HTTPError(response.status_code, response.text)

    def _post_request(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any] | list[dict[str, Any]]:
        url = f'{self._base_url}/{endpoint}'
        body = {**self._base_query, **params}
        response = self._session.post(url, headers=self._base_headers, json=body)
        if response.status_code == 200:
            return response.json()
        else:
            raise requests.exceptions.HTTPError(response.status_code, response.text)

    def register_board_id(self, board_name: str) -> None:
        boards = self._get_request('members/me/boards', {'fields': 'name'})
        for board in boards:
            if board['name'] == board_name:
                self.active_board_id = board['id']
                break
        else:
            raise ValueError(f'{board_name} board not found')

    def register_list_id(self, list_name: str) -> None:
        lists = self._get_request(f'boards/{self.active_board_id}/lists', {'fields': 'name'})
        for list_ in lists:
            if list_['name'] == list_name:
                self.active_list_id = list_['id']
                break
        else:
            raise ValueError(f'{list_name} list not found')

    def register_course_label_ids(self, courses: list[str]) -> None:
        # first, filter out the label names that already exist in Trello
        existing_labels = self._get_request(f'boards/{self.active_board_id}/labels', {'fields': 'name,color'})
        courses_to_add = [course for course in courses if course not in map(itemgetter('name'), existing_labels)]

        # find all available colors (colors not already in use)
        existing_color_names = set(label['color'] for label in existing_labels)
        available_colors = [color for color in LABEL_COLORS if color not in existing_color_names]

        # if there are fewer labels than courses, fill in with random colors
        courses_overflow = max(0, len(courses) - len(available_colors))
        for _ in range(math.ceil(courses_overflow / len(LABEL_COLORS))):
            available_colors += LABEL_COLORS[:courses_overflow % len(LABEL_COLORS)]

        # add all labels that don't exist
        for course_name in courses_to_add:
            label_color = random.choice(available_colors)
            available_colors.remove(label_color)
            self._post_request(f'boards/{self.active_board_id}/labels', {'name': course_name, 'color': label_color})

        # finally, get all label ids for the courses
        all_labels = self._get_request(f'boards/{self.active_board_id}/labels', {'fields': 'name'})
        self.course_label_ids = {label['name']: label['id'] for label in all_labels if label['name'] in courses}

    def add_assignment_card(self, assignment: Assignment) -> None:
        params = {
            'idList': self.active_list_id,
            'name': assignment.title,
            'due': assignment.due.to('UTC').isoformat().replace('+00:00', 'Z'),
            'idLabels': self.course_label_ids[assignment.course],
            'pos': 'bottom'
        }
        self._post_request('cards', params)


if __name__ == '__main__':
    tm = TrelloManager(
        'School',
        'Backlog',
        ['ITEC 301', 'ITEC 447', 'CSCE 146 HN', 'ITEC 445', 'ECON 224 HN', 'ITEC 444']
    )
