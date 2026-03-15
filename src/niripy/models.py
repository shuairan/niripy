from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING, Any, override

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_pascal

if TYPE_CHECKING:
    from niripy.instances import Instance


class ReplyError(Exception):
    """Exception raised when an error occurs while processing a Niri reply.

    This exception is raised when:
    - Niri returns an error response
    - A reply cannot be unwrapped/parsed
    - A response doesn't contain expected fields

    Example:
        >>> from niripy.models import Reply, ReplyError
        >>> try:
        ...     reply = Reply.model_validate_json(error_response)
        ...     reply.unwrap()
        ... except ReplyError as e:
        ...     print(f"Niri error: {e}")
    """

    pass


class _NiriModel(BaseModel):
    """Base model for Niri objects that need access to the Instance.

    This is a Pydantic BaseModel that stores a reference to the Instance,
    allowing models to query related objects and state from Niri.

    Attributes:
        _instance (Instance): Reference to the connected Niri instance.

    Note:
        When validating models that inherit from this, always pass
        `context={'instance': instance}` to `model_validate()`.

    Example:
        >>> from niripy.instances import Instance
        >>> from niripy.models import Window
        >>> instance = Instance()
        >>> window_data = {"id": 1, "title": "Test", ...}
        >>> window = Window.model_validate(window_data, context={'instance': instance})
    """

    _instance: Instance

    @override
    def model_post_init(self, context: Any):
        """Post-initialization hook to validate and store the instance context.

        Args:
            context (Any): Validation context. Must be a dict with 'instance' key.

        Raises:
            AssertionError: If context doesn't contain the 'instance' key.
        """
        if not isinstance(context, dict) or "instance" not in context:
            raise AssertionError(
                "context['instance'] not defined: "  # pyright: ignore[reportImplicitStringConcatenation]
                "Make sure to validate with context={'instance': ...}. "
                "i.e. Model.model_validate(data, context={'instance': instance})"
            )
        self._instance = context["instance"]


class ConfiguredPosition(BaseModel):
    """A 2D [position][1] with integer coordinates.

    [1]: https://niri-wm.github.io/niri/niri_ipc/struct.ConfiguredPosition.html

    Attributes:
        x (int): X coordinate.
        y (int): Y coordinate.
    """

    x: int
    y: int


class KeyboardLayouts(BaseModel):
    """Information about available [keyboard layouts][1].

    [1]: https://niri-wm.github.io/niri/niri_ipc/struct.KeyboardLayouts.html

    Attributes:
        names (list[str]): List of available keyboard layout names.
        current_idx (int): Index of the currently active layout in the names list.
    """

    names: list[str]
    current_idx: int


class Layer(StrEnum):
    """Wayland [layer][1] shell layer types.

    Represents the different zwlr_layer_shell layers for positioning surfaces.
    [1]: https://niri-wm.github.io/niri/niri_ipc/enum.Layer.html

    Attributes:
        BACKGROUND: Background layer, below everything.
        BOTTOM: Above background, below normal windows.
        TOP: Above normal windows, below overlay.
        OVERLAY: Top layer, above everything.
    """

    BACKGROUND = "Background"
    BOTTOM = "Bottom"
    TOP = "Top"
    OVERLAY = "Overlay"


class LayerSurfaceKeyboardInteractivity(StrEnum):
    """[Layer surface keyboard interactivity][1] modes.

    Defines the keyboard interactivity behavior for layer surfaces in Wayland,
    controlling how keyboard input is handled and routed to the surface.
    [1]: https://niri-wm.github.io/niri/niri_ipc/enum.LayerSurfaceKeyboardInteractivity.html

    Attributes:
        NONE: Keyboard input is not delivered to the layer surface.
        EXCLUSIVE: The layer surface has exclusive keyboard focus and receives
            all keyboard input.
        ON_DEMAND: Keyboard input is delivered to the layer surface only when
            explicitly requested.
    """

    NONE = "None"
    EXCLUSIVE = "Exclusive"
    ON_DEMAND = "OnDemand"


class LayerSurface(_NiriModel):
    """A layer shell [surface][1] (e.g., panel, notification).

    Represents a surface from the Wayland layer shell protocol.
    [1]: https://niri-wm.github.io/niri/niri_ipc/struct.LayerSurface.html

    Attributes:
        namespace (str): The namespace/identifier of the surface.
        output_name (str): The name of the output this surface is on.
        layer (Layer): The layer this surface is placed in.
        keyboard_interactivity (LayerSurfaceKeyboardInteractivity): Keyboard
            interactivity mode for this surface.
    """

    namespace: str
    output_name: str = Field(alias="output")
    layer: Layer
    keyboard_interactivity: LayerSurfaceKeyboardInteractivity

    def get_output(self) -> Output | None:
        """Get the output this layer surface is displayed on.

        Returns:
            The output object, or None if not found.
        """
        return self._instance.get_output_by_name(self.output_name)


class Transform(StrEnum):
    """Image [transformation][1] operations.

    Represents various transformations that can be applied to images,
    including rotations and flips.
    [1]: https://niri-wm.github.io/niri/niri_ipc/enum.Transform.html

    Attributes:
        NORMAL: No transformation applied.
        ROTATE_90: Rotate image 90 degrees clockwise.
        ROTATE_180: Rotate image 180 degrees.
        ROTATE_270: Rotate image 270 degrees clockwise.
        FLIPPED: Flip image horizontally.
        FLIPPED_90: Flip image horizontally and rotate 90 degrees clockwise.
        FLIPPED_180: Flip image horizontally and rotate 180 degrees.
        FLIPPED_270: Flip image horizontally and rotate 270 degrees clockwise.
    """

    NORMAL = "Normal"
    ROTATE_90 = "90"
    ROTATE_180 = "180"
    ROTATE_270 = "270"
    FLIPPED = "Flipped"
    FLIPPED_90 = "Flipped90"
    FLIPPED_180 = "Flipped180"
    FLIPPED_270 = "Flipped270"


class LogicalOutput(BaseModel):
    """[Logical output][1] configuration and transformations.

    Represents the logical position and scaling of an output in a multi-monitor
    setup.
    [1]: https://niri-wm.github.io/niri/niri_ipc/struct.LogicalOutput.html

    Attributes:
        x (int): Logical X position in pixels.
        y (int): Logical Y position in pixels.
        width (int): Logical width in pixels.
        height (int): Logical height in pixels.
        scale (float): Scale factor for DPI (e.g., 2.0 for 200%).
        transform (Transform): Rotation and/or flip transformation.
    """

    x: int
    y: int
    width: int
    height: int
    scale: float
    transform: Transform


class Mode(BaseModel):
    """A display [mode][1] (resolution and refresh rate).

    [1]: https://niri-wm.github.io/niri/niri_ipc/struct.Mode.html

    Attributes:
        width (int): Resolution width in pixels.
        height (int): Resolution height in pixels.
        refresh_rate (int): Refresh rate in Hz.
        is_preferred (bool): Whether this is the preferred/native mode.
    """

    width: int
    height: int
    refresh_rate: int
    is_preferred: bool


class Output(_NiriModel):
    """A [monitor/output][1] device.

    Represents a connected display monitor with its capabilities and current state.
    [1]: https://niri-wm.github.io/niri/niri_ipc/struct.Output.html

    Attributes:
        name (str): Output identifier (e.g., "HDMI-1", "DP-2").
        make (str): Manufacturer name.
        model (str): Model designation.
        serial (str | None): Serial number if available.
        physical_size (tuple[int, int]): Physical dimensions in millimeters (width, height).
        modes (list[Mode]): Available display modes.
        current_mode (int | None): Index of current mode in modes list, or None if custom.
        is_custom_mode (bool): Whether the current mode is custom/manual.
        vrr_supported (bool): Whether variable refresh rate is supported.
        vrr_enabled (bool): Whether VRR is currently enabled.
        logical (LogicalOutput | None): Logical position and scaling info.
    """

    name: str
    make: str
    model: str
    serial: str | None
    physical_size: tuple[int, int]
    modes: list[Mode]
    current_mode: int | None
    is_custom_mode: bool
    vrr_supported: bool
    vrr_enabled: bool
    logical: LogicalOutput | None

    def get_workspaces(self) -> list[Workspace]:
        """Get all workspaces on this output.

        Returns:
            Workspaces displayed on this output.
        """
        return [
            ws for ws in self._instance.get_workspaces() if ws.output_name == self.name
        ]

    def get_layers(self) -> list[LayerSurface]:
        """Get all layer surfaces on this output.

        Returns:
            Layer surfaces (panels, notifications, etc.)
                on this output.
        """
        return [
            layer
            for layer in self._instance.get_layers()
            if layer.output_name == self.name
        ]

    def get_windows(self) -> list[Window]:
        """Get all windows on workspaces on this output.

        Returns:
            Windows from all workspaces on this output.
        """
        workspace_ids = [ws.id for ws in self.get_workspaces()]
        return [
            window
            for window in self._instance.get_windows()
            if window.workspace_id in workspace_ids
        ]


class Overview(BaseModel):
    """[Overview][1] mode state.

    [1]: https://niri-wm.github.io/niri/niri_ipc/struct.Overview.html

    Attributes:
        is_open (bool): Whether the overview is currently open/visible.
    """

    is_open: bool


# TODO: test colorpicker
class PickedColor(BaseModel):
    """A [color][1] picked by the color picker tool.

    [1]: https://niri-wm.github.io/niri/niri_ipc/struct.PickedColor.html

    Attributes:
        rgb (tuple[float, float, float]): RGB color values (typically 0-1 range).

    Note:
        This model is not fully tested yet.
    """

    rgb: tuple[float, float, float]


class Timestamp(BaseModel):
    """A [timestamp][1] with second and nanosecond precision.

    [1]: https://niri-wm.github.io/niri/niri_ipc/struct.Timestamp.html

    Attributes:
        seconds (int): Number of seconds.
        nanoseconds (int): Nanosecond component (0-999,999,999).
    """

    seconds: int = Field(alias="secs")
    nanoseconds: int = Field(alias="nanos")


class VrrToSet(BaseModel):
    """[VRR][1] (Variable Refresh Rate) settings to apply.

    [1]: https://niri-wm.github.io/niri/niri_ipc/struct.VrrToSet.html

    Attributes:
        vrr (bool): Whether to enable VRR.
        on_demand (bool): If true, VRR is only active during updates
            (power saving mode).
    """

    vrr: bool
    on_demand: bool


class WindowLayout(BaseModel):
    """[Layout information][1] for a window in the tiling layout.

    Contains positioning and sizing data for a window within Niri's tiling system.
    [1]: https://niri-wm.github.io/niri/niri_ipc/struct.WindowLayout.html

    Attributes:
        pos_in_scrolling_layout (tuple[int, int] | None): Position in scrolling layout.
        tile_size (tuple[float, float]): Size of the tile (width, height).
        window_size (tuple[int, int]): Actual window size in pixels (width, height).
        tile_pos_in_workspace_view (tuple[float, float] | None): Tile position
            in workspace view.
        window_offset_in_tile (tuple[float, float]): Offset of window content
            within its tile.
    """

    pos_in_scrolling_layout: tuple[int, int] | None
    tile_size: tuple[float, float]
    window_size: tuple[int, int]
    tile_pos_in_workspace_view: tuple[float, float] | None
    window_offset_in_tile: tuple[float, float]


class Window(_NiriModel):
    """A [Window][1] in the Niri compositor.

    Represents an open window with its state, position, and metadata.
    [1]: https://niri-wm.github.io/niri/niri_ipc/struct.Window.html

    Attributes:
        id (int): Unique window identifier.
        title (str | None): Window title if available.
        app_id (str | None): Application ID (from desktop file).
        pid (int | None): Process ID if available.
        workspace_id (int | None): ID of workspace containing this window.
        is_focused (bool): Whether this window has keyboard focus.
        is_floating (bool): Whether the window is floating (not tiled).
        is_urgent (bool): Whether the window has an urgent flag set.
        layout (WindowLayout): Tiling layout information.
        focus_timestamp (Timestamp | None): When this window was last focused.
    """

    id: int
    title: str | None
    app_id: str | None
    pid: int | None
    workspace_id: int | None
    is_focused: bool
    is_floating: bool
    is_urgent: bool
    layout: WindowLayout
    focus_timestamp: Timestamp | None

    def get_workspace(self) -> Workspace | None:
        """Get the workspace containing this window.

        Returns:
            The workspace, or None if not in any workspace.
        """
        if self.workspace_id is None:
            return None
        return self._instance.get_workspace_by_id(self.workspace_id)


class Workspace(_NiriModel):
    """A [workspace][1] (virtual desktop) in Niri.

    Represents a workspace that contains windows and is assigned to an output.
    [1]: https://niri-wm.github.io/niri/niri_ipc/struct.Workspace.html

    Attributes:
        id (int): Unique workspace identifier.
        idx (int): Index/order of this workspace.
        name (str | None): User-friendly workspace name if set.
        output_name (str | None): Name of the output this workspace is on.
        is_urgent (bool): Whether the workspace has an urgent flag set.
        is_active (bool): Whether this workspace is active (visible).
        is_focused (bool): Whether this workspace has keyboard focus.
        active_window_id (int | None): ID of the currently focused window.
    """

    id: int
    idx: int
    name: str | None
    output_name: str | None = Field(alias="output")
    is_urgent: bool
    is_active: bool
    is_focused: bool
    active_window_id: int | None

    def get_output(self) -> Output | None:
        """Get the output this workspace is displayed on.

        Returns:
            The output, or None if not assigned.
        """
        if self.output_name is None:
            return None
        return self._instance.get_output_by_name(self.output_name)

    def get_active_window(self) -> Window | None:
        """Get the currently focused window in this workspace.

        Returns:
            The active window, or None if no window is focused.
        """
        if self.active_window_id is None:
            return None
        return self._instance.get_window_by_id(self.active_window_id)

    def get_windows(self) -> list[Window]:
        """Get all windows in this workspace.

        Returns:
            All windows currently in this workspace.
        """
        return [
            window
            for window in self._instance.get_windows()
            if window.workspace_id == self.id
        ]


class OutputConfigChanged(StrEnum):
    """[Output configuration][1] change states.

    [1]: https://niri-wm.github.io/niri/niri_ipc/enum.OutputConfigChanged.html

    Attributes:
        APPLIED: Indicates that the output configuration change was successfully applied.
        OUTPUT_WAS_MISSING: Indicates that the output configuration change occurred because
                           the output was previously missing.
    """

    APPLIED = "Applied"
    OUTPUT_WAS_MISSING = "OutputWasMissing"


class CastKind(StrEnum):
    """Available [casting/screen capture][1] backends.

    [1]: https://niri-wm.github.io/niri/niri_ipc/enum.CastKind.html

    Attributes:
        PIPEWIRE: PipeWire audio/video server backend for screen casting.
        WLR_SCREENCOPY: Wlroots screencopy protocol backend for screen capture.
    """

    PIPEWIRE = "PipeWire"
    WLR_SCREENCOPY = "WlrScreencopy"


class CastTarget(BaseModel):
    """[Target][1] of a screen cast (what to record).

    One of the three fields should be set to indicate the cast target.
    [1]: https://niri-wm.github.io/niri/niri_ipc/enum.CastTarget.html

    Attributes:
        nothing (dict[str, str] | None): No specific target (background, etc.).
        output (dict[str, str] | None): Cast a specific output/monitor.
        window (dict[str, int] | None): Cast a specific window.
    """

    model_config = ConfigDict(alias_generator=to_pascal)  # pyright: ignore[reportUnannotatedClassAttribute]
    nothing: dict[str, str] | None = None
    output: dict[str, str] | None = None
    window: dict[str, int] | None = None


# TODO: test screencasting
class Cast(BaseModel):
    """An active [screen cast][1] session.

    Represents a screen capture/recording session.
    [1]: https://niri-wm.github.io/niri/niri_ipc/struct.Cast.html

    Attributes:
        stream_id (int): Stream identifier.
        session_id (int): Session identifier.
        kind (CastKind): The casting protocol used.
        target (CastTarget): What is being cast (output/window/etc).
        is_dynamic_target (bool): Whether the target can change during cast.
        is_active (bool): Whether the cast is currently active.
        pid (int | None): Process ID of the casting application.
        pw_node_id (int | None): PipeWire node ID if using PipeWire.

    Note:
        Screen casting is not fully tested yet.
    """

    stream_id: int
    session_id: int
    kind: CastKind
    target: CastTarget
    is_dynamic_target: bool
    is_active: bool
    pid: int | None
    pw_node_id: int | None


class Response(BaseModel):
    """A [response][1] from a Niri IPC request.

    Contains the result of a request, with one of the fields populated depending
    on the request type.
    [1]: https://niri-wm.github.io/niri/niri_ipc/enum.Response.html

    Attributes:
        handled (bool | None): Whether an action was handled.
        version (str | None): Niri version string.
        outputs (dict[str, Output] | None): Map of output names to Output objects.
        workspaces (list[Workspace] | None): List of all workspaces.
        windows (list[Window] | None): List of all windows.
        layers (list[LayerSurface] | None): List of layer surfaces.
        keyboard_layouts (KeyboardLayouts | None): Available keyboard layouts.
        focused_output (Output | None): The currently focused output.
        focused_window (Window | None): The currently focused window.
        picked_window (Window | None): Window selected by pick-window action.
        picked_color (PickedColor | None): Color selected by pick-color action.
        output_config_changed (OutputConfigChanged | None): Status of output config change.
        overview_state (Overview | None): Overview mode state.
        casts (list[Cast] | None): List of active screen casts.
    """

    model_config = ConfigDict(alias_generator=to_pascal)  # pyright: ignore[reportUnannotatedClassAttribute]
    handled: bool | None = None
    version: str | None = None
    outputs: dict[str, Output] | None = None
    workspaces: list[Workspace] | None = None
    windows: list[Window] | None = None
    layers: list[LayerSurface] | None = None
    keyboard_layouts: KeyboardLayouts | None = None
    focused_output: Output | None = None
    focused_window: Window | None = None
    picked_window: Window | None = None
    picked_color: PickedColor | None = None
    output_config_changed: OutputConfigChanged | None = None
    overview_state: Overview | None = None
    casts: list[Cast] | None = None

    @model_validator(mode="before")
    @classmethod
    def _validate_handled(cls, data: Any) -> Any:
        return {"Handled": True} if data == "Handled" else data

    def unwrap(self) -> Any:
        """Extract the meaningful field from the response.

        Returns the first non-None field from the response. Useful for extracting
        the actual response value after validation.

        Returns:
            The first non-None response field.

        Raises:
            ReplyError: If all fields are None.

        Example:
            >>> reply = Reply.model_validate_json(json_data, context={'instance': instance})
            >>> response = reply.unwrap()
            >>> windows = response.unwrap()  # Extract the actual data
        """
        for value in self.model_dump().values():
            if value is not None:
                return value
        raise ReplyError("Response does not contain any known fields.")


class Reply(BaseModel):
    """A Niri IPC protocol [reply][1].

    Wraps a Response with success/error indication. Either `ok` or `err`
    will be set, never both.
    [1]: https://niri-wm.github.io/niri/niri_ipc/type.Reply.html

    Attributes:
        ok (Response | None): The response data if the request succeeded.
        err (str | None): Error message if the request failed.

    Example:
        >>> from niripy.instances import Instance
        >>> instance = Instance()
        >>> json_data = instance.socket.send_command({"Outputs": {}})
        >>> reply = Reply.model_validate_json(json_data, context={'instance': instance})
        >>> response = reply.unwrap()  # Raises ReplyError if err is set
        >>> windows = response.unwrap()  # Extract the actual data
    """

    model_config = ConfigDict(alias_generator=to_pascal)  # pyright: ignore[reportUnannotatedClassAttribute]
    ok: Response | None = None
    err: str | None = None

    def unwrap(self) -> Response:
        """Extract the response or raise an error.

        Returns:
            The ok response if present.

        Raises:
            ReplyError: If the reply contains an error.

        Example:
            >>> reply = Reply.model_validate_json(data, context={'instance': instance})
            >>> response = reply.unwrap()  # Raises if err is set
        """
        if self.err is not None:
            raise ReplyError(f"Niri replied with error: {self.err}")
        assert self.ok is not None
        return self.ok
