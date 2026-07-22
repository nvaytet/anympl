# from matplotlib.backend_bases import (
#     FigureCanvasBase,
#     FigureManagerBase,
#     RendererBase,
# )


# from .widget import PlotWidget


# class RendererAnyWidget(RendererBase):
#     def __init__(self):
#         super().__init__()
#         self.commands = []

#     def draw_path(
#         self,
#         gc,
#         path,
#         transform,
#         rgbFace=None,
#     ):
#         vertices = transform.transform(path.vertices)

#         self.commands.append(
#             {
#                 "type": "path",
#                 "vertices": vertices,
#                 "face": rgbFace,
#                 "linewidth": gc.get_linewidth(),
#                 "color": gc.get_rgb(),
#             }
#         )

#         if len(path.vertices) > 50:
#             print("PATH", len(path.vertices))

#     # def draw_text(
#     #     self,
#     #     gc,
#     #     x,
#     #     y,
#     #     s,
#     #     prop,
#     #     angle,
#     #     ismath=False,
#     #     mtext=None,
#     # ):
#     #     print("TEXT:", s, x, y)

#     def draw_text(
#         self,
#         gc,
#         x,
#         y,
#         s,
#         prop,
#         angle,
#         ismath=False,
#         mtext=None,
#     ):
#         print("TEXT", repr(s))
#         # print(
#         #     repr(s),
#         #     prop.get_name(),
#         #     prop.get_size_in_points(),
#         #     angle,
#         # )


# class FigureCanvasAnyWidget(FigureCanvasBase):
#     def __init__(self, figure):
#         super().__init__(figure)

#         self.widget = PlotWidget()

#         self.renderer = RendererAnyWidget()

#     def draw(self):
#         self.renderer.commands.clear()

#         self.figure.draw(self.renderer)

#         commands = []

#         for cmd in self.renderer.commands:
#             commands.append(
#                 {
#                     "type": "path",
#                     "vertices": cmd["vertices"].tolist(),
#                     "linewidth": cmd["linewidth"],
#                     "color": cmd["color"],
#                 }
#             )

#         self.widget.send(
#             {
#                 "type": "draw",
#                 "commands": commands,
#             }
#         )

#     def _repr_mimebundle_(self, **kwargs):
#         return self.widget._repr_mimebundle_(**kwargs)


# class FigureManagerAnyWidget(FigureManagerBase):
#     pass


# FigureCanvas = FigureCanvasAnyWidget
# FigureManager = FigureManagerAnyWidget


from matplotlib.backend_bases import (
    FigureCanvasBase,
    FigureManagerBase,
    RendererBase,
)

from .widget import PlotWidget


class RendererAnyWidget(RendererBase):
    def __init__(self, width, height, dpi):
        super().__init__()
        self.width = width
        self.height = height
        self.dpi = dpi
        self.scene = []

    def clear(self):
        self.scene.clear()

    def draw_path(
        self,
        gc,
        path,
        transform,
        rgbFace=None,
    ):
        vertices = transform.transform(path.vertices)

        self.scene.append(
            {
                "type": "path",
                "vertices": vertices.tolist(),
                "linewidth": gc.get_linewidth(),
                "color": gc.get_rgb(),
            }
        )

    def draw_text(
        self,
        gc,
        x,
        y,
        s,
        prop,
        angle,
        ismath=False,
        mtext=None,
    ):
        self.scene.append(
            {
                "type": "text",
                "text": s,
                "x": x,
                "y": y,
                "angle": angle,
                "size": prop.get_size_in_points(),
                "family": prop.get_name(),
                "color": gc.get_rgb(),
            }
        )

    def get_text_width_height_descent(self, s, prop, ismath):
        """
        Get the width, height, and descent of text.
        This is required for matplotlib to call draw_text.
        """
        # Return approximate values - for a proper implementation,
        # you'd measure the actual text
        size = prop.get_size_in_points()
        width = len(s) * size * 0.6  # rough approximation
        height = size
        descent = size * 0.2
        return width, height, descent

    def draw_image(self, gc, x, y, im):
        """
        Draw an image (for imshow, pcolormesh, etc.)
        im is an RGBA image with shape (height, width, 4)
        (x, y) is the position in display coordinates
        """
        # Convert the image array to a list for JSON serialization
        h, w = im.shape[:2]

        # Flatten RGBA data to 1D list
        image_data = im.flatten().tolist()

        self.scene.append(
            {
                "type": "image",
                "x": x,
                "y": y,
                "width": w,
                "height": h,
                "data": image_data,
            }
        )

    def draw_path_collection(
        self,
        gc,
        master_transform,
        paths,
        all_transforms,
        offsets,
        offset_trans,
        facecolors,
        edgecolors,
        linewidths,
        linestyles,
        antialiaseds,
        urls,
        offset_position,
    ):
        """
        Draw a collection of paths (used by scatter plots)
        This is more efficient than drawing each marker individually
        """
        # Transform the offsets (scatter point positions) to display coordinates
        if len(offsets):
            offsets = offset_trans.transform(offsets)

        # For simplicity, we'll assume all markers are the same
        # Get the first path and its transform if available
        if len(paths) > 0:
            path = paths[0]
            # Get marker size from the transform matrix
            if len(all_transforms) > 0:
                marker_size = all_transforms[0].get_matrix()[0, 0]
            else:
                marker_size = 5.0  # Default size
        else:
            return  # No paths to draw

        # Get colors - they can be single values or arrays
        if len(facecolors) == 1:
            facecolor = facecolors[0]
        else:
            facecolor = facecolors[0] if len(facecolors) > 0 else (0, 0, 0, 1)

        if len(edgecolors) == 1:
            edgecolor = edgecolors[0]
        else:
            edgecolor = edgecolors[0] if len(edgecolors) > 0 else (0, 0, 0, 1)

        linewidth = linewidths[0] if len(linewidths) > 0 else 1.0

        self.scene.append(
            {
                "type": "markers",
                "vertices": offsets.tolist(),
                "marker_size": marker_size,
                "facecolor": facecolor,
                "edgecolor": edgecolor,
                "linewidth": linewidth,
            }
        )


class FigureCanvasAnyWidget(FigureCanvasBase):
    def __init__(self, figure):
        super().__init__(figure)

        self.widget = PlotWidget()
        self.widget.canvas = self  # Link widget back to canvas

    def get_renderer(self, cleared=False):
        w = int(self.figure.bbox.width)
        h = int(self.figure.bbox.height)
        dpi = self.figure.dpi

        if not hasattr(self, "renderer") or self.renderer is None:
            self.renderer = RendererAnyWidget(w, h, dpi)
        else:
            self.renderer.width = w
            self.renderer.height = h
            self.renderer.dpi = dpi

        if cleared:
            self.renderer.clear()

        return self.renderer

    def draw(self):
        renderer = self.get_renderer(cleared=True)

        self.figure.draw(renderer)

        self.widget.width = int(self.figure.bbox.width)
        self.widget.height = int(self.figure.bbox.height)

        # Collect axes bounding boxes for clipping
        axes_bboxes = []
        for ax in self.figure.axes:
            bbox = ax.bbox
            axes_bboxes.append(
                {
                    "x0": bbox.x0,
                    "y0": bbox.y0,
                    "x1": bbox.x1,
                    "y1": bbox.y1,
                }
            )

        # Send the scene with the figure height for coordinate conversion
        self.widget.set_scene(renderer.scene, renderer.height, axes_bboxes)

    def _repr_mimebundle_(self, **kwargs):
        return self.widget._repr_mimebundle_(**kwargs)

    def enable_zoom(self, enable=True):
        """Enable or disable zoom functionality"""
        self.widget.zoom_enabled = enable

    def _handle_zoom(self, x0, x1, y0, y1):
        """Handle zoom event from JavaScript"""
        # Convert display coordinates to data coordinates
        # Find the axes that contain the zoom region
        for ax in self.figure.axes:
            # Get axes bbox in display coordinates
            bbox = ax.bbox

            # Check if zoom region overlaps with this axes
            if x0 >= bbox.x0 and x1 <= bbox.x1 and y0 >= bbox.y0 and y1 <= bbox.y1:
                # Transform display coords to data coords
                try:
                    p0 = ax.transData.inverted().transform([[x0, y0]])[0]
                    p1 = ax.transData.inverted().transform([[x1, y1]])[0]

                    # Set new limits
                    ax.set_xlim(p0[0], p1[0])
                    ax.set_ylim(p0[1], p1[1])

                    # Redraw
                    self.draw()
                    break
                except Exception as e:
                    print(f"Zoom error: {e}")


class FigureManagerAnyWidget(FigureManagerBase):
    pass


FigureCanvas = FigureCanvasAnyWidget
FigureManager = FigureManagerAnyWidget
