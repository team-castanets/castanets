import castanets.commands.castanets  # noqa: F401
from castanets import context, engine
from castanets.alerts import SlackAlert, TeamsAlert
from castanets.constants import SLACK, SLACK_CHANNEL, SLACK_TOKEN, TEAMS, TEAMS_WEBHOOK_URL


def main():
    engine.push_command_from_context()

    # Alerts
    if SLACK:
        engine.register_alert(SlackAlert(context, SLACK_CHANNEL, SLACK_TOKEN))
    if TEAMS:
        engine.register_alert(TeamsAlert(context, TEAMS_WEBHOOK_URL))

    engine.run()
    return 0


exit(main())
