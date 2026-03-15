"""Tests for niripy.models module."""

from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from niripy.models import (
    Cast,
    CastKind,
    CastTarget,
    ConfiguredPosition,
    KeyboardLayouts,
    Layer,
    LayerSurface,
    LayerSurfaceKeyboardInteractivity,
    LogicalOutput,
    Mode,
    Output,
    OutputConfigChanged,
    Overview,
    PickedColor,
    Reply,
    ReplyError,
    Response,
    Timestamp,
    Transform,
    VrrToSet,
    Window,
    WindowLayout,
    Workspace,
)


@pytest.fixture
def mock_instance():
    """Create a mock Instance for testing."""
    return MagicMock()


class TestConfiguredPosition:
    """Tests for ConfiguredPosition model."""

    def test_create_configured_position(self):
        """Test creating a ConfiguredPosition."""
        pos = ConfiguredPosition(x=100, y=200)
        assert pos.x == 100
        assert pos.y == 200

    def test_configured_position_negative_values(self):
        """Test ConfiguredPosition with negative values."""
        pos = ConfiguredPosition(x=-50, y=-100)
        assert pos.x == -50
        assert pos.y == -100

    def test_configured_position_zero_values(self):
        """Test ConfiguredPosition with zero values."""
        pos = ConfiguredPosition(x=0, y=0)
        assert pos.x == 0
        assert pos.y == 0


class TestKeyboardLayouts:
    """Tests for KeyboardLayouts model."""

    def test_create_keyboard_layouts(self):
        """Test creating KeyboardLayouts."""
        kb_layouts = KeyboardLayouts(names=["us", "de", "fr"], current_idx=1)
        assert kb_layouts.names == ["us", "de", "fr"]
        assert kb_layouts.current_idx == 1

    def test_keyboard_layouts_empty_list(self):
        """Test KeyboardLayouts with empty list."""
        kb_layouts = KeyboardLayouts(names=[], current_idx=0)
        assert kb_layouts.names == []
        assert kb_layouts.current_idx == 0

    def test_keyboard_layouts_single_layout(self):
        """Test KeyboardLayouts with single layout."""
        kb_layouts = KeyboardLayouts(names=["us"], current_idx=0)
        assert len(kb_layouts.names) == 1


class TestLayerEnum:
    """Tests for Layer enum."""

    def test_layer_values(self):
        """Test all Layer enum values."""
        assert Layer.BACKGROUND.value == "Background"
        assert Layer.BOTTOM.value == "Bottom"
        assert Layer.TOP.value == "Top"
        assert Layer.OVERLAY.value == "Overlay"

    def test_layer_enum_members(self):
        """Test Layer enum has all expected members."""
        members = [layer.name for layer in Layer]
        assert "BACKGROUND" in members
        assert "BOTTOM" in members
        assert "TOP" in members
        assert "OVERLAY" in members


class TestLayerSurfaceKeyboardInteractivityEnum:
    """Tests for LayerSurfaceKeyboardInteractivity enum."""

    def test_keyboard_interactivity_values(self):
        """Test all LayerSurfaceKeyboardInteractivity enum values."""
        assert LayerSurfaceKeyboardInteractivity.NONE.value == "None"
        assert LayerSurfaceKeyboardInteractivity.EXCLUSIVE.value == "Exclusive"
        assert LayerSurfaceKeyboardInteractivity.ON_DEMAND.value == "OnDemand"


class TestLayerSurface:
    """Tests for LayerSurface model."""

    def test_create_layer_surface(self, mock_instance):
        """Test creating a LayerSurface."""
        layer = LayerSurface.model_validate(
            {
                "namespace": "test",
                "output": "eDP-1",
                "layer": Layer.TOP,
                "keyboard_interactivity": LayerSurfaceKeyboardInteractivity.NONE,
            },
            context={"instance": mock_instance},
        )
        assert layer.namespace == "test"
        assert layer.output_name == "eDP-1"
        assert layer.layer == Layer.TOP
        assert layer.keyboard_interactivity == LayerSurfaceKeyboardInteractivity.NONE

    def test_layer_surface_model_post_init_requires_instance(self):
        """Test LayerSurface requires instance in context."""
        with pytest.raises(ValidationError, match="context"):
            LayerSurface.model_validate(
                {
                    "namespace": "test",
                    "output": "eDP-1",
                    "layer": Layer.TOP,
                    "keyboard_interactivity": LayerSurfaceKeyboardInteractivity.NONE,
                }
            )

    def test_layer_surface_output_property(self, mock_instance):
        """Test LayerSurface output property."""
        mock_output = MagicMock()
        mock_instance.get_output_by_name.return_value = mock_output

        layer = LayerSurface.model_validate(
            {
                "namespace": "test",
                "output": "eDP-1",
                "layer": Layer.TOP,
                "keyboard_interactivity": LayerSurfaceKeyboardInteractivity.NONE,
            },
            context={"instance": mock_instance},
        )

        output = layer.get_output()
        assert output == mock_output
        mock_instance.get_output_by_name.assert_called_once_with("eDP-1")

    def test_layer_surface_with_alias(self, mock_instance):
        """Test LayerSurface uses 'output' alias for 'output_name'."""
        layer = LayerSurface.model_validate(
            {
                "namespace": "panel",
                "output": "HDMI-1",
                "layer": Layer.BOTTOM,
                "keyboard_interactivity": LayerSurfaceKeyboardInteractivity.EXCLUSIVE,
            },
            context={"instance": mock_instance},
        )
        assert layer.output_name == "HDMI-1"


class TestTransformEnum:
    """Tests for Transform enum."""

    def test_transform_values(self):
        """Test Transform enum values."""
        assert Transform.NORMAL.value == "Normal"
        assert Transform.ROTATE_90.value == "90"
        assert Transform.ROTATE_180.value == "180"
        assert Transform.FLIPPED.value == "Flipped"


class TestLogicalOutput:
    """Tests for LogicalOutput model."""

    def test_create_logical_output(self):
        """Test creating a LogicalOutput."""
        logical = LogicalOutput(
            x=0,
            y=0,
            width=1920,
            height=1080,
            scale=1.0,
            transform=Transform.NORMAL,
        )
        assert logical.x == 0
        assert logical.y == 0
        assert logical.width == 1920
        assert logical.height == 1080
        assert logical.scale == 1.0
        assert logical.transform == Transform.NORMAL

    def test_logical_output_with_scale(self):
        """Test LogicalOutput with different scales."""
        logical = LogicalOutput(
            x=100,
            y=200,
            width=1920,
            height=1080,
            scale=2.0,
            transform=Transform.NORMAL,
        )
        assert logical.scale == 2.0

    def test_logical_output_with_transform(self):
        """Test LogicalOutput with rotation."""
        logical = LogicalOutput(
            x=0,
            y=0,
            width=1080,
            height=1920,
            scale=1.0,
            transform=Transform.ROTATE_90,
        )
        assert logical.transform == Transform.ROTATE_90


class TestMode:
    """Tests for Mode model."""

    def test_create_mode(self):
        """Test creating a Mode."""
        mode = Mode(
            width=1920,
            height=1080,
            refresh_rate=60,
            is_preferred=True,
        )
        assert mode.width == 1920
        assert mode.height == 1080
        assert mode.refresh_rate == 60
        assert mode.is_preferred is True

    def test_mode_not_preferred(self):
        """Test Mode with is_preferred=False."""
        mode = Mode(
            width=1024,
            height=768,
            refresh_rate=75,
            is_preferred=False,
        )
        assert mode.is_preferred is False

    def test_mode_high_refresh_rate(self):
        """Test Mode with high refresh rate."""
        mode = Mode(
            width=2560,
            height=1440,
            refresh_rate=144,
            is_preferred=True,
        )
        assert mode.refresh_rate == 144


class TestOutput:
    """Tests for Output model."""

    def test_create_output(self, mock_instance):
        """Test creating an Output."""
        output = Output.model_validate(
            {
                "name": "eDP-1",
                "make": "Unknown",
                "model": "Unknown",
                "serial": None,
                "physical_size": (390, 220),
                "modes": [],
                "current_mode": None,
                "is_custom_mode": False,
                "vrr_supported": False,
                "vrr_enabled": False,
                "logical": None,
            },
            context={"instance": mock_instance},
        )
        assert output.name == "eDP-1"
        assert output.make == "Unknown"
        assert output.physical_size == (390, 220)

    def test_output_with_modes(self, mock_instance):
        """Test Output with modes."""
        modes = [
            {"width": 1920, "height": 1080, "refresh_rate": 60, "is_preferred": True},
            {"width": 1920, "height": 1080, "refresh_rate": 75, "is_preferred": False},
        ]
        output = Output.model_validate(
            {
                "name": "HDMI-1",
                "make": "Samsung",
                "model": "S27A700",
                "serial": "12345678",
                "physical_size": (610, 340),
                "modes": modes,
                "current_mode": 0,
                "is_custom_mode": False,
                "vrr_supported": True,
                "vrr_enabled": True,
                "logical": {
                    "x": 0,
                    "y": 0,
                    "width": 1920,
                    "height": 1080,
                    "scale": 1.0,
                    "transform": "Normal",
                },
            },
            context={"instance": mock_instance},
        )
        assert len(output.modes) == 2
        assert output.current_mode == 0
        assert output.vrr_enabled is True

    def test_output_workspaces_property(self, mock_instance):
        """Test Output workspaces property."""
        mock_workspaces = [
            MagicMock(output_name="eDP-1"),
            MagicMock(output_name="HDMI-1"),
        ]
        mock_instance.get_workspaces.return_value = mock_workspaces

        output = Output.model_validate(
            {
                "name": "eDP-1",
                "make": "Unknown",
                "model": "Unknown",
                "serial": None,
                "physical_size": (390, 220),
                "modes": [],
                "current_mode": None,
                "is_custom_mode": False,
                "vrr_supported": False,
                "vrr_enabled": False,
                "logical": None,
            },
            context={"instance": mock_instance},
        )

        workspaces = output.get_workspaces()
        assert len(workspaces) == 1
        assert workspaces[0].output_name == "eDP-1"

    def test_output_layers_property(self, mock_instance):
        """Test Output layers property."""
        mock_layer1 = MagicMock(output_name="eDP-1")
        mock_layer2 = MagicMock(output_name="HDMI-1")
        mock_instance.get_layers.return_value = [mock_layer1, mock_layer2]

        output = Output.model_validate(
            {
                "name": "eDP-1",
                "make": "Unknown",
                "model": "Unknown",
                "serial": None,
                "physical_size": (390, 220),
                "modes": [],
                "current_mode": None,
                "is_custom_mode": False,
                "vrr_supported": False,
                "vrr_enabled": False,
                "logical": None,
            },
            context={"instance": mock_instance},
        )

        layers = output.get_layers()
        assert len(layers) == 1
        assert layers[0].output_name == "eDP-1"

    def test_output_windows_property(self, mock_instance):
        """Test Output windows property."""
        mock_ws1 = MagicMock(output_name="eDP-1", id=1)
        mock_ws2 = MagicMock(output_name="HDMI-1", id=2)
        mock_win1 = MagicMock(workspace_id=1)
        mock_win2 = MagicMock(workspace_id=2)
        mock_instance.get_workspaces.return_value = [mock_ws1, mock_ws2]
        mock_instance.get_windows.return_value = [mock_win1, mock_win2]

        output = Output.model_validate(
            {
                "name": "eDP-1",
                "make": "Unknown",
                "model": "Unknown",
                "serial": None,
                "physical_size": (390, 220),
                "modes": [],
                "current_mode": None,
                "is_custom_mode": False,
                "vrr_supported": False,
                "vrr_enabled": False,
                "logical": None,
            },
            context={"instance": mock_instance},
        )

        windows = output.get_windows()
        assert len(windows) == 1
        assert windows[0].workspace_id == 1


class TestOverview:
    """Tests for Overview model."""

    def test_create_overview_open(self):
        """Test creating an open Overview."""
        overview = Overview(is_open=True)
        assert overview.is_open is True

    def test_create_overview_closed(self):
        """Test creating a closed Overview."""
        overview = Overview(is_open=False)
        assert overview.is_open is False


class TestPickedColor:
    """Tests for PickedColor model."""

    def test_create_picked_color(self):
        """Test creating a PickedColor."""
        color = PickedColor(rgb=(1.0, 0.5, 0.2))
        assert color.rgb == (1.0, 0.5, 0.2)

    def test_picked_color_black(self):
        """Test PickedColor for black."""
        color = PickedColor(rgb=(0.0, 0.0, 0.0))
        assert color.rgb == (0.0, 0.0, 0.0)

    def test_picked_color_white(self):
        """Test PickedColor for white."""
        color = PickedColor(rgb=(1.0, 1.0, 1.0))
        assert color.rgb == (1.0, 1.0, 1.0)


class TestTimestamp:
    """Tests for Timestamp model."""

    def test_create_timestamp(self):
        """Test creating a Timestamp."""
        ts = Timestamp(secs=1000, nanos=500000000)
        assert ts.seconds == 1000
        assert ts.nanoseconds == 500000000

    def test_timestamp_zero(self):
        """Test Timestamp with zero values."""
        ts = Timestamp(secs=0, nanos=0)
        assert ts.seconds == 0
        assert ts.nanoseconds == 0


class TestVrrToSet:
    """Tests for VrrToSet model."""

    def test_vrr_to_set_enabled(self):
        """Test VrrToSet with vrr enabled."""
        vrr = VrrToSet(vrr=True, on_demand=False)
        assert vrr.vrr is True
        assert vrr.on_demand is False

    def test_vrr_to_set_on_demand(self):
        """Test VrrToSet with on-demand vrr."""
        vrr = VrrToSet(vrr=True, on_demand=True)
        assert vrr.vrr is True
        assert vrr.on_demand is True

    def test_vrr_to_set_disabled(self):
        """Test VrrToSet with vrr disabled."""
        vrr = VrrToSet(vrr=False, on_demand=False)
        assert vrr.vrr is False


class TestWindowLayout:
    """Tests for WindowLayout model."""

    def test_create_window_layout(self):
        """Test creating a WindowLayout."""
        layout = WindowLayout(
            pos_in_scrolling_layout=(10, 20),
            tile_size=(100.0, 200.0),
            window_size=(96, 192),
            tile_pos_in_workspace_view=(5.0, 10.0),
            window_offset_in_tile=(2.0, 4.0),
        )
        assert layout.pos_in_scrolling_layout == (10, 20)
        assert layout.tile_size == (100.0, 200.0)
        assert layout.window_size == (96, 192)

    def test_window_layout_none_scrolling_position(self):
        """Test WindowLayout with None scrolling position."""
        layout = WindowLayout(
            pos_in_scrolling_layout=None,
            tile_size=(100.0, 200.0),
            window_size=(96, 192),
            tile_pos_in_workspace_view=None,
            window_offset_in_tile=(2.0, 4.0),
        )
        assert layout.pos_in_scrolling_layout is None
        assert layout.tile_pos_in_workspace_view is None


class TestWindow:
    """Tests for Window model."""

    def test_create_window(self, mock_instance):
        """Test creating a Window."""
        window = Window.model_validate(
            {
                "id": 1,
                "title": "Test Window",
                "app_id": "test-app",
                "pid": 1234,
                "workspace_id": 1,
                "is_focused": True,
                "is_floating": False,
                "is_urgent": False,
                "layout": {
                    "pos_in_scrolling_layout": (0, 0),
                    "tile_size": (1920.0, 1080.0),
                    "window_size": (1920, 1080),
                    "tile_pos_in_workspace_view": (0.0, 0.0),
                    "window_offset_in_tile": (0.0, 0.0),
                },
                "focus_timestamp": None,
            },
            context={"instance": mock_instance},
        )
        assert window.id == 1
        assert window.title == "Test Window"
        assert window.app_id == "test-app"
        assert window.is_focused is True

    def test_window_with_timestamp(self, mock_instance):
        """Test Window with focus timestamp."""
        window = Window.model_validate(
            {
                "id": 2,
                "title": None,
                "app_id": "firefox",
                "pid": 5678,
                "workspace_id": 2,
                "is_focused": False,
                "is_floating": True,
                "is_urgent": True,
                "layout": {
                    "pos_in_scrolling_layout": None,
                    "tile_size": (500.0, 500.0),
                    "window_size": (500, 500),
                    "tile_pos_in_workspace_view": None,
                    "window_offset_in_tile": (0.0, 0.0),
                },
                "focus_timestamp": {"secs": 100, "nanos": 500000000},
            },
            context={"instance": mock_instance},
        )
        assert window.id == 2
        assert window.focus_timestamp is not None
        assert window.focus_timestamp.seconds == 100

    def test_window_workspace_property(self, mock_instance):
        """Test Window workspace property."""
        mock_workspace = MagicMock()
        mock_instance.get_workspace_by_id.return_value = mock_workspace

        window = Window.model_validate(
            {
                "id": 1,
                "title": "Test",
                "app_id": "test",
                "pid": 1234,
                "workspace_id": 1,
                "is_focused": False,
                "is_floating": False,
                "is_urgent": False,
                "layout": {
                    "pos_in_scrolling_layout": None,
                    "tile_size": (100.0, 100.0),
                    "window_size": (100, 100),
                    "tile_pos_in_workspace_view": None,
                    "window_offset_in_tile": (0.0, 0.0),
                },
                "focus_timestamp": None,
            },
            context={"instance": mock_instance},
        )

        workspace = window.get_workspace()
        assert workspace == mock_workspace
        mock_instance.get_workspace_by_id.assert_called_once_with(1)

    def test_window_workspace_property_none(self, mock_instance):
        """Test Window workspace property when workspace_id is None."""
        window = Window.model_validate(
            {
                "id": 1,
                "title": "Test",
                "app_id": "test",
                "pid": 1234,
                "workspace_id": None,
                "is_focused": False,
                "is_floating": False,
                "is_urgent": False,
                "layout": {
                    "pos_in_scrolling_layout": None,
                    "tile_size": (100.0, 100.0),
                    "window_size": (100, 100),
                    "tile_pos_in_workspace_view": None,
                    "window_offset_in_tile": (0.0, 0.0),
                },
                "focus_timestamp": None,
            },
            context={"instance": mock_instance},
        )

        workspace = window.get_workspace()
        assert workspace is None


class TestWorkspace:
    """Tests for Workspace model."""

    def test_create_workspace(self, mock_instance):
        """Test creating a Workspace."""
        workspace = Workspace.model_validate(
            {
                "id": 1,
                "idx": 0,
                "name": "Workspace 1",
                "output": "eDP-1",
                "is_urgent": False,
                "is_active": True,
                "is_focused": True,
                "active_window_id": 1,
            },
            context={"instance": mock_instance},
        )
        assert workspace.id == 1
        assert workspace.idx == 0
        assert workspace.name == "Workspace 1"
        assert workspace.output_name == "eDP-1"
        assert workspace.is_active is True

    def test_workspace_output_property(self, mock_instance):
        """Test Workspace output property."""
        mock_output = MagicMock()
        mock_instance.get_output_by_name.return_value = mock_output

        workspace = Workspace.model_validate(
            {
                "id": 1,
                "idx": 0,
                "name": None,
                "output": "HDMI-1",
                "is_urgent": False,
                "is_active": False,
                "is_focused": False,
                "active_window_id": None,
            },
            context={"instance": mock_instance},
        )

        output = workspace.get_output()
        assert output == mock_output
        mock_instance.get_output_by_name.assert_called_once_with("HDMI-1")

    def test_workspace_output_property_none(self, mock_instance):
        """Test Workspace output property when output_name is None."""
        workspace = Workspace.model_validate(
            {
                "id": 1,
                "idx": 0,
                "name": "Test",
                "output": None,
                "is_urgent": False,
                "is_active": False,
                "is_focused": False,
                "active_window_id": None,
            },
            context={"instance": mock_instance},
        )

        output = workspace.get_output()
        assert output is None

    def test_workspace_active_window_property(self, mock_instance):
        """Test Workspace active_window property."""
        mock_window = MagicMock()
        mock_instance.get_window_by_id.return_value = mock_window

        workspace = Workspace.model_validate(
            {
                "id": 1,
                "idx": 0,
                "name": "Test",
                "output": "eDP-1",
                "is_urgent": False,
                "is_active": True,
                "is_focused": True,
                "active_window_id": 42,
            },
            context={"instance": mock_instance},
        )

        window = workspace.get_active_window()
        assert window == mock_window
        mock_instance.get_window_by_id.assert_called_once_with(42)

    def test_workspace_active_window_property_none(self, mock_instance):
        """Test Workspace active_window property when active_window_id is None."""
        workspace = Workspace.model_validate(
            {
                "id": 1,
                "idx": 0,
                "name": "Test",
                "output": "eDP-1",
                "is_urgent": False,
                "is_active": False,
                "is_focused": False,
                "active_window_id": None,
            },
            context={"instance": mock_instance},
        )

        window = workspace.get_active_window()
        assert window is None

    def test_workspace_windows_property(self, mock_instance):
        """Test Workspace windows property."""
        mock_win1 = MagicMock(workspace_id=1)
        mock_win2 = MagicMock(workspace_id=2)
        mock_instance.get_windows.return_value = [mock_win1, mock_win2]

        workspace = Workspace.model_validate(
            {
                "id": 1,
                "idx": 0,
                "name": "Test",
                "output": "eDP-1",
                "is_urgent": False,
                "is_active": True,
                "is_focused": True,
                "active_window_id": None,
            },
            context={"instance": mock_instance},
        )

        windows = workspace.get_windows()
        assert len(windows) == 1
        assert windows[0].workspace_id == 1


class TestOutputConfigChangedEnum:
    """Tests for OutputConfigChanged enum."""

    def test_output_config_changed_values(self):
        """Test OutputConfigChanged enum values."""
        assert OutputConfigChanged.APPLIED.value == "Applied"
        assert OutputConfigChanged.OUTPUT_WAS_MISSING.value == "OutputWasMissing"


class TestCastKindEnum:
    """Tests for CastKind enum."""

    def test_cast_kind_values(self):
        """Test CastKind enum values."""
        assert CastKind.PIPEWIRE.value == "PipeWire"
        assert CastKind.WLR_SCREENCOPY.value == "WlrScreencopy"


class TestCastTarget:
    """Tests for CastTarget model."""

    def test_create_cast_target_nothing(self):
        """Test creating CastTarget with nothing."""
        target = CastTarget.model_validate({"Nothing": None})
        assert target.nothing is None

    def test_create_cast_target_output(self):
        """Test creating CastTarget with output."""
        target = CastTarget.model_validate({"Output": {"name": "eDP-1"}})
        assert target.output == {"name": "eDP-1"}

    def test_create_cast_target_window(self):
        """Test creating CastTarget with window."""
        target = CastTarget.model_validate({"Window": {"id": 1}})
        assert target.window == {"id": 1}


class TestCast:
    """Tests for Cast model."""

    def test_create_cast(self):
        """Test creating a Cast."""
        cast = Cast(
            stream_id=1,
            session_id=100,
            kind=CastKind.PIPEWIRE,
            target=CastTarget(),
            is_dynamic_target=False,
            is_active=True,
            pid=5678,
            pw_node_id=42,
        )
        assert cast.stream_id == 1
        assert cast.session_id == 100
        assert cast.kind == CastKind.PIPEWIRE
        assert cast.is_active is True

    def test_create_cast_wlr_screencopy(self):
        """Test creating a Cast with WlrScreencopy."""
        cast = Cast(
            stream_id=2,
            session_id=200,
            kind=CastKind.WLR_SCREENCOPY,
            target=CastTarget.model_validate({"Output": {"name": "HDMI-1"}}),
            is_dynamic_target=True,
            is_active=False,
            pid=None,
            pw_node_id=None,
        )
        assert cast.kind == CastKind.WLR_SCREENCOPY
        assert cast.is_dynamic_target is True


class TestResponse:
    """Tests for Response model."""

    def test_response_handled(self):
        """Test Response with handled field."""
        response = Response.model_validate({"Handled": True})
        assert response.handled is True

    def test_response_handled_from_string(self):
        """Test Response handles 'Handled' string input."""
        response = Response.model_validate("Handled")
        assert response.handled is True

    def test_response_version(self):
        """Test Response with version field."""
        response = Response.model_validate({"Version": "0.1.0"})
        assert response.version == "0.1.0"

    def test_response_with_output(self, mock_instance):
        """Test Response with outputs field."""
        response = Response.model_validate(
            {
                "Outputs": {
                    "eDP-1": {
                        "name": "eDP-1",
                        "make": "Unknown",
                        "model": "Unknown",
                        "serial": None,
                        "physical_size": [390, 220],
                        "modes": [],
                        "current_mode": None,
                        "is_custom_mode": False,
                        "vrr_supported": False,
                        "vrr_enabled": False,
                        "logical": None,
                    }
                }
            },
            context={"instance": mock_instance},
        )
        assert response.outputs is not None
        assert "eDP-1" in response.outputs

    def test_response_unwrap_handled(self):
        """Test Response unwrap method with handled."""
        response = Response.model_validate({"Handled": True})
        unwrapped = response.unwrap()
        assert unwrapped is True

    def test_response_unwrap_version(self):
        """Test Response unwrap method with version."""
        response = Response.model_validate({"Version": "0.1.0"})
        unwrapped = response.unwrap()
        assert unwrapped == "0.1.0"

    def test_response_unwrap_empty(self):
        """Test Response unwrap with no fields raises error."""
        response = Response()
        with pytest.raises(ReplyError, match="does not contain any known fields"):
            response.unwrap()


class TestReply:
    """Tests for Reply model."""

    def test_reply_ok(self):
        """Test Reply with ok field."""
        reply = Reply.model_validate({"Ok": {"Handled": True}})
        assert reply.ok is not None
        assert reply.err is None

    def test_reply_error(self):
        """Test Reply with error."""
        reply = Reply.model_validate({"Err": "Socket error"})
        assert reply.err == "Socket error"
        assert reply.ok is None

    def test_reply_unwrap_ok(self):
        """Test Reply unwrap with success."""
        reply = Reply.model_validate({"Ok": {"Version": "0.1.0"}})
        unwrapped = reply.unwrap()
        assert unwrapped is not None
        assert unwrapped.version == "0.1.0"

    def test_reply_unwrap_error(self):
        """Test Reply unwrap with error raises ReplyError."""
        reply = Reply.model_validate({"Err": "Command failed"})
        with pytest.raises(ReplyError, match="Niri replied with error"):
            reply.unwrap()

    def test_reply_json_parsing(self):
        """Test Reply model_validate_json parsing."""
        import json

        reply_json = json.dumps({"Ok": {"Handled": True}})
        reply = Reply.model_validate_json(reply_json)
        assert reply.ok is not None
        assert reply.ok.handled is True
