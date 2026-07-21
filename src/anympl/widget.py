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
