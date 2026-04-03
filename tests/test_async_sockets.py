"""Tests for async socket methods."""
import asyncio
import os
import socket
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from niripy.sockets import Socket


@pytest.fixture
def socket_path(tmp_path):
    socket_file = tmp_path / "test.sock"
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.bind(str(socket_file))
    sock.listen(1)
    yield socket_file
    sock.close()
    if socket_file.exists():
        socket_file.unlink()


@pytest.fixture
def mock_env_socket(socket_path):
    with patch.dict(os.environ, {"NIRI_SOCKET": str(socket_path)}):
        yield socket_path


def test_async_event_stream_yields_decoded_lines(mock_env_socket):
    """async_event_stream yields UTF-8 decoded lines from the socket."""
    raw_lines = [
        b'{"Ok":"Handled"}\n',
        b'{"WorkspacesChanged":{"workspaces":[]}}\n',
    ]

    async def fake_connection(path):
        async def line_iter():
            for line in raw_lines:
                yield line

        mock_writer = MagicMock()
        mock_writer.write_eof = MagicMock()
        mock_writer.close = MagicMock()
        mock_writer.wait_closed = AsyncMock()
        return line_iter(), mock_writer

    async def run():
        with patch("asyncio.open_unix_connection", fake_connection):
            sock = Socket()
            result = []
            async for line in sock.async_event_stream():
                result.append(line)
        return result

    result = asyncio.run(run())
    assert result == [
        '{"Ok":"Handled"}\n',
        '{"WorkspacesChanged":{"workspaces":[]}}\n',
    ]


def test_async_event_stream_closes_writer_on_cancel(mock_env_socket):
    """async_event_stream cleans up writer.close() + wait_closed() even on cancel."""
    mock_writer = MagicMock()
    mock_writer.write_eof = MagicMock()
    mock_writer.close = MagicMock()
    mock_writer.wait_closed = AsyncMock()

    async def infinite_stream():
        while True:
            yield b"line\n"
            await asyncio.sleep(0)  # yield control

    async def fake_connection(path):
        return infinite_stream(), mock_writer

    async def run():
        with patch("asyncio.open_unix_connection", fake_connection):
            sock = Socket()
            task = asyncio.create_task(_consume(sock))
            await asyncio.sleep(0)  # let task start
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        mock_writer.close.assert_called_once()
        mock_writer.wait_closed.assert_awaited_once()

    async def _consume(sock):
        async for _ in sock.async_event_stream():
            pass

    asyncio.run(run())


from niripy.events import NiriEvent
from niripy.instances import Instance


def test_asubscribe_skips_reply_and_yields_events(mock_env_socket):
    """asubscribe yields NiriEvent objects, consuming the initial reply line."""
    stream_lines = [
        '{"Ok":"Handled"}\n',
        '{"WorkspacesChanged":{"workspaces":[]}}\n',
        '{"WindowClosed":{"id":123}}\n',
    ]

    async def fake_stream():
        for line in stream_lines:
            yield line

    async def run():
        with patch.object(Instance, "_request") as mock_req:
            mock_req.return_value.version = "0.1.0"
            instance = Instance()
            with patch.object(instance.socket, "async_event_stream", return_value=fake_stream()):
                events = []
                async for event in instance.asubscribe():
                    events.append(event)
                return events

    events = asyncio.run(run())
    assert len(events) == 2
    assert all(isinstance(e, NiriEvent) for e in events)
    assert events[0].name == "WorkspacesChanged"
    assert events[1].name == "WindowClosed"


def test_asubscribe_raises_on_bad_reply(mock_env_socket):
    """asubscribe raises if the initial reply is not Ok."""
    async def fake_stream():
        yield '{"Err":"SomeError"}\n'

    async def run():
        with patch.object(Instance, "_request") as mock_req:
            mock_req.return_value.version = "0.1.0"
            instance = Instance()
            with patch.object(instance.socket, "async_event_stream", return_value=fake_stream()):
                async for _ in instance.asubscribe():
                    pass  # should raise before yielding

    with pytest.raises(Exception):
        asyncio.run(run())
