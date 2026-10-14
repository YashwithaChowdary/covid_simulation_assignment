# COVID-19 Spread Simulation — Assignment 2

This folder contains a Python implementation of the assignment, the provided
country dataset and transition/holding-time parameters, a Streamlit interface,
and the generated simulation outputs.

## Files

- `assignment2.py` — main simulation and `run()` entry point.
- `streamlit_ui.py` — Streamlit interface for selecting parameters and countries.
- `sim_parameters.py` — transition probabilities and holding times supplied for the assignment.
- `helper.py` — chart generation helper. It retains the required `create_plot()` interface and supports selecting one or more countries.
- `a2-countries.csv` — country population and age-distribution input.
- `test.py` — supplied test driver, copied under the conventional filename.
- `assignment2.txt`, `streamlit_ui.txt`, and matching support `.txt` files — text copies of the corresponding Python source files as requested in the assignment brief.
- `a2-covid-simulated-timeseries.csv` — individual/day simulation output.
- `a2-covid-summary-timeseries.csv` — per-country daily state counts.
- `a2-covid-simulation.png` — generated chart.

## Requirements

Python 3.9 or later is recommended. Install the dependencies in a terminal from
this folder:

```bash
python -m pip install -r requirements.txt
```

## Run the provided test

From this folder, run:

```bash
python test.py
```

The test invokes `assignment2.run()` with Afghanistan, Sweden and Japan for
2021-04-01 through 2022-04-30. Successful execution regenerates the two CSV
files and the plot in this folder.

## Run the simulation directly

```bash
python assignment2.py
```

To use different countries or dates, edit the example call in the
`if __name__ == "__main__":` section of `assignment2.py`, or call
`assignment2.run(...)` from another Python script.

## Start the Streamlit app

From this folder, run:

```bash
streamlit run streamlit_ui.py
```

Streamlit will print a local URL, usually `http://localhost:8501`. Open it in a
browser, choose a sample ratio, start/end dates, and one or more countries, and
click **Run**. The generated chart appears in the app; the CSV and PNG output
files are saved alongside the Python files.

## Notes

The simulation is stochastic, so results and the chart can vary from run to
run. The sample count for each country is based on the integer population/sample
ratio, and age-group counts are rounded from the country's published age shares.
