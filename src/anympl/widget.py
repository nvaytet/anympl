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

    def set_scene(self, scene, figure_height=None):
        self.send(
            {
                "type": "scene",
                "scene": scene,
                "figure_height": figure_height
                if figure_height is not None
                else self.height,
            }
        )
