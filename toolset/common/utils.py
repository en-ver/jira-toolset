from jira2py import Jira
from dotenv import load_dotenv
import os, json
from pydantic import validate_call


@validate_call
def get_config(conf_file: str | None = "config.json") -> dict:

    if not os.path.exists(conf_file):
        raise FileNotFoundError(f"The configuration file '{conf_file}' does not exist.")

    with open(conf_file, "r") as f:
        return json.load(f)


@validate_call
def get_jira(env_file: str | None = ".env") -> Jira:

    if not os.path.exists(env_file):
        raise FileNotFoundError(
            "The {env_file} file is missing. Please create it with the required variables."
        )

    load_dotenv(dotenv_path=env_file)
    return Jira(
        jira_url=os.getenv("JIRA_URL"),
        jira_user=os.getenv("JIRA_USER"),
        jira_api_token=os.getenv("JIRA_API_TOKEN"),
    )
