from typing import Any, Dict, List

from slack_sdk import WebClient

from castanets.utils import get_logger

from .base import BaseAlert, alert_handler, subscribe

logger = get_logger(__name__)


@alert_handler
class SlackAlert(BaseAlert):
    """
    Alert handler for Slack.

    :param context: castanets.context.Context
    :param channel: Slack channel
    :param token: Slack token
    """

    def __init__(self, context: Any, channel: str, token: str):
        self.context = context
        self.channel = channel
        self.client = WebClient(token=token)

    def _render_header(self, title: str, process_info_as_description: bool = False) -> List[Dict[str, Any]]:
        """
        Render slack message.

        :param title: Title of header
        :returns: Slack message blocks
        """
        name = self.context.castanets.config.name
        description = self.context.castanets.config.description
        rendered = []

        # Title
        if not process_info_as_description:
            title = f"[{name}] {title}"
        rendered.append({"type": "header", "text": {"type": "plain_text", "text": title, "emoji": True}})

        if process_info_as_description:
            # Process Info
            rendered.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Name:* {name}\n*Description:* {description}",
                    },
                }
            )

        # Divider
        rendered.append({"type": "divider"})

        return rendered

    def _render_footer(self) -> List[Dict[str, Any]]:
        """
        Render footer of message.

        :returns: Slack message blocks
        """
        url = f"https://github.com/{self.context.github_actions.repo}/issues/{self.context.github_actions.issue_id}"
        rendered = []

        rendered.append(
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "View in GitHub"},
                        "url": url,
                    }
                ],
            }
        )

        rendered.append(
            {
                "type": "context",
                "elements": [{"type": "plain_text", "text": "Notification from Castanets", "emoji": True}],
            }
        )

        return rendered

    def _render_stage_start(self, name: str, description: str):
        """
        Render stage start message.

        :param name: Stage name
        :param description: Stage description
        :returns: Slack message blocks
        """
        return [
            (
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"🚀 *Stage {name} has started!*\n{description}",
                    },
                }
            )
        ]

    def _render_finish(self):
        """
        Render finish message.

        :returns: Slack message blocks
        """
        return [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "🎉 *Castanets Process is finished. You can close the issue.*"},
            }
        ]

    def _render_review(self, username: str, is_approval: bool):
        """
        Render review message.

        :param username: Username of the reviewer
        :param is_approval: Approval or Dismiss
        :returns: Slack message blocks
        """
        return [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{username}* has created *{'✅ Approved' if is_approval else '❌ Dismiss'}* review.",
                },
            }
        ]

    def _render_remaining_reviewers(self, approvers: List[str], reviewers: List[str], must_review: List[str]):
        """
        Render remaining reviewers message.

        :param approvers: Approvers
        :param reviewers: Reviewers
        :param must_review: Reviewers that must review
        :returns: Slack message blocks
        """
        rendered = []

        rendered.append({"type": "section", "text": {"type": "mrkdwn", "text": "🔥 *Current Review Status*"}})
        for reviewer in reviewers:
            reviewer_text = f"• ✅ {reviewer}" if reviewer in approvers else f"• 🟠 *{reviewer}*"
            if reviewer in must_review:
                reviewer_text += " (Must Review)"
            rendered.append({"type": "section", "text": {"type": "mrkdwn", "text": reviewer_text}})

        return rendered

    def _post_message(self, blocks: List[Dict[str, Any]]):
        """
        Send a message to slack.

        :blocks: Slack message blocks
        """
        self.client.chat_postMessage(
            channel=self.channel,
            blocks=blocks,
            username="Castanets",
            icon_url="https://gcdnb.pbrd.co/images/UySphOakKcZh.png",
        )

    @subscribe(on="initialize")
    def on_initialize(self, command_output: Dict[str, Any]):
        logger.info(f"SlackAlert: initialize, payload: {command_output}")
        blocks = []
        blocks.extend(self._render_header("Castanets Process Start", process_info_as_description=True))
        blocks.extend(self._render_footer())
        self._post_message(blocks)

    @subscribe(on="stage_start")
    def on_stage_start(self, command_output: Dict[str, Any]):
        logger.info(f"SlackAlert: stage_start, payload: {command_output}")

        stage_idx = command_output["stage_idx"]
        stage_name = self.context.castanets.config.stages[stage_idx].name
        stage_description = self.context.castanets.config.stages[stage_idx].description
        review = self.context.castanets.config.stages[stage_idx].review
        reviewers = review.reviewers
        must_review = review.must_review

        blocks = []
        blocks.extend(self._render_header(f"Stage {stage_idx + 1} start"))
        blocks.extend(self._render_stage_start(stage_name, stage_description))
        blocks.extend(self._render_remaining_reviewers([], reviewers, must_review))
        blocks.extend(self._render_footer())
        self._post_message(blocks)

    @subscribe(on="approve")
    def on_approve(self, command_output: Dict[str, Any]):
        logger.info(f"SlackAlert: approve, payload: {command_output}")

        username = command_output["username"]
        approvers = command_output["approvers"]

        stage_idx = self.context.castanets.stage_idx
        review = self.context.castanets.config.stages[stage_idx].review
        reviewers = review.reviewers
        must_review = review.must_review

        blocks = []
        blocks.extend(self._render_header("Approval Event"))
        blocks.extend(self._render_review(username, True))
        blocks.extend(self._render_remaining_reviewers(approvers, reviewers, must_review))
        blocks.extend(self._render_footer())
        self._post_message(blocks)

    @subscribe(on="dismiss")
    def on_dismiss(self, command_output: Dict[str, Any]):
        logger.info(f"SlackAlert: dismiss, payload: {command_output}")

        username = command_output["username"]
        approvers = command_output["approvers"]

        stage_idx = self.context.castanets.stage_idx
        review = self.context.castanets.config.stages[stage_idx].reviewers
        reviewers = review.reviewers
        must_review = review.must_review

        blocks = []
        blocks.extend(self._render_header("Dismiss Event"))
        blocks.extend(self._render_review(username, True))
        blocks.extend(self._render_remaining_reviewers(approvers, reviewers, must_review))
        blocks.extend(self._render_footer())
        self._post_message(blocks)

    @subscribe(on="finish")
    def on_finish(self, command_output: Dict[str, Any]):
        logger.info(f"SlackAlert: finish, payload: {command_output}")

        blocks = []
        blocks.extend(self._render_header("Process finished"))
        blocks.extend(self._render_finish())
        blocks.extend(self._render_footer())
        self._post_message(blocks)
