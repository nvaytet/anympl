# anympl

Example:

```Python
import matplotlib
import matplotlib.pyplot as plt

matplotlib.use(
    "module://anympl.backend_anywidget"
)


fig, ax = plt.subplots()

ax.plot([1,2,3], color="red")
ax.plot([3,2,1], color="blue")
ax.set_title("Hello")
fig.canvas

fig.canvas.draw()
```
