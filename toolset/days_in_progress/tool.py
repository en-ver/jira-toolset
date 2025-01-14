from datetime import datetime, timedelta
import logging, time
from pydantic import validate_call

from common import get_jira

from .models import TaskConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(levelname)s: %(message)s"  # Exclude the logger name
)


class DaysInProgress:

    def __init__(self, task: dict):

        self.jira = get_jira(env_file="./config/.env")  # create jira instance
        self.task = TaskConfig(**task)
        self.add_field_ids()  # add field ids if they are not set

    def add_field_ids(self) -> None:
        """
        Checks if only field names are defined in config, add corresponding ids
        """

        for field in [field for field in self.task.fields if not field.id]:
            field_id = self.jira.fields().get_field_id(field_names=[field.name])
            field.id = "".join(field_id)

    @property
    def list_field_ids(self) -> list[str]:

        return [field.id for field in self.task.fields] + [
            "status",
            "key",
        ]

    @validate_call
    def is_search_changelog_full(self, issue: dict) -> bool:

        return issue["changelog"]["maxResults"] == issue["changelog"]["total"]

    @validate_call
    def get_changelog(self, issue: dict, field: str) -> list[dict]:

        # Keep the search results changelog or load the full changelog
        if self.is_search_changelog_full(issue=issue):
            changelog = issue["changelog"]["histories"]
        else:
            changelog = self.jira.issue(id_key=issue["key"]).changelog_all_pages()

        # Filter and flatten the changelog
        changelog = [
            {"created": change["created"], **item}
            for change in changelog
            for item in change["items"]
            if item["field"] == field
        ]

        changelog = sorted(
            changelog, key=lambda x: datetime.fromisoformat(x["created"])
        )

        return changelog

    @validate_call
    def calculate_duration(
        self, changelog: list[dict], focus_statuses: list[str]
    ) -> float | None:

        timestamp_format = "%Y-%m-%dT%H:%M:%S.%f%z"
        duration = timedelta(seconds=0)

        for prev, curr in zip(changelog, changelog[1:]):
            if curr["fromString"] in focus_statuses:
                duration += datetime.strptime(
                    curr["created"], timestamp_format
                ) - datetime.strptime(prev["created"], timestamp_format)

        days_duration = duration.total_seconds() / 86400  # Convert seconds to days
        if days_duration < 1:
            rounded_days = round(days_duration, 1)  # Float for < 1 day
        elif days_duration < 5:
            rounded_days = (
                round(days_duration * 2) / 2
            )  # Round to nearest 0.5 for < 5 days
        else:
            rounded_days = round(days_duration)  # Round to integer for >= 5 days

        days_str = f"{rounded_days:.1f}"
        rounded = float(days_str)

        return rounded if rounded > 0 else None

    @validate_call
    def get_fields_payload(
        self, issue: dict, changelog: list[dict], task: TaskConfig
    ) -> dict[str, float]:
        """
        Returns the fields payload json used later for the issue fields update
        """
        # Get the issue current status
        curr_status = issue["fields"]["status"]["name"]
        payload = {}

        for field in task.fields:
            focus_statuses = [
                status for status in field.statuses if status != curr_status
            ]
            duration = self.calculate_duration(
                changelog=changelog, focus_statuses=focus_statuses
            )

            if duration != issue["fields"][field.id]:
                payload[field.id] = duration

        return payload

    def run(self) -> None:

        while True:

            search_results_json = self.jira.jql(jql=self.task.jql).get_all_pages(
                fields=self.list_field_ids, expand="names,changelog"
            )

            for issue in search_results_json["issues"]:

                changelog = self.get_changelog(
                    issue=issue,
                    field="status",
                )
                fields_payload = self.get_fields_payload(
                    issue=issue, changelog=changelog, task=self.task
                )
                if fields_payload:

                    self.jira.issue(id_key=issue["id"]).edit(fields=fields_payload)
                    logging.info(f"{issue['key']}: {fields_payload}")
                    # Issue has been edited, wait for 1 sec to respect the Atlassian API limits
                    time.sleep(1)

            # Delay section
            seconds = self.task.delay.total_seconds()
            print(f"Sleeping for {self.task.delay} ...")
            time.sleep(seconds)
            print("Delay completed!")
