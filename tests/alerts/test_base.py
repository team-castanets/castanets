from dataclasses import dataclass

from castanets.alerts.base import BaseAlert, alert_handler, subscribe


def test_alert():
    @dataclass
    class MustBeModified:
        item: str = "not_modified"

    @alert_handler
    class ModifyItemAlert(BaseAlert):
        """
        Test alert for changing message in payload.

        :param must_be_modified: Payload that variable `item` will be modified.
        """

        def __init__(self, must_be_modified: MustBeModified):
            self.must_be_modified = must_be_modified

        @subscribe(on="test")
        def test_command(self, payload: dict):
            self.must_be_modified.item = payload["item"]

    must_be_modified = MustBeModified()
    alert = ModifyItemAlert(must_be_modified)
    alert.alert("test", {"item": "modified"})

    assert must_be_modified.item == "modified"
