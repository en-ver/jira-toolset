from common import get_config
from common.models import ToolConfig
from days_in_progress import DaysInProgress


def get_active_tools() -> list[ToolConfig]:

    config_json = get_config(conf_file="./config/config.json")

    return [
        tool
        for tool in [ToolConfig(**tool_json) for tool_json in config_json]
        if tool.active
    ]


def main():

    active_tools = get_active_tools()

    for tool in active_tools:
        if tool.name == "days_in_progress":
            for task in tool.tasks:
                DaysInProgress(task=task).run()


if __name__ == "__main__":

    main()
