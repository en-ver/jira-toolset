from datetime import timedelta
from pydantic import BaseModel


class TaskFields(BaseModel):
    id: str
    name: str
    statuses: list[str]


class TaskConfig(BaseModel):
    delay: timedelta
    jql: str
    fields: list[TaskFields]
