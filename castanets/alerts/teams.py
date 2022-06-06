from typing import Any, Dict, List

import pymsteams

from castanets.utils import get_logger

from .base import BaseAlert, alert_handler, subscribe

logger = get_logger(__name__)


@alert_handler
class TeamsAlert(BaseAlert):
    """
    Alert handler for Microsoft Teams.

    :param context: castanets.context.Context
    :param webhook_url: Teams webhook url
    """

    def __init__(self, context: Any, webhook_url: str):
        self.context = context
        self.webhook_url = webhook_url
        self.teams = pymsteams.connectorcard(webhook_url)

    def _render_header(self, title: str) -> List[Dict[str, Any]]:
        """
        Render teams header message.

        :param title: Title of header
        """
        self.teams.title(f"[{self.context.castanets.config.name}] {title}")
        self.teams.text(self.context.castanets.config.description)

    def _render_footer(self) -> List[Dict[str, Any]]:
        """
        Render footer of message.

        :returns: Teams message blocks
        """
        url = f"https://github.com/{self.context.github_actions.repo}/issues/{self.context.github_actions.issue_id}"
        self.teams.addLinkButton("View in GitHub", url)

    def _render_stage_start(self, name: str, description: str):
        """
        Render stage start message.

        :param name: Stage name
        :param description: Stage description
        :returns: Teams message blocks
        """
        section = pymsteams.cardsection()
        section.text(f"🚀 **Stage {name} has started!**   \n{description}")
        self.teams.addSection(section)

    def _render_finish(self):
        """
        Render finish message.

        :returns: Teams message blocks
        """
        section = pymsteams.cardsection()
        section.text("🎉 **Castanets Process is finished. You can close the issue.**")
        self.teams.addSection(section)

    def _render_review(self, username: str, is_approval: bool):
        """
        Render review message.

        :param username: Username of the reviewer
        :param is_approval: Approval or Dismiss
        :returns: Teams message blocks
        """
        section = pymsteams.cardsection()
        section.text("*{username}* has created *{'✅ Approved' if is_approval else '❌ Dismiss'}* review.")
        self.teams.addSection(section)

    def _render_remaining_reviewers(self, approvers: List[str], reviewers: List[str], must_review: List[str]):
        """
        Render remaining reviewers message.

        :param approvers: Approvers
        :param reviewers: Reviewers
        :param must_review: Reviewers that must review
        :returns: Teams message blocks
        """
        section = pymsteams.cardsection()
        section.text("🔥 **Current Review Status**")

        for reviewer in reviewers:
            emoji = "✅" if reviewer in approvers else "🟠"
            reviewer_text = reviewer
            if reviewer in must_review:
                reviewer_text += " (Must Review)"
            section.addFact(emoji, reviewer_text)

        self.teams.addSection(section)

    def _send(self):
        """
        Send a message to Teams.
        """
        self.teams.send()
        self.teams = pymsteams.connectorcard(self.webhook_url)

    @subscribe(on="initialize")
    def on_initialize(self, command_output: Dict[str, Any]):
        logger.info(f"TeamsAlert: initialize, payload: {command_output}")
        self._render_header("Castanets Process Start")
        self._render_footer()
        self._send()

    @subscribe(on="stage_start")
    def on_stage_start(self, command_output: Dict[str, Any]):
        logger.info(f"TeamsAlert: stage_start, payload: {command_output}")

        stage_idx = command_output["stage_idx"]
        stage_name = self.context.castanets.config.stages[stage_idx].name
        stage_description = self.context.castanets.config.stages[stage_idx].description
        review = self.context.castanets.config.stages[stage_idx].review
        reviewers = review.reviewers
        must_review = review.must_review

        self._render_header(f"Stage {stage_idx + 1} start")
        self._render_stage_start(stage_name, stage_description)
        self._render_remaining_reviewers([], reviewers, must_review)
        self._render_footer()
        self._send()

    @subscribe(on="approve")
    def on_approve(self, command_output: Dict[str, Any]):
        logger.info(f"TeamsAlert: approve, payload: {command_output}")

        username = command_output["username"]
        approvers = command_output["approvers"]

        stage_idx = self.context.castanets.stage_idx
        review = self.context.castanets.config.stages[stage_idx].review
        reviewers = review.reviewers
        must_review = review.must_review

        self._render_header("Approval Event")
        self._render_review(username, True)
        self._render_remaining_reviewers(approvers, reviewers, must_review)
        self._render_footer()
        self._send()

    @subscribe(on="dismiss")
    def on_dismiss(self, command_output: Dict[str, Any]):
        logger.info(f"TeamsAlert: dismiss, payload: {command_output}")

        username = command_output["username"]
        approvers = command_output["approvers"]

        stage_idx = self.context.castanets.stage_idx
        review = self.context.castanets.config.stages[stage_idx].reviewers
        reviewers = review.reviewers
        must_review = review.must_review

        self._render_header("Dismiss Event")
        self._render_review(username, True)
        self._render_remaining_reviewers(approvers, reviewers, must_review)
        self._render_footer()
        self._send()

    @subscribe(on="finish")
    def on_finish(self, command_output: Dict[str, Any]):
        logger.info(f"TeamsAlert: finish, payload: {command_output}")

        self._render_header("Process finished")
        self._render_finish()
        self._render_footer()
        self._send()
