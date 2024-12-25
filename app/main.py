from tasks import DaysInProgress
from utils import load_config, load_jira
import time

config = load_config("config.json")
jira = load_jira()


def main():

    while True:

        for task_config in config:

            delay = task_config.get("delay", 3600)
            task_name = task_config.get("name", None)
            task_status = task_config.get("status", "off")

            if task_name == "days_in_progress" and task_status == "on":
                days_in_progress = DaysInProgress(task_config, jira)
                days_in_progress.run()
                time.sleep(int(delay))


if __name__ == "__main__":
    main()
