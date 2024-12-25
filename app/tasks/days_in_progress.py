from datetime import datetime
import logging, time

from jira2py import Jira

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(levelname)s: %(message)s"  # Exclude the logger name
)


class DaysInProgress:

    def __init__(self, task_config: dict, jira: Jira):

        self._jira = jira
        self._jira_fields = jira.fields().get()
        self._search = jira.search()
        self._issue = jira.issue()

        self._config = self._add_field_ids_to_config(task_config)

    def _add_field_ids_to_config(self, config: dict) -> dict:

        for item in config["mapping"]:
            item["field_id"] = self._get_jira_field_id(item["field_name"])

        return config

    def _get_jira_field_id(self, field_name: str) -> str:

        return next(
            field["id"] for field in self._jira_fields if field["name"] == field_name
        )

    # Define a function to extract the datetime object from the string
    def _get_datetime(date_str) -> datetime:

        return datetime.strptime(date_str, "%Y-%m-%d %H:%M")

    def _get_changelog(self, issue: dict, field_name: str | None = None) -> list:

        if issue["changelog"]["maxResults"] == issue["changelog"]["total"]:
            full_changelog = issue["changelog"]["histories"]
        else:
            pass
            full_changelog = []
            start_at = 0
            max_results = 100
            is_last = False

            while is_last == False:

                changelog = self._jira.issue().get_changelogs(
                    key=issue["key"], start_at=start_at, max_results=max_results
                )

                full_changelog += changelog["values"]
                start_at += max_results
                is_last = changelog.get("isLast", True)

        sorted_changelog = sorted(
            full_changelog,
            key=lambda x: datetime.strptime(x["created"], "%Y-%m-%dT%H:%M:%S.%f%z"),
        )

        filtered_changelog = [
            {
                "field": item["field"],
                "from": item["fromString"],
                "to": item["toString"],
                "date": change["created"],
            }
            for change in sorted_changelog
            for item in change["items"]
            if item["field"] == field_name or not field_name
        ]

        return filtered_changelog

    def _convert_seconds_to_days(self, seconds) -> float:

        days = seconds / 86400  # Convert seconds to days
        if days < 1:
            duration = round(days, 1)  # Float for < 1 day
        elif days < 5:
            duration = round(days * 2) / 2  # Round to nearest 0.5 for < 5 days
        else:
            duration = round(days)  # Integer for >= 5 days

        # return Decimal(duration).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
        rounded = f"{duration:.1f}"
        return float(rounded)

    def _calculate_duration(self, curr, prev) -> int:

        # Format of the timestamp
        timestamp_format = "%Y-%m-%dT%H:%M:%S.%f%z"

        # Calculate the duration
        duration = datetime.strptime(curr, timestamp_format) - datetime.strptime(
            prev, timestamp_format
        )

        return duration.total_seconds()

    def _get_fields_payload(self, changelog: dict, issue: dict) -> dict:

        payload = {}

        for item in self._config["mapping"]:
            duration = 0
            field_id = item["field_id"]
            for prev, curr in zip(changelog, changelog[1:]):
                if curr["from"] in item["statuses"]:
                    duration += self._calculate_duration(curr["date"], prev["date"])
            duration = self._convert_seconds_to_days(duration)
            duration = duration if duration > 0 else None
            if duration != issue["fields"][field_id]:
                payload[field_id] = duration

        return payload

    @property
    def _jql(self) -> str:

        return self._config["jql"]

    @property
    def _fields_to_update(self) -> list[str]:

        return [item["field_id"] for item in self._config["mapping"]]

    def run(self) -> None:

        search = {}

        while True:

            # Get the search results page
            next_page_token = search.get("nextPageToken", None)
            if not next_page_token and search:
                break

            search = self._search.jql(
                jql=self._jql,
                next_page_token=next_page_token,
                fields=self._fields_to_update,
                expand="names,changelog",
            )

            # For every issue in search results page get the payload and udit the issue
            # for issue in tqdm(search["issues"], desc="Processing Issues", unit="issue"):
            for issue in search["issues"]:
                changelog = self._get_changelog(issue, "status")
                fields_payload = self._get_fields_payload(changelog, issue)
                if fields_payload:
                    self._issue.edit(key=issue["key"], fields=fields_payload)
                    logging.info(f"{issue['key']}: {fields_payload}")
                    # If the issue has been edited, wait for 1 sec to respect the Atlassian API limits
                    time.sleep(1)
