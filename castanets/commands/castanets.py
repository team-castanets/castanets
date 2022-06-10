import os

from jinja2 import Environment, FileSystemLoader

from castanets import context, engine
from castanets.commands import command
from castanets.constants import ISSUE_AUTOCLOSE, ROOT_DIR
from castanets.utils import get_castanets_stage_label, get_logger, get_mermaid_from_context, github

logger = get_logger(__name__)
jinja_env = Environment(loader=FileSystemLoader(os.path.join(ROOT_DIR, "templates")))


@command("help")
def help():
    """
    Create help message.
    """
    help_text = "## Castanets Usage\n"
    help_text += "* `/help`\n"
    help_text += "* `/approve`: Approve the current stage.\n"
    help_text += "* `/dismiss`: Dismiss the current stage.\n"
    help_text += "* `/rerun`: Rerun the current stage's workflow.\n"
    help_text += "* `/clean_up`: Clean up current stage.\n"
    help_text += "* `/stage_next`: Force move to next stage.\n"
    help_text += "* `/finish`: Finish the process.\n"
    github.comment(context.github_actions, help_text)


@command("initialize")
def initialize():
    """
    Initialize castanets.
    """
    template = jinja_env.get_template("castanets_initialize.md")
    comment = template.render(name=context.castanets.config.name, description=context.castanets.config.description)
    github.comment(context.github_actions, comment)


@command("stage_start")
def stage_start(stage_idx: int):
    """
    Start stage with stage index.

    :param stage_idx: Stage ID
    """
    if stage_idx >= len(context.castanets.config.stages) or stage_idx < 0:
        raise ValueError(f"Stage Index is out of range: {stage_idx}")

    stage = context.castanets.config.stages[stage_idx]
    if stage_idx == 0:
        prev_stage_name = "Start"
    else:
        prev_stage_name = context.castanets.config.stages[stage_idx - 1].name
    mermaid = get_mermaid_from_context(context.castanets, stage_idx)

    template = jinja_env.get_template("castanets_process.md")
    comment = template.render(
        prev_stage=prev_stage_name,
        current_stage=stage.name,
        workflow_url=f"https://github.com/{context.github_actions.repo}/actions/workflows/{stage.workflow.filename}",
        stage_mermaid=mermaid,
        description=stage.description,
        minimum_approval=stage.review.minimum_approval,
        reviewers=stage.review.reviewers,
        must_review=stage.review.must_review,
    )

    github.comment(context.github_actions, comment)
    github.set_label(context.github_actions, get_castanets_stage_label(stage.label))
    github.set_assignees(context.github_actions, stage.review.reviewers)
    github.run_workflow(context.github_actions, stage.workflow.filename, stage.workflow.inputs)

    # State update
    state = github.read_state_from_first_comment(context.github_actions)
    state["stage_idx"] = stage_idx
    github.write_state_to_first_comment(context.github_actions, state)

    return {"stage_idx": stage_idx}


@command("stage_rerun")
def stage_rerun():
    """
    Rerun current stage's workflow.
    """
    stage_idx = context.castanets.stage_idx
    stage = context.castanets.config.stages[stage_idx]
    github.run_workflow(context.github_actions, stage.workflow.filename, stage.workflow.inputs)


@command("stage_clean_up")
def stage_clean_up():
    """
    Clean up current stage.
    """
    stage_idx = context.castanets.stage_idx
    stage = context.castanets.config.stages[stage_idx]
    github.remove_label(
        context.github_actions,
        get_castanets_stage_label(stage.label),
    )
    github.remove_assignees(context.github_actions, stage.review.reviewers)
    github.write_state_to_first_comment(context.github_actions, {})

    if stage.workflow_clean_up is not None:
        github.run_workflow(context.github_actions, stage.workflow_clean_up.filename, stage.workflow_clean_up.inputs)


@command("stage_next")
def stage_next():
    """
    Move to next stage.
    """
    engine.push_command("stage_clean_up")
    stage_idx = context.castanets.stage_idx
    if stage_idx + 1 >= len(context.castanets.config.stages):
        engine.push_command("finish")
    else:
        engine.push_command("stage_start", stage_idx + 1)


@command("approve")
def approve(username: str):
    """
    Approve user.
    """
    approvers = set(context.castanets.approvers) if context.castanets.approvers else set()
    approvers.add(username)
    new_approvers = list(approvers)

    stage_idx = context.castanets.stage_idx
    review = context.castanets.config.stages[stage_idx].review
    if review.is_stage_approved(new_approvers):
        engine.push_command("stage_next")
    else:
        # Update State Comment
        state = github.read_state_from_first_comment(context.github_actions)
        state["approvers"] = new_approvers
        github.write_state_to_first_comment(context.github_actions, state)

    return {"username": username, "approvers": new_approvers}


@command("dismiss")
def dismiss(username: str):
    """
    Dismiss user.
    """
    approvers = set(context.castanets.approvers) if context.castanets.approvers else set()
    approvers.discard(username)
    new_approvers = list(approvers.add(username))

    # Update State Comment
    state = github.read_state_from_first_comment(context.github_actions)
    state["approvers"] = new_approvers
    github.write_state_to_first_comment(context.github_actions, state)

    return {"username": username, "approvers": new_approvers}


@command("finish")
def finish(auto_close: bool = False):
    """
    Finish the process.
    """
    template = jinja_env.get_template("castanets_finish.md")
    comment = template.render(issue_autoclose=ISSUE_AUTOCLOSE)
    github.comment(context.github_actions, comment)
    github.write_state_to_first_comment(context.github_actions, {"finished": True})

    if ISSUE_AUTOCLOSE:
        github.update_issue(context.github_actions, {"state": "closed"})
