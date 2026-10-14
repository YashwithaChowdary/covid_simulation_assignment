"""Plot helper for the COVID-19 simulation output."""

from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

OUTPUT_NAME = "a2-covid-simulation.png"
BASE_DIR = Path(__file__).resolve().parent


def get_filepath(filename):
    """Return a path relative to this helper module unless already absolute."""
    path = Path(filename).expanduser()
    if path.is_absolute():
        return path
    return BASE_DIR / path


def save_plot(fig, filename):
    """Save a figure next to this helper module."""
    fig.savefig(get_filepath(filename), dpi=180, bbox_inches="tight")


def read_dataset(filename):
    """Read a CSV dataset from the project folder."""
    return pd.read_csv(get_filepath(filename), sep=",", header=0)


def create_plot(summary_csv, countries):
    """Create a stacked daily state chart for each selected country."""
    summary = read_dataset(summary_csv)
    required_columns = {"country", "date", "H", "I", "S", "M", "D"}
    missing = required_columns.difference(summary.columns)
    if missing:
        raise ValueError(
            "Summary CSV is missing required column(s): " + ", ".join(sorted(missing))
        )

    summary = summary.copy()
    summary["date"] = pd.to_datetime(summary["date"])
    selected_countries = list(countries)
    if not selected_countries:
        raise ValueError("At least one country is required for the plot.")

    figure, axes = plt.subplots(
        nrows=len(selected_countries),
        ncols=1,
        figsize=(16, max(6, 5 * len(selected_countries))),
        squeeze=False,
    )
    colors = ["green", "darkorange", "indianred", "lightseagreen", "slategray"]
    states = ["H", "I", "S", "M", "D"]
    legend_labels = [
        "Healthy", "Infected (without symptoms)",
        "Infected (with symptoms)", "Immune", "Deceased",
    ]

    for axis, country in zip(axes[:, 0], selected_countries):
        country_data = (
            summary.loc[summary["country"] == country]
            .sort_values("date")
            .reset_index(drop=True)
        )
        if country_data.empty:
            axis.text(
                0.5, 0.5, f"No sampled people for {country}",
                horizontalalignment="center", verticalalignment="center",
                transform=axis.transAxes,
            )
            axis.set_title(f"COVID Infection Status in {country}")
            axis.set_xlabel("Date")
            axis.set_ylabel("Population in Samples")
            continue

        country_data.plot(
            kind="bar", x="date", y=states, stacked=True, width=1.0,
            color=colors, ax=axis, legend=False,
        )
        axis.legend(legend_labels, loc="upper left")
        axis.set_title(f"COVID Infection Status in {country}")
        axis.set_xlabel("Date")
        axis.set_ylabel("Population in Samples")

        # Use the first plotted position of each month for readable date labels.
        month_periods = country_data["date"].dt.to_period("M")
        month_starts = ~month_periods.duplicated()
        positions = country_data.index[month_starts].tolist()
        labels = country_data.loc[month_starts, "date"].dt.strftime("%b %Y").tolist()
        axis.set_xticks(positions)
        axis.set_xticklabels(labels, rotation=30, ha="right")
        axis.grid(axis="y", alpha=0.2)

    figure.tight_layout()
    save_plot(figure, OUTPUT_NAME)
    plt.close(figure)
    print("Plotting done.")
