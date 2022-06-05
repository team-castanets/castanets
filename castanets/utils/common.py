import base64
import json
import logging
import sys
import zlib
from typing import Any, Dict

import yaml
from markdown import markdown

from castanets.models import CastanetsContext


def get_logger(name: str) -> logging.Logger:
    """
    Create logger.

    :param name: Logger name
    :returns: Logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(logging.Formatter("[%(asctime)s] %(message)s"))
    logger.addHandler(stream_handler)

    return logger


def get_castanets_stage_label(label: str) -> str:
    """
    Return stage label for current stage.

    :returns: Label for current stage
    """
    return f"castanets:stage:{label}"


def get_castanets_state_from_comment(comment: str) -> Dict[str, Any]:
    """
    Read comment and get Castanets state.
    Uses XML Process Instruction format like: <?castanets {payload}?>
    """
    if "<?" not in comment or "?>" not in comment:
        return {}

    payloads = comment[comment.find("<?") + 2 : comment.find("?>")].strip().split(maxsplit=1)
    if len(payloads) <= 1 or payloads[0] != "castanets":
        return {}

    state = json.loads(payloads[1])
    return state


def get_castanets_params_from_comment(comment: str) -> Dict[str, Any]:
    """
    Get Castanets parameter from comment.
    """
    # Parse Markdown to HTML
    parsed = markdown(comment, extensions=["fenced_code"])

    # Find Code Block with <code/> Tag
    start_tag = "<code>yaml castanets\n"
    end_tag = "</code>"
    if start_tag not in parsed or end_tag not in parsed:
        return {}

    # Get Params from Code Block
    start_idx = parsed.find(start_tag) + len(start_tag)
    end_idx = parsed.find(end_tag)
    payload = parsed[start_idx:end_idx].strip()
    params = yaml.load(payload, Loader=yaml.FullLoader)
    return params


def state_dict_to_process_instruction(state: Dict[str, Any]) -> str:
    """
    With state dict, return process instruction.
    """
    return f"<?castanets {json.dumps(state)}?>"


def embed_state_to_comment(comment: str, state: Dict[str, Any]) -> str:
    """
    Embed Castanets state to comment.
    """
    state_pi = state_dict_to_process_instruction(state)

    # If it is first run
    if "<?" not in comment or "?>" not in comment:
        return comment + "\n" + state_pi

    prev_state_pi = comment[comment.find("<?") : comment.find("?>") + 2]
    return comment.replace(prev_state_pi, state_pi)


def get_mermaid_from_context(context: CastanetsContext, stage_idx: int):
    """
    Render mermaid from Castanets context.
    """
    stage_nodes = []
    for idx, stage in enumerate(context.config.stages):
        if idx < stage_idx:
            stage_nodes.append(f"{stage.label}[{stage.name}]:::Done")
        elif idx == stage_idx:
            stage_nodes.append(f"{stage.label}[{stage.name}]:::Running")
        else:
            stage_nodes.append(f"{stage.label}[{stage.name}]:::Pending")
    stage_flow = " --> ".join(stage_nodes)

    return f"""
    flowchart LR
        {stage_flow}

    classDef Done fill:#2da44e,stroke:#fff,color:white
    classDef Running fill:#bf8700,stroke:#fff,color:white
    classDef Pending fill:#888,stroke:#fff,color:white
    """


def get_mermaid_image_url(mermaid: str):
    serialized = base64.urlsafe_b64encode(zlib.compress(mermaid.encode("utf-8"), 9)).decode("ascii")
    return f"https://kroki.io/mermaid/png/{serialized}"


class Singleton:
    """
    Util class for Singleton pattern.
    """

    __instance = None

    @classmethod
    def __get_instance(cls):
        return cls.__instance

    @classmethod
    def instance(cls, *args, **kwargs):
        cls.__instance = cls(*args, **kwargs)
        cls.instance = cls.__get_instance
        return cls.__instance
