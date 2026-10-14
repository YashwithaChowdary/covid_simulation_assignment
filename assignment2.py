"""COVID-19 population simulation for Assignment 2.

Each sampled person starts in the healthy (H) state. State transitions are
selected according to the age-group parameters in ``sim_parameters.py`` and
occur after the configured number of simulated days in a state. The run
function writes an individual-level time series, a country-level summary, and
then asks ``helper.create_plot`` to generate the chart.
"""

from datetime import date, datetime, timedelta
from pathlib import Path
import math
import random
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple, Union

import pandas as pd

from helper import create_plot
from sim_parameters import HOLDING_TIMES, TRANSITION_PROBS


AGE_GROUPS = ("less_5", "5_to_14", "15_to_24", "25_to_64", "over_65")
STATES = ("H", "I", "S", "M", "D")
SUMMARY_STATES = ("D", "H", "I", "M", "S")
SIMULATED_OUTPUT = "a2-covid-simulated-timeseries.csv"
SUMMARY_OUTPUT = "a2-covid-summary-timeseries.csv"
PLOT_OUTPUT = "a2-covid-simulation.png"
BASE_DIR = Path(__file__).resolve().parent


DateLike = Union[str, date, datetime, pd.Timestamp]


def _as_date(value: DateLike, argument_name: str) -> date:
    """Convert a string/date/datetime value into a calendar date."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError(
            f"{argument_name} must use the YYYY-MM-DD date format."
        ) from exc


def _resolve_input_path(filename: Union[str, Path]) -> Path:
    """Resolve an input path from the current directory or this project folder."""
    path = Path(filename).expanduser()
    if path.is_absolute() and path.exists():
        return path
    if path.exists():
        return path.resolve()
    local_path = BASE_DIR / path.name
    if local_path.exists():
        return local_path
    raise FileNotFoundError(f"Could not find input file: {filename}")


def _read_country_data(countries_csv_name: Union[str, Path]) -> pd.DataFrame:
    """Read and validate the country population and age-distribution data."""
    csv_path = _resolve_input_path(countries_csv_name)
    country_data = pd.read_csv(csv_path)

    required_columns = {"country", "population", *AGE_GROUPS}
    missing_columns = required_columns.difference(country_data.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Country CSV is missing required column(s): {missing}")
    if country_data["country"].duplicated().any():
        raise ValueError("Country names in the input CSV must be unique.")

    return country_data


def _build_population_samples(
    country_data: pd.DataFrame,
    countries: Sequence[str],
    sample_ratio: float,
) -> List[Dict[str, Union[int, str]]]:
    """Create one record per sampled person according to each country's ages."""
    samples: List[Dict[str, Union[int, str]]] = []
    person_id = 0

    country_names = set(country_data["country"].astype(str))
    unknown_countries = [country for country in countries if country not in country_names]
    if unknown_countries:
        raise ValueError(
            "Country name(s) not found in the CSV: " + ", ".join(unknown_countries)
        )

    for country in countries:
        country_row = country_data.loc[country_data["country"] == country].iloc[0]
        population = float(country_row["population"])
        number_of_people = int(population // sample_ratio)

        for age_group in AGE_GROUPS:
            age_percentage = float(country_row[age_group])
            age_group_size = int(round(number_of_people * age_percentage / 100.0))
            for _ in range(age_group_size):
                samples.append(
                    {
                        "person_id": person_id,
                        "age_group_name": age_group,
                        "country": str(country),
                    }
                )
                person_id += 1

    return samples


def _validate_parameters() -> None:
    """Check that the supplied transition rows are usable probability lists."""
    for age_group in AGE_GROUPS:
        if age_group not in TRANSITION_PROBS or age_group not in HOLDING_TIMES:
            raise ValueError(f"Missing simulation parameters for age group {age_group!r}.")

        transition_by_state = TRANSITION_PROBS[age_group]
        holding_by_state = HOLDING_TIMES[age_group]
        for state in STATES:
            if state not in transition_by_state or state not in holding_by_state:
                raise ValueError(
                    f"Missing state {state!r} in parameters for age group {age_group!r}."
                )

            destinations = transition_by_state[state]
            if not destinations:
                raise ValueError(
                    f"No transition probabilities configured for {age_group!r}/{state!r}."
                )
            probabilities = list(destinations.values())
            if any(probability < 0 or probability > 1 for probability in probabilities):
                raise ValueError(
                    f"Invalid probability in parameters for {age_group!r}/{state!r}."
                )
            if not math.isclose(sum(probabilities), 1.0, rel_tol=1e-9, abs_tol=1e-9):
                raise ValueError(
                    f"Transition probabilities for {age_group!r}/{state!r} must sum to 1."
                )

            holding_time = holding_by_state[state]
            if not isinstance(holding_time, (int, float)) or holding_time < 0:
                raise ValueError(
                    f"Holding time for {age_group!r}/{state!r} must be non-negative."
                )


def _choose_next_state(age_group: str, current_state: str) -> str:
    """Choose the next state using the selected age group's probability row."""
    probabilities = TRANSITION_PROBS[age_group][current_state]
    destination_states = list(probabilities.keys())
    weights = list(probabilities.values())
    return random.choices(destination_states, weights=weights, k=1)[0]


def _simulate_person(
    person: Mapping[str, Union[int, str]],
    dates: Sequence[date],
) -> List[Dict[str, Union[int, str]]]:
    """Simulate one person's state for every date, inclusive of both endpoints."""
    age_group = str(person["age_group_name"])
    current_state = "H"
    staying_days = 0
    previous_state = "H"
    records: List[Dict[str, Union[int, str]]] = []

    for current_date in dates:
        records.append(
            {
                "person_id": int(person["person_id"]),
                "age_group_name": age_group,
                "country": str(person["country"]),
                "date": current_date.isoformat(),
                "state": current_state,
                "staying_days": staying_days,
                "prev_state": previous_state,
            }
        )

        # A holding time of zero is treated as one simulated day, as required.
        configured_holding_time = HOLDING_TIMES[age_group][current_state]
        effective_holding_time = max(int(configured_holding_time), 1)

        if staying_days + 1 >= effective_holding_time:
            old_state = current_state
            current_state = _choose_next_state(age_group, current_state)
            previous_state = old_state
            staying_days = 0
        else:
            previous_state = current_state
            staying_days += 1

    return records


def _create_summary(
    simulation_data: pd.DataFrame,
    dates: Sequence[date],
    countries: Sequence[str],
) -> pd.DataFrame:
    """Aggregate person states into one row per requested country and date."""
    date_strings = [item.isoformat() for item in dates]
    full_index = pd.MultiIndex.from_product(
        [date_strings, list(countries)], names=["date", "country"]
    )

    if simulation_data.empty:
        counts = pd.DataFrame(0, index=full_index, columns=SUMMARY_STATES)
    else:
        counts = (
            simulation_data.groupby(["date", "country", "state"])
            .size()
            .unstack("state", fill_value=0)
            .reindex(columns=SUMMARY_STATES, fill_value=0)
        )
        counts = counts.reindex(full_index, fill_value=0)
    summary = counts.reset_index()
    summary = summary[["date", "country", *SUMMARY_STATES]]
    for state in SUMMARY_STATES:
        summary[state] = summary[state].astype(int)
    return summary


def run(
    countries_csv_name: str,
    countries: Sequence[str],
    sample_ratio: float,
    start_date: DateLike,
    end_date: DateLike,
) -> pd.DataFrame:
    """Run the COVID-19 simulation and write all required output files.

    Args:
        countries_csv_name: Input CSV filename containing country data.
        countries: Names of countries to simulate.
        sample_ratio: Number of real people represented by each sample.
        start_date: First simulation date, formatted YYYY-MM-DD or a date object.
        end_date: Last simulation date, formatted YYYY-MM-DD or a date object.

    Returns:
        The country/date summary DataFrame (also written to the required CSV).
    """
    try:
        ratio = float(sample_ratio)
    except (TypeError, ValueError) as exc:
        raise ValueError("sample_ratio must be a positive number.") from exc
    if not math.isfinite(ratio) or ratio <= 0:
        raise ValueError("sample_ratio must be a positive finite number.")

    selected_countries = list(countries)
    if not selected_countries:
        raise ValueError("Select at least one country to simulate.")
    if len(set(selected_countries)) != len(selected_countries):
        raise ValueError("The countries list must not contain duplicate names.")

    first_day = _as_date(start_date, "start_date")
    last_day = _as_date(end_date, "end_date")
    if last_day < first_day:
        raise ValueError("end_date must be on or after start_date.")

    _validate_parameters()
    country_data = _read_country_data(countries_csv_name)
    population_samples = _build_population_samples(
        country_data, selected_countries, ratio
    )
    dates = [first_day + timedelta(days=offset)
             for offset in range((last_day - first_day).days + 1)]

    print(
        f"Simulating {len(population_samples)} sampled people across "
        f"{len(selected_countries)} country/countries for {len(dates)} days."
    )

    simulation_records: List[Dict[str, Union[int, str]]] = []
    for person in population_samples:
        simulation_records.extend(_simulate_person(person, dates))

    simulation_df = pd.DataFrame(
        simulation_records,
        columns=[
            "person_id", "age_group_name", "country", "date",
            "state", "staying_days", "prev_state",
        ],
    )
    simulated_path = BASE_DIR / SIMULATED_OUTPUT
    simulation_df.to_csv(simulated_path, index=False)

    summary_df = _create_summary(simulation_df, dates, selected_countries)
    summary_path = BASE_DIR / SUMMARY_OUTPUT
    summary_df.to_csv(summary_path, index=False)

    create_plot(str(summary_path), selected_countries)

    print(f"Individual time series saved to: {simulated_path}")
    print(f"Summary time series saved to: {summary_path}")
    print(f"Plot saved to: {BASE_DIR / PLOT_OUTPUT}")
    return summary_df


if __name__ == "__main__":
    run(
        countries_csv_name="a2-countries.csv",
        countries=["Afghanistan", "Sweden", "Japan"],
        sample_ratio=1e6,
        start_date="2021-04-01",
        end_date="2022-04-30",
    )
