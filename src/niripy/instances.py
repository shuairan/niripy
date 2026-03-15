from typing import Any, Literal, override, Generator

from pydantic.alias_generators import to_pascal, to_snake

from niripy.events import NiriEvent
from niripy.models import (
    LayerSurface,
    Output,
    Reply,
    Response,
    Window,
    Workspace,
)
from niripy.sockets import Socket

RequestCmd = Literal[
    "outputs",
    "workspaces",
    "windows",
    "layers",
    "keyboard-layouts",
    "focused-output",
    "focused-window",
    "pick-window",
    "pick-color",
    "version",
    "request-error",
    "overview-state",
]

ActionCmd = Literal[
    "quit",
    "power-off-monitors",
    "power-on-monitors",
    "spawn",
    "spawn-sh",
    "do-screen-transition",
    "screenshot",
    "screenshot-screen",
    "screenshot-window",
    "toggle-keyboard-shortcuts-inhibit",
    "close-window",
    "fullscreen-window",
    "toggle-windowed-fullscreen",
    "focus-window",
    "focus-window-in-column",
    "focus-window-previous",
    "focus-column-left",
    "focus-column-right",
    "focus-column-first",
    "focus-column-last",
    "focus-column-right-or-first",
    "focus-column-left-or-last",
    "focus-column",
    "focus-window-or-monitor-up",
    "focus-window-or-monitor-down",
    "focus-column-or-monitor-left",
    "focus-column-or-monitor-right",
    "focus-window-down",
    "focus-window-up",
    "focus-window-down-or-column-left",
    "focus-window-down-or-column-right",
    "focus-window-up-or-column-left",
    "focus-window-up-or-column-right",
    "focus-window-or-workspace-down",
    "focus-window-or-workspace-up",
    "focus-window-top",
    "focus-window-bottom",
    "focus-window-down-or-top",
    "focus-window-up-or-bottom",
    "move-column-left",
    "move-column-right",
    "move-column-to-first",
    "move-column-to-last",
    "move-column-left-or-to-monitor-left",
    "move-column-right-or-to-monitor-right",
    "move-column-to-index",
    "move-window-down",
    "move-window-up",
    "move-window-down-or-to-workspace-down",
    "move-window-up-or-to-workspace-up",
    "consume-or-expel-window-left",
    "consume-or-expel-window-right",
    "consume-window-into-column",
    "expel-window-from-column",
    "swap-window-right",
    "swap-window-left",
    "toggle-column-tabbed-display",
    "set-column-display",
    "center-column",
    "center-window",
    "center-visible-columns",
    "focus-workspace-down",
    "focus-workspace-up",
    "focus-workspace",
    "focus-workspace-previous",
    "move-window-to-workspace-down",
    "move-window-to-workspace-up",
    "move-window-to-workspace",
    "move-column-to-workspace-down",
    "move-column-to-workspace-up",
    "move-column-to-workspace",
    "move-workspace-down",
    "move-workspace-up",
    "move-workspace-to-index",
    "set-workspace-name",
    "unset-workspace-name",
    "focus-monitor-left",
    "focus-monitor-right",
    "focus-monitor-down",
    "focus-monitor-up",
    "focus-monitor-previous",
    "focus-monitor-next",
    "focus-monitor",
    "move-window-to-monitor-left",
    "move-window-to-monitor-right",
    "move-window-to-monitor-down",
    "move-window-to-monitor-up",
    "move-window-to-monitor-previous",
    "move-window-to-monitor-next",
    "move-window-to-monitor",
    "move-column-to-monitor-left",
    "move-column-to-monitor-right",
    "move-column-to-monitor-down",
    "move-column-to-monitor-up",
    "move-column-to-monitor-previous",
    "move-column-to-monitor-next",
    "move-column-to-monitor",
    "set-window-width",
    "set-window-height",
    "reset-window-height",
    "switch-preset-column-width",
    "switch-preset-column-width-back",
    "switch-preset-window-width",
    "switch-preset-window-width-back",
    "switch-preset-window-height",
    "switch-preset-window-height-back",
    "maximize-column",
    "maximize-window-to-edges",
    "set-column-width",
    "expand-column-to-available-width",
    "switch-layout",
    "show-hotkey-overlay",
    "move-workspace-to-monitor-left",
    "move-workspace-to-monitor-right",
    "move-workspace-to-monitor-down",
    "move-workspace-to-monitor-up",
    "move-workspace-to-monitor-previous",
    "move-workspace-to-monitor-next",
    "move-workspace-to-monitor",
    "toggle-debug-tint",
    "debug-toggle-opaque-regions",
    "debug-toggle-damage",
    "toggle-window-floating",
    "move-window-to-floating",
    "move-window-to-tiling",
    "focus-floating",
    "focus-tiling",
    "switch-focus-between-floating-and-tiling",
    "move-floating-window",
    "toggle-window-rule-opacity",
    "set-dynamic-cast-window",
    "set-dynamic-cast-monitor",
    "clear-dynamic-cast-target",
    "toggle-overview",
    "open-overview",
    "close-overview",
    "toggle-window-urgent",
    "set-window-urgent",
    "unset-window-urgent",
    "load-config-file",
]


def _kebab_to_pascal(s: str):
    return to_pascal(to_snake(s))


class Instance:
    """High-level interface to Niri window manager.

    Provides methods to query and control the Niri window manager via IPC socket.
    Handles communication with Niri, model validation, and state management.
    """

    socket: Socket
    """The IPC socket connection to Niri."""
    version: str
    """The version string of the connected Niri instance."""

    def __init__(self):
        """Initialize a connection to the Niri window manager.

        Establishes a socket connection and queries the Niri version.

        Raises:
            RuntimeError: If $NIRI_SOCKET is not set and no socket is available.
            FileNotFoundError: If the Niri socket does not exist.
            ConnectionRefusedError: If unable to connect to the Niri socket.

        Example:
            >>> instance = Instance()
            >>> print(f"Connected to Niri {instance.version}")
        """
        self.socket = Socket()
        self.version = self._request("version").version or "unknown"

    @override
    def __repr__(self) -> str:
        return f"<Instance(socket={str(self.socket.path)!r})>"

    def _request(self, command: RequestCmd) -> Response:
        command_str = _kebab_to_pascal(command)
        reply = Reply.model_validate_json(
            self.socket.send_command(command_str),
            context={"instance": self},
        )
        return reply.unwrap()

    def action(self, action: ActionCmd, **kwargs: Any) -> bool:
        """Execute an action command in Niri.

        Sends an action command to Niri with optional parameters and returns
        whether the action was handled.

        Args:
            action (ActionCmd): The action to execute (e.g., "quit", "focus-window").
            **kwargs: Additional parameters for the action. Parameter names are
                case-sensitive and should match Niri's expected format.

        Returns:
            True if the action was handled by Niri, False otherwise.

        Example:
            >>> instance = Instance()
            >>> # Close the current window
            >>> instance.action("close-window")
            True
            >>>
            >>> # Focus workspace by index
            >>> instance.action("focus-workspace", index=1)
            True
        """
        action_str = _kebab_to_pascal(action)
        request: dict[str, Any] = {"Action": {action_str: {}}}
        for k, v in kwargs.items():
            request["Action"][action_str].update({k: v})
        reply = Reply.model_validate_json(
            self.socket.send_command(request),
            context={"instance": self},
        )
        return reply.unwrap().handled or False

    def get_windows(self) -> list[Window]:
        """Get all open windows in Niri.

        Returns:
            A list of all currently open windows. Returns an empty
                list if no windows are open.

        Example:
            >>> instance = Instance()
            >>> windows = instance.get_windows()
            >>> for window in windows:
            ...     print(f"Title: {window.title}")
        """
        return self._request("windows").windows or []

    def get_focused_window(self) -> Window:
        """Get the currently focused window.

        Returns:
            The window that currently has keyboard focus.

        Raises:
            ValueError: If no window is focused.

        Example:
            >>> instance = Instance()
            >>> focused = instance.get_focused_window()
        """
        focused_window = self._request("focused-window").focused_window
        if focused_window is None:
            raise ValueError("Unable to retrieve focused window")
        return focused_window

    def get_window_by_id(self, window_id: int) -> Window | None:
        """Get a window by its ID.

        Args:
            window_id (int): The ID of the window to retrieve.

        Returns:
            The window with the given ID, or None if not found.

        Example:
            >>> instance = Instance()
            >>> window = instance.get_window_by_id(12345)
            >>> if window:
            ...     print(f"Found: {window.title}")
        """
        for window in self.get_windows():
            if window.id == window_id:
                return window

    def get_workspaces(self) -> list[Workspace]:
        """Get all workspaces.

        Returns:
            A list of all workspaces. Returns an empty list if
                no workspaces exist.

        Example:
            >>> instance = Instance()
            >>> workspaces = instance.get_workspaces()
            >>> for ws in workspaces:
            ...     print(f"Workspace: {ws.name}, Focused: {ws.is_focused}")
        """
        return self._request("workspaces").workspaces or []

    def get_focused_workspace(self) -> Workspace:
        """Get the currently focused workspace.

        Returns:
            The workspace that currently has focus.

        Raises:
            ValueError: If no workspace is focused.

        Example:
            >>> instance = Instance()
            >>> focused = instance.get_focused_workspace()
            >>> print(f"Focused workspace: {focused.name}")
        """
        focused_workspace = next(
            (ws for ws in self.get_workspaces() if ws.is_focused), None
        )
        if focused_workspace is None:
            raise ValueError("Unable to retrieve focused workspace")
        return focused_workspace

    def get_workspace_by_id(self, workspace_id: int) -> Workspace | None:
        """Get a workspace by its ID.

        Args:
            workspace_id (int): The ID of the workspace to retrieve.

        Returns:
            The workspace with the given ID, or None if not found.

        Example:
            >>> instance = Instance()
            >>> workspace = instance.get_workspace_by_id(1)
            >>> if workspace:
            ...     print(f"Found workspace: {workspace.name}")
        """
        for workspace in self.get_workspaces():
            if workspace.id == workspace_id:
                return workspace

    def get_workspace_by_name(self, name: str) -> Workspace | None:
        """Get a workspace by its name.

        Args:
            name (str): The name of the workspace to retrieve.

        Returns:
            The workspace with the given name, or None if not
                found.

        Example:
            >>> instance = Instance()
            >>> workspace = instance.get_workspace_by_name("work")
            >>> if workspace:
            ...     print(f"Found workspace: {workspace.id}")
        """
        for workspace in self.get_workspaces():
            if workspace.name == name:
                return workspace

    def get_outputs(self) -> list[Output]:
        """Get all connected monitors/outputs.

        Returns:
            A list of all connected outputs (monitors). Returns an
                empty list if no outputs are connected.

        Example:
            >>> instance = Instance()
            >>> outputs = instance.get_outputs()
            >>> for output in outputs:
            ...     print(f"Monitor: {output.name}, Width: {output.physical_size}")
        """
        return list((self._request("outputs").outputs or {}).values())

    def get_focused_output(self) -> Output:
        """Get the currently focused monitor/output.

        Returns:
            The output that currently has focus (where the cursor is).

        Raises:
            ValueError: If no output is focused.

        Example:
            >>> instance = Instance()
            >>> output = instance.get_focused_output()
            >>> print(f"Focused monitor: {output.name}")
        """
        focused_output = self._request("focused-output").focused_output
        if focused_output is None:
            raise ValueError("Unable to retrieve focused output")
        return focused_output

    def get_output_by_name(self, name: str) -> Output | None:
        """Get an output (monitor) by its name.

        Args:
            name (str): The name of the output (e.g., "HDMI-1", "DP-2").

        Returns:
            The output with the given name, or None if not found.

        Example:
            >>> instance = Instance()
            >>> output = instance.get_output_by_name("HDMI-1")
            >>> if output:
            ...     print(f"Found monitor: {output.name}")
        """
        outputs = self._request("outputs").outputs or {}
        return outputs.get(name)

    def get_layers(self) -> list[LayerSurface]:
        """Get all layer surfaces.

        Returns:
            A list of all layer surfaces (e.g., panels,
                backgrounds). Returns an empty list if no layer surfaces exist.

        Example:
            >>> instance = Instance()
            >>> layers = instance.get_layers()
            >>> for layer in layers:
            ...     print(f"Layer: {layer.namespace}")
        """
        return self._request("layers").layers or []

    def subscribe(self) -> Generator[NiriEvent, None, None]:
        """Subscribe to an event stream.

        Yields:
            NiriEvent: Events received from Niri.

        Example:
            >>> for event in instance.subscribe():
            ...     print(event)
            ...     if condition:
            ...         break
        """
        event_stream = self.socket.event_stream()
        # first message on stream is a reply, no event:
        reply_json = next(event_stream)
        reply = Reply.model_validate_json(
            reply_json,
            context={"instance": self},
        )
        # Ensure the subscription was successful
        _ = reply.unwrap()

        for line in event_stream:
            try:
                event = NiriEvent.from_json(line, context={"instance": self})
                yield event
            except Exception as e:
                print(f"Error processing event: {e}")
                continue
