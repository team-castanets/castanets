from typing import Optional

import requests

from castanets.models import GithubActionsContext
from castanets.utils import embed_state_to_comment, get_castanets_params_from_comment, get_castanets_state_from_comment


def _base_api_call(
    context: GithubActionsContext, endpoint: str, method: str, payload: Optional[dict] = None, no_repo: bool = False
):
    """
    Call a GitHub API

    :param context: Context of Github Actions
    :param endpoint: Github API Endpoint
    :param method: Github API Method
    :param payload: Github API Payload
    :param no_repo: If True, do not include repository in the URL
    :return: Github API Response
    """
    headers = {
        "Authorization": f"token {context.token}",
        "Content-Type": "application/json",
        "Accept": "application/vnd.github.v3+json",
    }

    if no_repo:
        url = f"https://api.github.com/{endpoint}"
    else:
        url = f"https://api.github.com/repos/{context.repo}/{endpoint}"

    if method == "POST":
        response = requests.post(url, headers=headers, json=payload)
    elif method == "GET":
        response = requests.get(url, headers=headers)
    elif method == "PATCH":
        response = requests.patch(url, headers=headers, json=payload)
    elif method == "DELETE":
        response = requests.delete(url, headers=headers)
    else:
        raise ValueError(f"Invalid Method: {method}")

    if not response.ok:
        raise Exception(f"Github API Call on {method} /{endpoint} Failed. {response.status_code}: {response.text}")

    if "Content-Type" in response.headers and "application/json" in response.headers["Content-Type"]:
        result = response.json()
    else:
        result = response.text

    return result


def get_user(context: GithubActionsContext):
    """
    Return the user authenticated by the token.

    :param context: Context of Github Actions
    """
    return _base_api_call(context=context, endpoint="user", method="GET", no_repo=True)


def run_workflow(context: GithubActionsContext, workflow: str, inputs: Optional[dict] = None):
    """
    Run a GitHub workflow.

    :param context: Context of Github Actions
    :param workflow: Github Workflow File Name or ID
    :param inputs: Github Workflow Inputs
    :return: Github Workflow Response
    """
    payload = {"ref": context.ref}
    if inputs is not None:
        payload["inputs"] = inputs

    return _base_api_call(
        context=context,
        endpoint=f"actions/workflows/{workflow}/dispatches",
        method="POST",
        payload=payload,
    )


def comment(context: GithubActionsContext, message: str):
    """
    Write a GitHub issue comment.

    :param context: Context of Github Actions
    :param message: Comment message
    """
    return _base_api_call(
        context=context,
        endpoint=f"issues/{context.issue_id}/comments",
        method="POST",
        payload={"body": message},
    )


def get_comments(context: GithubActionsContext):
    """
    Get all issues from GitHub Actions.

    :param context: Context of Github Actions
    """
    return _base_api_call(
        context=context,
        endpoint=f"issues/{context.issue_id}/comments",
        method="GET",
    )


def update_comment(context: GithubActionsContext, comment_id: str, message: str):
    """
    Write a comment to GitHub Issue.

    :param context: Context of Github Actions
    :param comment_id: Comment ID to update
    :param message: Comment message
    """
    return _base_api_call(
        context=context,
        endpoint=f"issues/comments/{comment_id}",
        method="PATCH",
        payload={"body": message},
    )


def _get_first_comment_from_action_user(context: GithubActionsContext):
    """
    Get first GitHub issue comment written by Castanets

    :param context: Context of Github Actions
    """
    action_user = get_user(context=context)
    comments = get_comments(context=context)
    for comment in comments:
        if comment["user"]["id"] == action_user["id"]:
            return comment
    return None


def read_state_from_first_comment(context: GithubActionsContext):
    """
    Get state from issue comment written by Castanets.

    :param context: Context of Github Actions
    """
    comment = _get_first_comment_from_action_user(context=context)
    if comment is None:
        return {}
    state = get_castanets_state_from_comment(comment["body"]) if comment else {}
    return state


def write_state_to_first_comment(context: GithubActionsContext, state: dict):
    """
    Write state to issue comment written by Castanets.

    :param context: Context of Github Actions
    :param state: State
    """
    comment = _get_first_comment_from_action_user(context=context)
    if comment is None:
        raise Exception("No Comment Found")
    state_embedded_comment = embed_state_to_comment(comment["body"], state)
    return update_comment(context, comment["id"], state_embedded_comment)


def get_issue(context: GithubActionsContext):
    """
    Get a GitHub issue.

    :param context: Context of Github Actions
    """
    return _base_api_call(
        context=context,
        endpoint=f"issues/{context.issue_id}",
        method="GET",
    )


def update_issue(context: GithubActionsContext, payload: dict):
    """
    Update a GitHub issue.

    :param context: Context of Github Actions
    """
    return _base_api_call(context=context, endpoint=f"issues/{context.issue_id}", method="PATCH", payload=payload)


def read_params_from_issue_body(context: GithubActionsContext):
    """
    Get parameters from issue body.

    :param context: Context of Github Actions
    """
    issue = get_issue(context=context)
    return get_castanets_params_from_comment(issue["body"]) if issue else {}


def set_label(context: GithubActionsContext, label: str):
    """
    Set a Github Label

    :param context: Context of Github Actions
    :param label: Github Label
    """
    return _base_api_call(
        context=context,
        endpoint=f"issues/{context.issue_id}/labels",
        method="POST",
        payload={"labels": [label]},
    )


def remove_label(context: GithubActionsContext, label: str):
    """
    Remove a Github Label

    :param context: Context of Github Actions
    :param label: Github Label
    """
    return _base_api_call(
        context=context,
        endpoint=f"issues/{context.issue_id}/labels/{label}",
        method="DELETE",
    )
