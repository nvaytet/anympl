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

import numpy as np

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
        This handles varying sizes and colors per marker
        """

        # Transform the offsets (scatter point positions) to display coordinates
        if len(offsets):
            offsets = offset_trans.transform(offsets)

        if len(paths) == 0 or len(offsets) == 0:
            return  # No paths to draw

        # Extract marker sizes from transforms
        marker_sizes = []
        if len(all_transforms) > 0:
            # all_transforms can be either transform objects or a numpy array of matrices
            if hasattr(all_transforms[0], 'get_matrix'):
                # It's a list of transform objects
                marker_sizes = [t.get_matrix()[0, 0] for t in all_transforms]
            else:
                # It's a numpy array - each row is a 3x3 matrix flattened or similar
                # The transform contains the scale in the matrix
                if isinstance(all_transforms, np.ndarray):
                    # If it's a 3D array of shape (n, 3, 3), extract [0,0] from each
                    if all_transforms.ndim == 3:
                        marker_sizes = all_transforms[:, 0, 0].tolist()
                    else:
                        # Fallback: use default size
                        marker_sizes = [5.0] * len(offsets)
                else:
                    marker_sizes = [5.0] * len(offsets)
        else:
            marker_sizes = [5.0] * len(offsets)

        # Ensure we have the right number of sizes
        if len(marker_sizes) == 1:
            marker_sizes = marker_sizes * len(offsets)
        elif len(marker_sizes) != len(offsets):
            marker_sizes = (
                [marker_sizes[0]] * len(offsets)
                if len(marker_sizes) > 0
                else [5.0] * len(offsets)
            )

        # Handle colors - can be single or per-marker
        if len(facecolors) == len(offsets):
            facecolors_list = (
                facecolors.tolist()
                if hasattr(facecolors, 'tolist')
                else list(facecolors)
            )
        elif len(facecolors) == 1:
            facecolors_list = [
                facecolors[0].tolist()
                if hasattr(facecolors[0], 'tolist')
                else facecolors[0]
            ] * len(offsets)
        else:
            facecolors_list = [(0, 0, 0, 1)] * len(offsets)

        if len(edgecolors) == len(offsets):
            edgecolors_list = (
                edgecolors.tolist()
                if hasattr(edgecolors, 'tolist')
                else list(edgecolors)
            )
        elif len(edgecolors) == 1:
            edgecolors_list = [
                edgecolors[0].tolist()
                if hasattr(edgecolors[0], 'tolist')
                else edgecolors[0]
            ] * len(offsets)
        else:
            edgecolors_list = [(0, 0, 0, 1)] * len(offsets)

        # Handle linewidths
        if len(linewidths) == len(offsets):
            linewidths_list = (
                linewidths.tolist()
                if hasattr(linewidths, 'tolist')
                else list(linewidths)
            )
        elif len(linewidths) == 1:
            linewidths_list = [linewidths[0]] * len(offsets)
        else:
            linewidths_list = [1.0] * len(offsets)

        self.scene.append(
            {
                "type": "markers",
                "vertices": offsets.tolist(),
                "marker_sizes": marker_sizes,  # Note: plural for varying sizes
                "facecolors": facecolors_list,  # Note: plural for varying colors
                "edgecolors": edgecolors_list,  # Note: plural for varying colors
                "linewidths": linewidths_list,  # Note: plural for varying widths
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

    def mpl_connect(self, event_name, callback):
        """Connect a callback to a matplotlib event"""
        if not hasattr(self, '_event_callbacks'):
            self._event_callbacks = {}

        if event_name not in self._event_callbacks:
            self._event_callbacks[event_name] = []

        # Simple connection ID (just use length as ID)
        cid = len(self._event_callbacks.get(event_name, []))
        self._event_callbacks[event_name].append((cid, callback))

        # Enable the corresponding event type in the widget
        if event_name == "button_press_event":
            self.widget.button_press_enabled = True
        elif event_name == "button_release_event":
            self.widget.button_release_enabled = True
        elif event_name == "motion_notify_event":
            self.widget.motion_notify_enabled = True

        return cid

    def mpl_disconnect(self, cid):
        """Disconnect a callback (not implemented yet)"""
        pass

    def _handle_mouse_event(self, event_data):
        """Handle mouse events from JavaScript"""
        from matplotlib.backend_bases import MouseEvent

        event_type = event_data["type"]
        x = event_data["x"]  # Display coordinates
        y = event_data["y"]  # Display coordinates
        button = event_data.get("button", 1)

        # Find which axes contains this point
        inaxes = None
        for ax in self.figure.axes:
            bbox = ax.bbox
            if bbox.x0 <= x <= bbox.x1 and bbox.y0 <= y <= bbox.y1:
                inaxes = ax
                break

        # Convert display coordinates to data coordinates
        xdata = ydata = None
        if inaxes is not None:
            try:
                data_coords = inaxes.transData.inverted().transform([[x, y]])[0]
                xdata, ydata = data_coords
            except:
                pass

        # Create the matplotlib event object
        event = MouseEvent(
            event_type,
            self,
            x,
            y,
            button=button,
            key=None,
            dblclick=False,
            guiEvent=None,
        )
        event.inaxes = inaxes
        event.xdata = xdata
        event.ydata = ydata

        # Dispatch to registered callbacks
        if hasattr(self, '_event_callbacks') and event_type in self._event_callbacks:
            for cid, callback in self._event_callbacks[event_type]:
                callback(event)

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
