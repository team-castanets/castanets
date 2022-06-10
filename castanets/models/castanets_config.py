from typing import List, Optional

from pydantic import validator
from pydantic.dataclasses import dataclass


@dataclass
class Review:
    """
    Review condition for current stage's approval.
    """

    #: Usernames of reviewers
    reviewers: List[str]
    #: Usernames who must review
    must_review: List[str]
    #: Minimum number of approvals required
    minimum_approval: int

    def is_stage_approved(self, approvers: List[str]) -> bool:
        """
        Get current stage's approval status.

        :param approvers: Users who approved the stage
        """
        return all(reviewer in approvers for reviewer in self.must_review) and len(approvers) >= self.minimum_approval

    @validator("reviewers", always=True)
    def _validate_reviewers(cls, v: List[str]) -> List[str]:
        assert len(v) > 0, "Reviewers must be at least one."
        return v

    @validator("must_review", each_item=True)
    def _validate_must_reviewers(cls, v: str, values: dict) -> str:
        assert v in values["reviewers"], f"Reviewer {v} must be in reviewers."
        return v

    @validator("minimum_approval", always=True)
    def _validate_minimum_approval(cls, v: int) -> int:
        assert v > 0, "Minimum approval must be greater than 0."
        return v


@dataclass
class Workflow:
    """
    Github Actions workflow info.
    """

    #: Workflow Filename
    filename: str
    #: Workflow Input
    inputs: Optional[dict] = None


@dataclass
class CastanetsStage:
    """
    Castanets stage info.
    """

    #: Stage name
    name: str
    #: Stage label
    label: str
    #: Stage description
    description: str
    #: Stage approval condition
    review: Review
    #: Workflow to run on stage start
    workflow: Optional[Workflow] = None
    #: Workflow to run on stage clean up
    workflow_clean_up: Optional[Workflow] = None


@dataclass
class CastanetsConfig:
    """
    Castanets configuration.
    """

    #: Process name
    name: str
    #: Process description
    description: str
    #: Stages to run
    stages: List[CastanetsStage]

    @staticmethod
    def from_dict(config_dict: dict) -> "CastanetsConfig":
        """
        Create config from dict

        :param config_dict: CastanetsConfig dict
        """
        return CastanetsConfig(**config_dict)
