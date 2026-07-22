# import anywidget
# from pathlib import Path
# import traitlets


# class PlotWidget(anywidget.AnyWidget):
#     _esm = Path(__file__).parent / "widget.js"

#     width = traitlets.Int(800).tag(sync=True)
#     height = traitlets.Int(600).tag(sync=True)

#     def send_scene(self, scene):
#         self.send(scene)

import anywidget
from pathlib import Path
import traitlets


class PlotWidget(anywidget.AnyWidget):
    _esm = Path(__file__).parent / "widget.js"

    width = traitlets.Int(800).tag(sync=True)
    height = traitlets.Int(600).tag(sync=True)
    zoom_enabled = traitlets.Bool(False).tag(sync=True)
    pan_enabled = traitlets.Bool(False).tag(sync=True)
    button_press_enabled = traitlets.Bool(False).tag(sync=True)
    button_release_enabled = traitlets.Bool(False).tag(sync=True)
    motion_notify_enabled = traitlets.Bool(False).tag(sync=True)
    toolbar_mode = traitlets.Unicode("").tag(sync=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.canvas = None  # Will be set by FigureCanvas
        self.on_msg(self._handle_msg)

    def _handle_msg(self, msg):
        """Handle messages from JavaScript"""
        # Extract the actual content from the nested message structure
        try:
            content = msg.get("content", {}).get("data", {}).get("content", {})

            if content.get("type") == "zoom" and self.canvas is not None:
                self.canvas._handle_zoom(
                    content["x0"], content["x1"], content["y0"], content["y1"]
                )
            elif content.get("type") == "pan" and self.canvas is not None:
                self.canvas._handle_pan(
                    content["x0"], content["y0"], content["x1"], content["y1"]
                )
            elif (
                content.get("type")
                in [
                    "motion_notify_event",
                    "button_press_event",
                    "button_release_event",
                ]
                and self.canvas is not None
            ):
                self.canvas._handle_mouse_event(content)
            elif content.get("type") == "toolbar_action" and self.canvas is not None:
                action = content.get("action")
                if action == "home" and hasattr(self.canvas.toolbar, "home"):
                    self.canvas.toolbar.home()
                elif action == "pan" and hasattr(self.canvas.toolbar, "pan"):
                    self.canvas.toolbar.pan()
                elif action == "zoom" and hasattr(self.canvas.toolbar, "zoom"):
                    self.canvas.toolbar.zoom()
        except Exception as e:
            print(f"Error handling message: {e}")

    def set_scene(self, scene, figure_height=None, axes_bboxes=None):
        self.send(
            {
                "type": "scene",
                "scene": scene,
                "figure_height": figure_height
                if figure_height is not None
                else self.height,
                "axes_bboxes": axes_bboxes or [],
            }
        )
