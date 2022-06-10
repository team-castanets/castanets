import json
import os
from typing import List, Optional

import yaml
from jinja2 import Environment, FileSystemLoader
from pydantic.dataclasses import dataclass

from .castanets_config import CastanetsConfig


@dataclass
class GithubActionsContext:
    """
    Github Actions의 Context를 담습니다.
    """

    #: Github Webhook Event
    event_name: str
    #: Github Repo Full Name (org/repo)
    repo: str
    #: Github Ref (branch, tag, ...)
    ref: str
    #: Github Personal Access Token
    token: str
    #: Event type (ex:opened, edited, ...)
    action: Optional[str] = None
    #: Github PR/Issue number
    issue_id: Optional[int] = None
    #: Issue comment
    issue_comment: Optional[str] = None
    #: Author of issue comment
    issue_comment_author: Optional[str] = None

    @classmethod
    def construct(
        cls,
        event_name: str,
        event_path: str,
        repo: str,
        ref: str,
        token: str,
    ) -> "GithubActionsContext":
        """
        Construct GithubActionsContext.
        """
        with open(event_path, "r") as f:
            webhook_payload = json.load(f)

        action = webhook_payload.get("action")

        # Event Payloads: https://docs.github.com/en/developers/webhooks-and-events/webhooks/webhook-events-and-payloads
        issue_id = None
        if "issue" in webhook_payload:
            issue_id = webhook_payload["issue"]["number"]
        elif "pull_request" in webhook_payload:
            issue_id = webhook_payload["pull_request"]["number"]

        issue_comment = webhook_payload["comment"]["body"] if "comment" in webhook_payload else None
        issue_comment_author = webhook_payload["comment"]["user"]["login"] if "comment" in webhook_payload else None

        return cls(
            event_name=event_name,
            action=action,
            repo=repo,
            ref=ref,
            token=token,
            issue_id=issue_id,
            issue_comment=issue_comment,
            issue_comment_author=issue_comment_author,
        )


@dataclass
class CastanetsContext:
    """
    Castanets Context
    """

    #: Castanets process info
    config: CastanetsConfig
    #: Is Finished
    finished: Optional[bool] = False
    #: Process' Global Parameters
    params: Optional[dict] = None
    #: Current Stage Index
    stage_idx: Optional[int] = None
    #: Current Stage's Approvers
    approvers: Optional[List[str]] = None

    @classmethod
    def construct(
        cls,
        config_path: str,
        github_actions_context: GithubActionsContext,
        state: Optional[dict] = None,
        finished: bool = False,
        params: Optional[dict] = None,
        stage_idx: Optional[int] = None,
        approvers: Optional[List[str]] = None,
    ) -> "CastanetsContext":
        """
        Create castanets context.
        """
        jinja_env = Environment(
            loader=FileSystemLoader(os.path.dirname(config_path)), extensions=["jinja2_time.TimeExtension"]
        )
        template = jinja_env.get_template(os.path.basename(config_path))
        config_dict = yaml.load(
            template.render(params=params, github=github_actions_context, state=state), Loader=yaml.FullLoader
        )

        return cls(
            config=CastanetsConfig.from_dict(config_dict),
            finished=finished,
            params=params,
            stage_idx=stage_idx,
            approvers=approvers,
        )
