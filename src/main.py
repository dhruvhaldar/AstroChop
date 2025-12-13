from datetime import datetime, timedelta
import numpy as np
from plotter import generate_porkchop, plot_porkchop, jd_from_date
from porkchop_mesh import DataGrid, PorkchopMesh
from mesh_exporter import write_vtp

def main():
    print("Generating Earth-Mars Porkchop Plot...")
    
    # Define date range
    # 2005 opportunity (approximate)
    start_launch = datetime(2005, 4, 1)
    end_launch = datetime(2005, 10, 1)
    
    start_arrival = datetime(2005, 11, 1)
    end_arrival = datetime(2006, 10, 1)
    
    # Generate dates
    launch_dates = [start_launch + timedelta(days=i) for i in range(0, (end_launch - start_launch).days, 5)]
    arrival_dates = [start_arrival + timedelta(days=i) for i in range(0, (end_arrival - start_arrival).days, 5)]
    
    print(f"Calculating for {len(launch_dates)} launch dates and {len(arrival_dates)} arrival dates.")
    
    ld, ad, C3, Vinf, TOF = generate_porkchop(launch_dates, arrival_dates, 'earth', 'mars')
    
    # Existing plotting
    print("Plotting PNG...")
    plot_porkchop(ld, ad, C3, TOF, filename='astrochop.png')

    # --- New Mesh Generation Logic ---
    print("Generating Mesh...")

    # Convert dates to floats (JDs) for the axes
    x_axis = np.array([jd_from_date(d) for d in ld])
    y_axis = np.array([jd_from_date(d) for d in ad])

    # Create DataGrid using C3 energy
    grid = DataGrid(C3, x_axis, y_axis)

    # Create Mesh
    mesh = PorkchopMesh(grid)

    # Generate Mesh Geometry
    # Using log_10 because C3 can vary significantly
    # Scaling Z by 1000 for visibility in ParaView (otherwise days/dates values might dwarf it)
    # Actually dates are JDs (~2.45e6), so Z needs to be comparable or we need to offset X/Y.
    # JDs are huge. Let's subtract the mean to center the mesh near origin.

    print("Centering coordinates for better mesh visualization...")
    x_mean = np.mean(x_axis)
    y_mean = np.mean(y_axis)
    grid.x_axis -= x_mean
    grid.y_axis -= y_mean

    mesh.generate_mesh(z_scale=50.0, morph_type='log_10')

    # Export
    print("Exporting VTP...")
    write_vtp('earth_mars_porkchop.vtp', mesh)

    # Test Ray Intersection (Simulate a click in the middle)
    # Midpoint of centered grid is roughly (0,0)
    ray_origin = np.array([0.0, 0.0, 1000.0]) # High above
    ray_dir = np.array([0.0, 0.0, -1.0]) # Straight down

    t, idx, pt = mesh.intersect_ray(ray_origin, ray_dir)

    if idx != -1:
        val = mesh.scalars.flatten()[mesh.indices[idx][0]]
        print(f"Ray Hit at {pt}, Triangle {idx}, Value ~{val:.2f}")
    else:
        print("Ray Missed")

    print("Done.")

if __name__ == "__main__":
    main()
