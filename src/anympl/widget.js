export function render({ model, el }) {

    // Create toolbar
    const toolbar = document.createElement("div");
    toolbar.style.cssText = `
        display: flex;
        gap: 5px;
        padding: 5px;
        background-color: #f0f0f0;
        border-bottom: 1px solid #ccc;
        font-family: sans-serif;
    `;

    // Create toolbar buttons
    const buttons = [
        { id: "home", label: "Home", icon: "🏠" },
        { id: "pan", label: "Pan", icon: "✋" },
        { id: "zoom", label: "Zoom", icon: "🔍" },
        { id: "prev", label: "Prev", icon: "◀", disabled: true },
        { id: "next", label: "Next", icon: "▶", disabled: true },
        { id: "save", label: "Save", icon: "💾", disabled: true }
    ];

    let currentMode = model.get("toolbar_mode") || "";

    buttons.forEach(btn => {
        const button = document.createElement("button");
        button.textContent = btn.icon + " " + btn.label;
        button.disabled = btn.disabled || false;
        button.style.cssText = `
            padding: 5px 10px;
            cursor: ${btn.disabled ? "not-allowed" : "pointer"};
            background-color: white;
            border: 1px solid #ccc;
            border-radius: 3px;
            font-size: 12px;
        `;

        if (!btn.disabled) {
            button.addEventListener("click", () => {
                model.send({ type: "toolbar_action", action: btn.id });
            });

            button.addEventListener("mouseenter", () => {
                if (!button.disabled) {
                    button.style.backgroundColor = "#e0e0e0";
                }
            });

            button.addEventListener("mouseleave", () => {
                const isActive = (btn.id === "pan" && currentMode === "pan") ||
                    (btn.id === "zoom" && currentMode === "zoom");
                button.style.backgroundColor = isActive ? "#d0d0ff" : "white";
            });
        }

        toolbar.appendChild(button);

        // Store button reference for mode updates
        button.dataset.action = btn.id;
    });

    el.appendChild(toolbar);

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

    // Pan state
    let panEnabled = model.get("pan_enabled") || false;
    let isPanning = false;
    let panStart = null;

    // Event enabled states
    let buttonPressEnabled = model.get("button_press_enabled") || false;
    let buttonReleaseEnabled = model.get("button_release_enabled") || false;
    let motionNotifyEnabled = model.get("motion_notify_enabled") || false;

    // Throttle mouse motion events to reduce lag
    let lastMotionEventTime = 0;
    const motionEventThrottle = 20; // milliseconds

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
            } else if (cmd.type === "markers") {
                // Draw scatter plot markers with varying sizes/colors
                const vertices = cmd.vertices;

                // Handle both single and per-marker properties
                const sizes = cmd.marker_sizes || [cmd.marker_size || 5.0];
                const faceColors = cmd.facecolors || [cmd.facecolor];
                const edgeColors = cmd.edgecolors || [cmd.edgecolor];
                const linewidths = cmd.linewidths || [cmd.linewidth || 1.0];

                for (let i = 0; i < vertices.length; i++) {
                    const x = vertices[i][0];
                    const y = figureHeight - vertices[i][1];

                    // Get properties for this marker (use modulo for cycling if needed)
                    const size = sizes[i % sizes.length];
                    const faceColor = faceColors[i % faceColors.length];
                    const edgeColor = edgeColors[i % edgeColors.length];
                    const linewidth = linewidths[i % linewidths.length];

                    ctx.beginPath();
                    ctx.arc(x, y, size / 2, 0, 2 * Math.PI);

                    // Fill
                    if (faceColor && faceColor[3] > 0) {  // Check alpha
                        ctx.fillStyle = `rgba(${faceColor[0] * 255}, ${faceColor[1] * 255}, ${faceColor[2] * 255}, ${faceColor[3]})`;
                        ctx.fill();
                    }

                    // Stroke
                    if (linewidth > 0 && edgeColor && edgeColor[3] > 0) {
                        ctx.strokeStyle = `rgba(${edgeColor[0] * 255}, ${edgeColor[1] * 255}, ${edgeColor[2] * 255}, ${edgeColor[3]})`;
                        ctx.lineWidth = linewidth;
                        ctx.stroke();
                    }
                }
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
        if (zoomEnabled) {
            canvas.style.cursor = "crosshair";
        } else if (panEnabled) {
            canvas.style.cursor = "grab";
        } else {
            canvas.style.cursor = "default";
        }
    });

    // Watch for pan_enabled changes
    model.on("change:pan_enabled", () => {
        panEnabled = model.get("pan_enabled");
        if (panEnabled) {
            canvas.style.cursor = "grab";
        } else if (zoomEnabled) {
            canvas.style.cursor = "crosshair";
        } else {
            canvas.style.cursor = "default";
        }
    });

    // Watch for toolbar mode changes
    model.on("change:toolbar_mode", () => {
        currentMode = model.get("toolbar_mode");
        // Update button styles based on mode
        toolbar.querySelectorAll("button").forEach(btn => {
            const action = btn.dataset.action;
            if (action === "pan" || action === "zoom") {
                const isActive = action === currentMode;
                btn.style.backgroundColor = isActive ? "#d0d0ff" : "white";
                btn.style.fontWeight = isActive ? "bold" : "normal";
            }
        });
    });

    // Watch for event enabled changes
    model.on("change:button_press_enabled", () => {
        buttonPressEnabled = model.get("button_press_enabled");
    });

    model.on("change:button_release_enabled", () => {
        buttonReleaseEnabled = model.get("button_release_enabled");
    });

    model.on("change:motion_notify_enabled", () => {
        motionNotifyEnabled = model.get("motion_notify_enabled");
    });

    // Mouse event handlers
    canvas.addEventListener("mousedown", (e) => {
        const rect = canvas.getBoundingClientRect();
        const canvasX = e.clientX - rect.left;
        const canvasY = e.clientY - rect.top;

        if (zoomEnabled) {
            zoomStart = { x: canvasX, y: canvasY };
            isZooming = true;
        } else if (panEnabled) {
            panStart = { x: canvasX, y: canvasY };
            isPanning = true;
            canvas.style.cursor = "grabbing";
        } else if (buttonPressEnabled) {
            // Send button_press_event to Python
            const mplX = canvasX;
            const mplY = currentFigureHeight - canvasY;

            model.send({
                type: "button_press_event",
                x: mplX,
                y: mplY,
                button: e.button + 1  // JS uses 0-indexed, matplotlib uses 1-indexed
            });
        }
    });

    canvas.addEventListener("mousemove", (e) => {
        const rect = canvas.getBoundingClientRect();
        const canvasX = e.clientX - rect.left;
        const canvasY = e.clientY - rect.top;

        if (isZooming) {
            zoomCurrent = { x: canvasX, y: canvasY };

            // Redraw with zoom box
            if (currentScene && currentFigureHeight) {
                drawScene(currentScene, currentFigureHeight, currentAxesBboxes);
            }
        } else if (isPanning && panStart) {
            // Send pan update to Python
            const mplX0 = panStart.x;
            const mplY0 = currentFigureHeight - panStart.y;
            const mplX1 = canvasX;
            const mplY1 = currentFigureHeight - canvasY;

            model.send({
                type: "pan",
                x0: mplX0,
                y0: mplY0,
                x1: mplX1,
                y1: mplY1
            });

            // Update pan start for next move
            panStart = { x: canvasX, y: canvasY };
        } else if (motionNotifyEnabled) {
            // Throttle motion events to reduce lag
            const now = Date.now();
            if (now - lastMotionEventTime < motionEventThrottle) {
                return;
            }
            lastMotionEventTime = now;

            // Send motion_notify_event to Python
            // Convert canvas coords to matplotlib display coords
            const mplX = canvasX;
            const mplY = currentFigureHeight - canvasY;

            model.send({
                type: "motion_notify_event",
                x: mplX,
                y: mplY,
                button: 0
            });
        }
    });

    canvas.addEventListener("mouseup", (e) => {
        const rect = canvas.getBoundingClientRect();
        const canvasX = e.clientX - rect.left;
        const canvasY = e.clientY - rect.top;

        if (isZooming) {
            // Send zoom coordinates to Python (in matplotlib coordinates)
            // Convert from canvas coords to matplotlib coords
            const x0_mpl = Math.min(zoomStart.x, canvasX);
            const x1_mpl = Math.max(zoomStart.x, canvasX);
            const y0_canvas = Math.max(zoomStart.y, canvasY);
            const y1_canvas = Math.min(zoomStart.y, canvasY);
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
        } else if (isPanning) {
            // End panning
            isPanning = false;
            panStart = null;
            canvas.style.cursor = "grab";
        } else if (buttonReleaseEnabled) {
            // Send button_release_event to Python
            const mplX = canvasX;
            const mplY = currentFigureHeight - canvasY;

            model.send({
                type: "button_release_event",
                x: mplX,
                y: mplY,
                button: e.button + 1
            });
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
        if (isPanning) {
            isPanning = false;
            panStart = null;
            if (panEnabled) {
                canvas.style.cursor = "grab";
            }
        }
    });
}