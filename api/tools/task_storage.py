import asyncio
from asyncio import Task


class TaskStorage:
    task_storage: dict[int: Task] = {}