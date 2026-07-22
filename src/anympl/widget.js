export function render({ model, el }) {

    const canvas = document.createElement("canvas");

    canvas.width = model.get("width");
    canvas.height = model.get("height");

    el.appendChild(canvas);

    const ctx = canvas.getContext("2d");

    // Store the current scene for redrawing
    let currentScene = null;
    let currentFigureHeight = null;
    let currentAxesBboxes = null;

    // Zoom state
    let zoomEnabled = model.get("zoom_enabled") || false;
    let isZooming = false;
    let zoomStart = null;
    let zoomCurrent = null;

    // Function to draw the scene
    function drawScene(scene, figureHeight, axesBboxes) {
        // Clear the canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Draw paths with clipping
        if (axesBboxes && axesBboxes.length > 0) {
            ctx.save();
            ctx.beginPath();

            // Add all axes as clipping regions
            for (const bbox of axesBboxes) {
                // Convert matplotlib coords to canvas coords
                const x = bbox.x0;
                const y = figureHeight - bbox.y1;
                const w = bbox.x1 - bbox.x0;
                const h = bbox.y1 - bbox.y0;

                ctx.rect(x, y, w, h);
            }

            ctx.clip();
        }

        // Draw paths (clipped to axes)
        for (const cmd of scene) {
            if (cmd.type == "path") {

                const v = cmd.vertices;

                ctx.beginPath();

                // Convert from matplotlib coords (bottom-left origin) to canvas (top-left origin)
                const y0 = figureHeight - v[0][1];
                ctx.moveTo(v[0][0], y0);

                for (let i = 1; i < v.length; i++) {
                    const y = figureHeight - v[i][1];
                    ctx.lineTo(v[i][0], y);
                }

                ctx.lineWidth = cmd.linewidth;

                const c = cmd.color;
                ctx.strokeStyle = `rgb(${c[0] * 255}, ${c[1] * 255}, ${c[2] * 255})`;

                ctx.stroke();
            } else if (cmd.type === "image") {
                // Draw images (imshow, pcolormesh, etc.)
                const imgData = ctx.createImageData(cmd.width, cmd.height);

                // Copy RGBA data - check if it's already 0-255 or needs conversion
                const maxVal = Math.max(...cmd.data.slice(0, 1000)); // Sample first values
                const scaleFactor = maxVal <= 1.0 ? 255 : 1;

                for (let i = 0; i < cmd.data.length; i++) {
                    imgData.data[i] = cmd.data[i] * scaleFactor;
                }

                // Convert matplotlib coords (bottom-left) to canvas (top-left)
                const canvasX = cmd.x;
                const canvasY = figureHeight - cmd.y - cmd.height;

                ctx.putImageData(imgData, canvasX, canvasY);
            }
        }

        // Restore context (remove clipping)
        if (axesBboxes && axesBboxes.length > 0) {
            ctx.restore();
        }

        // Draw text without clipping (so labels can appear outside axes)
        for (const cmd of scene) {
            if (cmd.type === "text") {

                ctx.save();

                // Text coordinates from matplotlib have y increasing downward from bottom of figure
                // (opposite to path coordinates which have y increasing upward)
                const canvasX = cmd.x;
                const canvasY = figureHeight + cmd.y;  // ADD instead of subtract

                ctx.translate(canvasX, canvasY);

                if (cmd.angle) {
                    ctx.rotate(-cmd.angle * Math.PI / 180);
                }

                ctx.font = `${cmd.size}px "${cmd.family}", sans-serif`;

                const c = cmd.color;
                ctx.fillStyle = `rgb(${c[0] * 255}, ${c[1] * 255}, ${c[2] * 255})`;

                ctx.textBaseline = "alphabetic";
                ctx.textAlign = "left";

                ctx.fillText(cmd.text, 0, 0);

                ctx.restore();

            }
        }

        // Draw zoom box if zooming
        if (isZooming && zoomStart && zoomCurrent) {
            ctx.save();
            ctx.strokeStyle = "rgba(0, 0, 0, 0.8)";
            ctx.fillStyle = "rgba(128, 128, 128, 0.2)";
            ctx.lineWidth = 1;

            const x = Math.min(zoomStart.x, zoomCurrent.x);
            const y = Math.min(zoomStart.y, zoomCurrent.y);
            const w = Math.abs(zoomCurrent.x - zoomStart.x);
            const h = Math.abs(zoomCurrent.y - zoomStart.y);

            ctx.fillRect(x, y, w, h);
            ctx.strokeRect(x, y, w, h);
            ctx.restore();
        }
    }

    // Handle scene updates
    model.on("msg:custom", (msg) => {
        if (msg.type === "scene") {
            currentScene = msg.scene;
            currentFigureHeight = msg.figure_height;
            currentAxesBboxes = msg.axes_bboxes;
            drawScene(currentScene, currentFigureHeight, currentAxesBboxes);
        }
    });

    // Watch for zoom_enabled changes
    model.on("change:zoom_enabled", () => {
        zoomEnabled = model.get("zoom_enabled");
    });

    // Mouse event handlers for zoom
    canvas.addEventListener("mousedown", (e) => {
        if (!zoomEnabled) return;

        const rect = canvas.getBoundingClientRect();
        zoomStart = {
            x: e.clientX - rect.left,
            y: e.clientY - rect.top
        };
        isZooming = true;
    });

    canvas.addEventListener("mousemove", (e) => {
        if (!isZooming) return;

        const rect = canvas.getBoundingClientRect();
        zoomCurrent = {
            x: e.clientX - rect.left,
            y: e.clientY - rect.top
        };

        // Redraw with zoom box
        if (currentScene && currentFigureHeight) {
            drawScene(currentScene, currentFigureHeight, currentAxesBboxes);
        }
    });

    canvas.addEventListener("mouseup", (e) => {
        if (!isZooming) return;

        const rect = canvas.getBoundingClientRect();
        const endX = e.clientX - rect.left;
        const endY = e.clientY - rect.top;

        // Send zoom coordinates to Python (in matplotlib coordinates)
        // Convert from canvas coords to matplotlib coords
        const x0_mpl = Math.min(zoomStart.x, endX);
        const x1_mpl = Math.max(zoomStart.x, endX);
        const y0_canvas = Math.max(zoomStart.y, endY);
        const y1_canvas = Math.min(zoomStart.y, endY);
        const y0_mpl = currentFigureHeight - y0_canvas;
        const y1_mpl = currentFigureHeight - y1_canvas;

        model.send({
            type: "zoom",
            x0: x0_mpl,
            x1: x1_mpl,
            y0: y0_mpl,
            y1: y1_mpl
        });

        // Reset zoom state
        isZooming = false;
        zoomStart = null;
        zoomCurrent = null;

        // Redraw without zoom box
        if (currentScene && currentFigureHeight) {
            drawScene(currentScene, currentFigureHeight, currentAxesBboxes);
        }
    });

    canvas.addEventListener("mouseleave", () => {
        if (isZooming) {
            isZooming = false;
            zoomStart = null;
            zoomCurrent = null;
            if (currentScene && currentFigureHeight) {
                drawScene(currentScene, currentFigureHeight, currentAxesBboxes);
            }
        }
    });
}