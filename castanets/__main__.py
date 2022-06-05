import castanets.commands.castanets  # noqa: F401
from castanets import context, engine
from castanets.alerts import SlackAlert
from castanets.constants import SLACK, SLACK_CHANNEL, SLACK_TOKEN


def main():
    engine.push_command_from_context()

    # Alerts
    if SLACK:
        engine.register_alert(SlackAlert(context, SLACK_CHANNEL, SLACK_TOKEN))

    engine.run()
    return 0


exit(main())
