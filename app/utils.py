import json, os
from dotenv import load_dotenv
from jira2py import Jira


def load_config(path_to_config: str) -> dict:
    with open(path_to_config, "r") as data:
        return json.load(data)


def load_jira():

    load_dotenv()

    return Jira(
        url=os.getenv("JIRA_URL", ""),
        user=os.getenv("JIRA_USER", ""),
        api_token=os.getenv("JIRA_API_TOKEN", ""),
    )
