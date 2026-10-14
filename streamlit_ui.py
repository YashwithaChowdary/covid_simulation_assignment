"""Simple Streamlit front end for the COVID-19 simulation assignment."""

from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

import assignment2


BASE_DIR = Path(__file__).resolve().parent
COUNTRIES_CSV = BASE_DIR / "a2-countries.csv"
PLOT_PATH = BASE_DIR / "a2-covid-simulation.png"


@st.cache_data
def load_countries(csv_path: str) -> list[str]:
    """Read country names for the multi-select control."""
    data = pd.read_csv(csv_path)
    if "country" not in data.columns:
        raise ValueError("The country CSV must contain a 'country' column.")
    return data["country"].dropna().astype(str).tolist()


def main() -> None:
    """Render the inputs, run the simulation, and show its output chart."""
    st.set_page_config(page_title="COVID-19 Simulation", layout="wide")
    st.title("COVID-19 Spread Simulation")
    st.write(
        "Choose a sample ratio, a date range, and one or more countries. "
        "The run produces individual and summary CSV files plus a chart."
    )

    try:
        available_countries = load_countries(str(COUNTRIES_CSV))
    except (OSError, ValueError, pd.errors.ParserError) as exc:
        st.error(f"Could not load country data: {exc}")
        return

    SAMPLE_RATIO = st.number_input(
        "Sample Ratio", min_value=1.0, value=1_000_000.0,
        step=100_000.0, format="%.0f",
        help="One simulated person represents approximately this many people.",
    )
    START_DATE = st.date_input("Start Date", value=date(2021, 4, 1))
    END_DATE = st.date_input("End Date", value=date(2022, 4, 30))
    default_countries = [
        country for country in ["Afghanistan", "Sweden", "Japan"]
        if country in available_countries
    ]
    SELECTED_COUNTRIES = st.multiselect(
        "Countries", options=available_countries, default=default_countries
    )

    if st.button("Run", type="primary"):
        if not SELECTED_COUNTRIES:
            st.error("Please select at least one country.")
        elif END_DATE < START_DATE:
            st.error("End Date must be on or after Start Date.")
        else:
            with st.spinner("Running the simulation..."):
                try:
                    assignment2.run(
                        countries_csv_name=str(COUNTRIES_CSV),
                        countries=SELECTED_COUNTRIES,
                        sample_ratio=SAMPLE_RATIO,
                        start_date=START_DATE.isoformat(),
                        end_date=END_DATE.isoformat(),
                    )
                except (ValueError, OSError, KeyError) as exc:
                    st.error(f"Simulation failed: {exc}")
                    return
            st.success("Simulation completed.")
            st.write(f"Countries: {', '.join(SELECTED_COUNTRIES)}")
            st.write(
                f"Date range: {START_DATE.isoformat()} to {END_DATE.isoformat()}"
            )
            st.write("Generated files:")
            st.code(
                "a2-covid-simulated-timeseries.csv\n"
                "a2-covid-summary-timeseries.csv\n"
                "a2-covid-simulation.png"
            )
            if PLOT_PATH.exists():
                st.image(str(PLOT_PATH), caption="Simulated COVID-19 state counts")
            else:
                st.warning("The simulation finished, but the chart file was not found.")

    elif PLOT_PATH.exists():
        st.subheader("Most recently generated chart")
        st.image(str(PLOT_PATH))


if __name__ == "__main__":
    main()
