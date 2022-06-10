import os
import sys

from pydantic.dataclasses import dataclass

from .constants import (
    CASTANETS_CONFIG_PATH,
    GITHUB_EVENT_NAME,
    GITHUB_EVENT_PATH,
    GITHUB_REF_NAME,
    GITHUB_REPOSITORY,
    GITHUB_TOKEN,
    GITHUB_WORKSPACE,
)
from .models.contexts import CastanetsContext, GithubActionsContext
from .utils import github


@dataclass
class Context:
    """
    Manage the context of the current execution.
    """

    #: Github Actions context
    github_actions: GithubActionsContext
    #: Castanets context
    castanets: CastanetsContext

    @classmethod
    def construct(cls) -> "Context":
        """
        Construct Castanets context.
        """
        github_actions = GithubActionsContext.construct(
            event_name=GITHUB_EVENT_NAME,
            event_path=GITHUB_EVENT_PATH,
            repo=GITHUB_REPOSITORY,
            ref=GITHUB_REF_NAME,
            token=GITHUB_TOKEN,
        )

        # Get Castanets State and Parameters
        if github_actions.issue_id is not None:
            state = github.read_state_from_first_comment(github_actions)
            params = github.read_params_from_issue_body(github_actions)
        else:
            state = {}
            params = {}

        stage_idx = state.get("stage_idx", None)
        approvers = state.get("approvers", None)
        finished = state.get("finished", False)
        castanets = CastanetsContext.construct(
            os.path.join(GITHUB_WORKSPACE, CASTANETS_CONFIG_PATH),
            github_actions,
            state,
            finished=finished,
            params=params,
            stage_idx=stage_idx,
            approvers=approvers,
        )

        return cls(
            github_actions=github_actions,
            castanets=castanets,
        )


sys.modules[__name__] = Context.construct()
