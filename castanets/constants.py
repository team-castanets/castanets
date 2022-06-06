import os

from dotenv import load_dotenv

load_dotenv()


def check_and_load(key: str) -> str:
    """
    Check if key exists in environment variables.
    If not, raise error.

    :param key: Enviroment variable name
    :returns: Value of environment variable
    """
    if key in os.environ:
        return os.environ[key]
    else:
        raise Exception(f"{key} is not set")


def boolean_str_to_bool(value: str) -> bool:
    """
    Get string of true or false, return into boolean value.
    """
    return value and value.lower() == "true"


#: Github Actions
GITHUB_EVENT_NAME = check_and_load("GITHUB_EVENT_NAME")
GITHUB_EVENT_PATH = check_and_load("GITHUB_EVENT_PATH")
GITHUB_WORKSPACE = check_and_load("GITHUB_WORKSPACE")
GITHUB_TOKEN = check_and_load("GITHUB_TOKEN")
GITHUB_REPOSITORY = check_and_load("GITHUB_REPOSITORY")
GITHUB_REF_NAME = check_and_load("GITHUB_REF_NAME")

#: Castanets
CASTANETS_CONFIG_PATH = check_and_load("CASTANETS_CONFIG_PATH")
ISSUE_AUTOCLOSE = boolean_str_to_bool(check_and_load("ISSUE_AUTOCLOSE"))

#: Slack
SLACK = boolean_str_to_bool(check_and_load("SLACK"))
SLACK_TOKEN = check_and_load("SLACK_TOKEN") if SLACK else None
SLACK_CHANNEL = check_and_load("SLACK_CHANNEL") if SLACK else None

#: Others
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
