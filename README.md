# AstroChop

![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)
![License: GPLv3](https://img.shields.io/badge/License-GPLv3-yellow.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)

**AstroChop** is a Python tool for generating interplanetary porkchop plots. It calculates the characteristic energy ($C_3$) and Time of Flight (TOF) for various launch and arrival dates, specifically focusing on Earth to Mars transfers.

Loosely based on [Gravity Engine](https://nbodyphysics.com/blog/gravity-engine-doc-1-3-2-2-2/demonstrations-2/porkchop-plots-visualize-transfer-delta-v/)

![AstroChop Porkchop Plot](astrochop.png)

## Features

- **Lambert Solver**: Implements a Universal Variables Lambert solver to calculate transfer orbits.
- **Analytical Ephemeris**: Uses simplified analytical ephemeris for Earth and Mars positions.
- **Visualization**: Generates contour plots of $C_3$ and TOF using Matplotlib.
- **3D Mesh Export**: Generates a 3D surface mesh (`.vtp`) of the porkchop plot (Launch Date vs. Arrival Date vs. C3), which can be visualized interactively in tools like **ParaView**.

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

To generate the porkchop plot and 3D mesh, run the main script.

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

This will generate:
1.  `astrochop.png`: A 2D contour plot (Matplotlib).
2.  `earth_mars_porkchop.vtp`: A 3D mesh file (VTK PolyData).

### Viewing the 3D Mesh
Open `earth_mars_porkchop.vtp` in **ParaView**.
- Set "Representation" to "Surface" or "Surface With Edges".
- Set "Coloring" to "MorphedValue" or "NormalizedUV".
- You can apply a "Warp By Scalar" filter if you wish to see the terrain height even more exaggerated, though the mesh is already pre-morphed.

## Running Tests

To run the unit tests, use the following command:

```bash
export PYTHONPATH=$PYTHONPATH:.
python tests/test_lambert.py
python tests/test_porkchop_mesh.py
```

## Structure

- `src/lambert.py`: Lambert solver implementation.
- `src/ephemeris.py`: Planetary position calculations.
- `src/plotter.py`: Plotting and data generation logic.
- `src/porkchop_mesh.py`: Mesh generation, data morphing, and ray intersection logic.
- `src/mesh_exporter.py`: VTP file export logic.
- `src/main.py`: Entry point script.
- `tests/`: Unit tests.
