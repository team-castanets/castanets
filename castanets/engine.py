import sys
from queue import Queue
from typing import Any, List

from castanets import context
from castanets.alerts import BaseAlert
from castanets.commands import get_command
from castanets.utils import get_logger, github

logger = get_logger(__name__)


class CastanetsEngine:
    """
    Do actions with Castanets' global command queue and alert hander:

    1. Command Management
    - With global command queue, run a command in pushed order.
    - Each command can also push command in command queue with `push_command` method.

    2. Alert Management
    - You can register alert handlers (Class that inherits `BaseAlert`) with `register_alert` method.
    - Each alert handler will be called when a command is executed.

    :param config_path: Configuration file path
    """

    _command_queue: Queue = Queue()
    _alerts: List[BaseAlert] = []

    def run(self):
        """
        Run commands in command queue.
        """
        while not self._command_queue.empty():
            command_name, args, kwargs = self._command_queue.get()
            command = get_command(command_name)

            try:
                logger.info(f"Running command {command_name} with args: {args} and kwargs: {kwargs}")
                output = command(*args, **kwargs)
            except Exception as e:
                raise RuntimeError(f"{command_name} Command 실행에 실패하였습니다.") from e

            self.alert(command._command_name, output)

    def push_command(self, command_name: str, *args, **kwargs):
        """
        Add command to queue.

        :param command: Name of command
        """
        self._command_queue.put((command_name, args, kwargs))

    def push_command_from_context(self):
        """
        Add commands to queue generated from context.
        """
        event_name = context.github_actions.event_name
        action = context.github_actions.action

        if context.castanets.finished:
            return

        if event_name in ["pull_request", "issues"] and action == "opened":
            self.push_command("initialize")
            self.push_command("stage_start", 0)
        elif event_name == "issue_comment" and action == "created":
            comment = context.github_actions.issue_comment
            author = context.github_actions.issue_comment_author
            action_user = github.get_user(context=context.github_actions)

            # If current event is from GitHub PAT's user, then do nothing.
            if author == action_user["login"]:
                return

            # If current comment is not slash command, then do nothing.
            if not comment.startswith("/"):
                return

            command = comment[1:].split()[0]
            if command in ["approve", "dismiss"]:
                self.push_command(command, author)
            elif command == ["rerun", "clean_up", "stage_next", "finish", "help"]:
                self.push_command(command)
            else:
                self.push_command("help")

    def alert(self, key: str, payload: Any):
        """
        Make an alert.

        :param key: Key(command_name) of alert
        :param payload: Payload of alert
        """
        try:
            for alert_handler in self._alerts:
                logger.info(f"Alerting {alert_handler.__class__.__name__} with payload: {payload}")
                alert_handler.alert(key, payload)
        except Exception as e:
            raise RuntimeError(f"Alert for {key} event failed.") from e

    def register_alert(self, alert: BaseAlert):
        """
        Register an alert handler.

        :param alert: Alert class
        """
        self._alerts.append(alert)


sys.modules[__name__] = CastanetsEngine()
