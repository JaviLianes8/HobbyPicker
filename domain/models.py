"""Simple domain models used by the application."""

from dataclasses import dataclass


@dataclass
class Activity:
    """A hobby or activity stored in the database."""

    id: int
    name: str
    done: int = 0
    accepted_count: int = 0


@dataclass
class SubItem:
    """A specific subitem belonging to an ``Activity``."""

    id: int
    activity_id: int
    name: str
