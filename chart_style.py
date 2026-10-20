"""One look for every chart Delay Lab draws (app sweep chart and README figures).

Series colours are the first slots of a colour-blind-checked categorical order,
always in this order; ink and grid colours keep the chrome quiet.
"""

SERIES = ["#2a78d6", "#eb6834"]  # slot 1 blue, slot 2 orange
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
FONT = ["Segoe UI", "Helvetica", "Arial", "DejaVu Sans"]


def new_figure(width=7.0, height=4.2):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": FONT, "font.size": 10})
    fig, ax = plt.subplots(figsize=(width, height), dpi=150)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(AXIS)
    ax.tick_params(colors=MUTED, labelcolor=INK_2, length=0, pad=6)
    ax.grid(color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    return fig, ax


def finish(fig, ax, out, title: str, subtitle: str = "") -> None:
    import matplotlib.pyplot as plt

    ax.set_title(title, loc="left", color=INK, fontsize=12, fontweight="bold",
                 pad=22 if subtitle else 10)
    if subtitle:
        ax.text(0, 1.02, subtitle, transform=ax.transAxes, color=INK_2, fontsize=9, va="bottom")
    fig.tight_layout()
    fig.savefig(out, facecolor=SURFACE, metadata={"Software": None})
    plt.close(fig)
