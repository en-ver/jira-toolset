from pydantic import BaseModel


class ToolConfig(BaseModel):
    name: str
    active: bool
    tasks: list[dict]
