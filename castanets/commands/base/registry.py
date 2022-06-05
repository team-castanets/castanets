from typing import Callable

#: Command Registry
__COMMAND_REGISTRY = {}


def command(name: str):
    """
    Decorator for defining Command.

    Example
    --------
    .. code-block:: python
        @command("test_command")
        def test_command(self, value):
            return {"status": "ok"}

    :param name: Command name (will be alerted with this name)
    """

    def __fn_decorator(fn):
        fn._command_name = name
        global __COMMAND_REGISTRY
        __COMMAND_REGISTRY[name] = fn
        return fn

    return __fn_decorator


def get_command(name: str) -> Callable:
    """
    Return command function by name.

    :param name: Command name
    :returns: Command function
    """
    return __COMMAND_REGISTRY[name]
