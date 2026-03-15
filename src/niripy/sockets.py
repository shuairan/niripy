from _socket import SHUT_WR

import json
import os
import select
import socket
from pathlib import Path
from typing import Any, override, Generator


class SocketError(Exception):
    """Exception raised when a socket operation fails.

    This exception is raised when any socket-related operation encounters an error,
    such as attempting to send data on a disconnected socket or timing out while
    waiting for a response.

    Example:
        >>> try:
        ...     socket.send("command")
        ... except SocketError as e:
        ...     print(f"Socket operation failed: {e}")
    """

    pass


class Socket:
    """Unix domain socket client for communicating with Niri.

    This class provides a high-level interface for sending commands to and receiving
    responses from a Niri IPC socket. It handles connection management, message
    serialization, and error handling.

    Example:
        >>> from niripy.sockets import Socket
        >>> socket = Socket()
        >>> response = socket.send_command({"action": "version"})
        >>> print(response)
    """

    path: Path
    """The filesystem path to the Unix domain socket."""
    _socket: socket.socket | None
    """The underlying socket object, or None if not connected."""

    def __init__(self, path_to_socket: str = ""):
        """Initialize a Socket instance.

        If no path is provided, attempts to read the socket path from the
        $NIRI_SOCKET environment variable. The socket must exist and be a valid
        Unix domain socket.

        Args:
            path_to_socket (str, optional): Path to the Niri socket. If not
                provided, reads from $NIRI_SOCKET environment variable.
                Defaults to "".

        Raises:
            RuntimeError: If neither path_to_socket nor $NIRI_SOCKET is defined.
            FileNotFoundError: If the socket path does not exist or is not a
                valid socket.

        Example:
            >>> # Using environment variable
            >>> socket = Socket()
            >>>
            >>> # Using explicit path
            >>> socket = Socket("/run/user/1000/niri.sock")
        """
        path_to_socket = path_to_socket or os.getenv("NIRI_SOCKET", "")
        if not path_to_socket:
            raise RuntimeError(
                "$NIRI_SOCKET is not defined and no socket provided. "  # pyright: ignore[reportImplicitStringConcatenation]
                "Are you running inside a niri session?"
            )

        self.path = Path(path_to_socket)

        if not self.path.is_socket():
            raise FileNotFoundError(f"No socket found at {self.path!r}.")
        self._socket = None
        self._event_socket = None

    @override
    def __repr__(self) -> str:
        return f"<Socket(path={str(self.path)!r})>"

    def connect(self, timeout: float | None = 1.0):
        """Establish a connection to the Niri socket.

        Creates a Unix domain socket and connects to the socket path specified
        during initialization. After connection, the socket is set to non-blocking
        mode.

        Args:
            timeout (float | None, optional): Connection timeout in seconds.
                Defaults to 1.0.

        Raises:
            SocketError: If the socket is already connected.
            ConnectionRefusedError: If connection to the socket fails.

        Example:
            >>> socket = Socket()
            >>> socket.connect(timeout=2.0)
        """
        if self._socket:
            raise SocketError("Connect to socket failed: Socket is already connected.")

        self._socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._socket.settimeout(timeout)
        self._socket.connect(str(self.path))
        self._socket.setblocking(False)

    def close(self):
        """Close the socket connection.

        Closes the underlying socket and sets the socket reference to None.
        After closing, the socket must be reconnected before further operations.

        Raises:
            SocketError: If the socket is not currently connected.

        Example:
            >>> socket = Socket()
            >>> socket.connect()
            >>> socket.close()
        """
        if not self._socket:
            raise SocketError("Close socket failed: Socket is not connected.")

        self._socket.close()
        self._socket = None

    def send(self, data: str):
        """Send a string message to the socket.

        Encodes the string as UTF-8 and sends it over the connected socket.

        Args:
            data (str): The message to send. Should be JSON-formatted for
                Niri commands.

        Raises:
            SocketError: If the socket is not currently connected.
            UnicodeEncodeError: If the data cannot be encoded as UTF-8.

        Example:
            >>> socket = Socket()
            >>> socket.connect()
            >>> socket.send('{"action": "version"}')
        """
        if not self._socket:
            raise SocketError("Send data to socket failed: Socket is not connected.")

        self._socket.sendall(data.encode("utf-8"))

    def wait(self, timeout: float | None = None):
        """Wait for data to be available on the socket.

        Blocks until data is available to read from the socket or the timeout
        expires.

        Args:
            timeout (float | None, optional): Maximum time to wait in seconds.
                If None, waits indefinitely. Defaults to None.

        Raises:
            SocketError: If the socket is not connected.
            SocketError: If no data becomes available within the timeout period.

        Example:
            >>> socket = Socket()
            >>> socket.connect()
            >>> socket.send('{"action": "version"}')
            >>> socket.wait(timeout=5.0)  # Wait up to 5 seconds for response
        """
        if not self._socket:
            raise SocketError(
                "Wait for data on socket failed: Socket is not connected."
            )

        ready, _, _ = select.select([self._socket], [], [], timeout)
        if not ready:
            raise SocketError(
                f"Wait for data on socket failed after {timeout} seconds."
            )

    def read(self) -> str:
        """Read all available data from the socket.

        Reads data from the socket in 4KB chunks until no more data is available.
        Handles non-blocking socket operations gracefully.

        Returns:
            The data read from the socket, decoded as UTF-8. For Niri
                responses, this will be JSON-formatted.

        Raises:
            SocketError: If the socket is not connected.
            SocketError: If a socket read error occurs.
            UnicodeDecodeError: If the data cannot be decoded as UTF-8.

        Example:
            >>> socket = Socket()
            >>> socket.connect()
            >>> socket.send('{"action": "version"}')
            >>> socket.wait(timeout=5.0)
            >>> response = socket.read()
            >>> print(response)
        """
        if not self._socket:
            raise SocketError("Read data from socket failed: Socket is not connected.")

        data = bytearray()
        while True:
            try:
                data_chunk = self._socket.recv(4096)
                if data_chunk:
                    data += data_chunk
                else:
                    break
            except BlockingIOError as e:
                if e.errno == 11:
                    break
                else:
                    raise SocketError("Read data from socket failed.") from e

        return data.decode("utf-8")

    def send_command(self, message: dict[str, Any] | str) -> str:
        """Send a command message and retrieve the response.

        A high-level convenience method that handles the complete request-response
        cycle: connects to the socket, sends the message, waits for a response,
        reads the data, and closes the connection.

        Args:
            message (dict[str, Any] | str): The command message to send.
                Can be a dictionary (which will be JSON-serialized) or a
                pre-formatted JSON string.

        Returns:
            The response received from Niri as a JSON-formatted string.

        Raises:
            SocketError: If any socket operation fails.
            RuntimeError: If $NIRI_SOCKET is not set and no socket path was
                provided.
            FileNotFoundError: If the socket does not exist.
            ConnectionRefusedError: If connection to the socket fails.

        Example:
            >>> from niripy.sockets import Socket
            >>> socket = Socket()
            >>>
            >>> # Send a dict command
            >>> response = socket.send_command({"action": "version"})
            >>> print(response)
            >>>
            >>> # Send a pre-formatted JSON command
            >>> response = socket.send_command('{"action": "version"}')
            >>> print(response)
        """
        self.connect()
        self.send(json.dumps(message) + "\n")
        self.wait(5)
        response = self.read()
        self.close()

        return response

    def event_stream(self) -> Generator[str, Any, None]:
        """Start continuously receiving events from the event stream.

        The first reply is expected to be an {"Ok":"Handled"}, then continuously send Events, one per line.

        Returns:
            The data read from the socket, decoded as UTF-8. For Niri
                responses, this will be JSON-formatted.
        """
        with socket.socket(socket.AF_UNIX) as niri_socket:
            niri_socket.connect(str(self.path))
            with niri_socket.makefile("rw") as file:
                file.write('"EventStream"')
                file.flush()
                niri_socket.shutdown(SHUT_WR)

                for line in file:
                    yield line
