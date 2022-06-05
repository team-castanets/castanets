from typing import Any, Dict

from castanets.utils import get_logger

logger = get_logger(__name__)


def alert_handler(cls):
    """
    Class decorator for Alert Handler.
    """

    cls._handlers = {}
    for methodname in dir(cls):
        method = getattr(cls, methodname)
        if hasattr(method, "_subscribe"):
            cls._handlers[method._subscribe] = method
    return cls


def subscribe(on: str):
    """
    Class method decorator for subscribing event with key.

    :param on: Event Key to subscribe (command name)
    """

    def __function_decorator(func):
        func._subscribe = on
        return func

    return __function_decorator


@alert_handler
class BaseAlert:
    """
    Base class for Castanets alert handlers.

    Example
    --------
    .. code-block:: python
        @alert_handler
        class ExampleAlert(BaseAlert):
            def __init__(self, **kwargs):
                super(self)
                if "api_key" not in kwargs:
                    raise ValueError("API Key was not given")
                self.api_key = kwargs["api_key"]

            @subscribe(on="test_command")
            def test_command(self, command_output: Dict[str, Any]):
                client = ExampleAlertClient(api_key=api_key)
                client.send("Test Command Event!")
    """

    def alert(self, key: str, command_output: Dict[str, Any]):
        """
        Trigger event with given key.

        :param key: Key to trigger event
        :param command_output: Output of command
        """
        if key not in self._handlers:
            return
        self._handlers[key](self, command_output)
