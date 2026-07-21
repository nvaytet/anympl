export function render({ model, el }) {

    const canvas = document.createElement("canvas");

    canvas.width = model.get("width");
    canvas.height = model.get("height");

    el.appendChild(canvas);

    const ctx = canvas.getContext("2d");

    model.on("msg:custom", (msg) => {

        console.log(msg);

        if (msg.type !== "scene")
            return;

        const figureHeight = msg.figure_height;

        // Clear the canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        for (const cmd of msg.scene) {

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

            } else if (cmd.type === "text") {

                console.log("TEXT DRAW", cmd);

                ctx.save();

                // Text coordinates from matplotlib have y increasing downward from bottom of figure
                // (opposite to path coordinates which have y increasing upward)
                const canvasX = cmd.x;
                const canvasY = figureHeight + cmd.y;  // ADD instead of subtract

                console.log("Figure height:", figureHeight);
                console.log("Text position - mpl coords:", cmd.x, cmd.y);
                console.log("Text position - canvas coords:", canvasX, canvasY);

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
    });
}