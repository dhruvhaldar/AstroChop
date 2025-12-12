# AstroChop

![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)
![License: GPLv3](https://img.shields.io/badge/License-GPLv3-yellow.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)

**AstroChop** is a Python tool for generating interplanetary porkchop plots. It calculates the characteristic energy ($C_3$) and Time of Flight (TOF) for various launch and arrival dates, specifically focusing on Earth to Mars transfers.

## Features

- **Lambert Solver**: Implements a Universal Variables Lambert solver to calculate transfer orbits.
- **Analytical Ephemeris**: Uses simplified analytical ephemeris for Earth and Mars positions.
- **Visualization**: Generates contour plots of $C_3$ and TOF using Matplotlib.

## Installation

1.  Clone the repository.
2.  Navigate to the `astrochop` directory (if separate) or just use the root.
3.  Create a virtual environment:

    ```bash
    python -m venv venv
    ```

4.  Activate the virtual environment:

    - On Windows:
      ```powershell
      .\venv\Scripts\activate
      ```
    - On macOS/Linux:
      ```bash
      source venv/bin/activate
      ```

5.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

To generate the porkchop plot, run the main script.

```bash
# On macOS/Linux
source venv/bin/activate
python src/main.py
```

```powershell
# On Windows
.\venv\Scripts\activate
python src\main.py
```

This will generate a file named `astrochop.png` in the current directory.

## Running Tests

To run the unit tests, use the following command:

```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)/astrochop
python astrochop/tests/test_lambert.py
```

## Structure

- `src/lambert.py`: Lambert solver implementation.
- `src/ephemeris.py`: Planetary position calculations.
- `src/plotter.py`: Plotting and data generation logic.
- `src/main.py`: Entry point script.
- `tests/`: Unit tests.
