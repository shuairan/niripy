import unittest
from unittest.mock import MagicMock, patch, mock_open
import json
from niripy.instances import Instance
from niripy.events import NiriEvent
import socket


class MockFile:
    def __init__(self, data):
        self.data = data
        self.iterator = iter(data)
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.closed = True

    def __iter__(self):
        return self.iterator

    def write(self, data):
        pass

    def flush(self):
        pass


class TestSubscribeCancel(unittest.TestCase):
    @patch("niripy.sockets.socket.socket")
    def test_subscribe_cancellation(self, mock_socket_cls):
        # Setup mock socket instance
        mock_socket = MagicMock()
        mock_socket_cls.return_value = mock_socket

        # Configure context manager for socket
        mock_socket.__enter__.return_value = mock_socket
        mock_socket.__exit__.return_value = None

        # Prepare event stream data
        events_data = [
            json.dumps({"Ok": {"Handled": True}}),
            json.dumps({"WorkspacesChanged": {"workspaces": []}}),
            json.dumps({"WindowClosed": {"id": 123}}),
        ]

        # Setup mock file object
        mock_file = MockFile(events_data)
        mock_socket.makefile.return_value = mock_file

        # We need to prevent Instance.__init__ from failing on network call
        # Mocking _request on the instance after creation won't work because it's called in __init__
        # So we patch Instance._request or mock the socket response for the version check too.

        # Let's mock _request instead, since we are testing subscribe.
        with patch.object(Instance, "_request") as mock_request:
            mock_request.return_value.version = "0.1.0"
            instance = Instance()

            # Now we test subscribe
            iterator = instance.subscribe()

            # 1. Start subscription - consumes the Reply
            # This happens implicitly when we start iterating or calling next()
            # But wait, next(iterator) will execute the code up to the first yield.
            # The code reads one line (Reply), validates it, then enters loop.

            # Get first event
            event1 = next(iterator)
            self.assertIsInstance(event1, NiriEvent)
            self.assertEqual(event1.name, "WorkspacesChanged")

            # Verify socket was NOT closed yet (context manager still active)
            # Actually, how do we verify context manager is still active?
            # We can check __exit__ hasn't been called.
            mock_socket.__exit__.assert_not_called()

            # Break the loop (by closing generator)
            iterator.close()

            # Now verify socket was closed
            mock_socket.__exit__.assert_called()
            # Verify file was closed
            self.assertTrue(mock_file.closed)


if __name__ == "__main__":
    unittest.main()
