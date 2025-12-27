from datetime import datetime, timedelta
import numpy as np
from plotter import generate_porkchop, plot_porkchop, jd_from_date
from porkchop_mesh import DataGrid, PorkchopMesh
from mesh_exporter import write_vtp

def main():
    print("\n🎨 Earth-Mars Porkchop Plot Generator")
    print("------------------------------------")
    
    # Define date range
    # 2005 opportunity (approximate)
    start_launch = datetime(2005, 4, 1)
    end_launch = datetime(2005, 10, 1)
    
    start_arrival = datetime(2005, 11, 1)
    end_arrival = datetime(2006, 10, 1)

    print(f"📅 Launch Window:  {start_launch.strftime('%Y-%m-%d')} to {end_launch.strftime('%Y-%m-%d')}")
    print(f"📅 Arrival Window: {start_arrival.strftime('%Y-%m-%d')} to {end_arrival.strftime('%Y-%m-%d')}")
    
    # Generate dates
    launch_dates = [start_launch + timedelta(days=i) for i in range(0, (end_launch - start_launch).days, 5)]
    arrival_dates = [start_arrival + timedelta(days=i) for i in range(0, (end_arrival - start_arrival).days, 5)]
    
    total_traj = len(launch_dates) * len(arrival_dates)
    print(f"🚀 Computing {total_traj} trajectories...")
    
    ld, ad, C3, Vinf, TOF = generate_porkchop(launch_dates, arrival_dates, 'earth', 'mars', verbose=False)
    print("✨ Solution calculated.")

    # Find optimal transfer (minimum C3)
    try:
        min_c3_idx = np.nanargmin(C3)
        # Convert flat index to 2D index
        arr_idx, launch_idx = np.unravel_index(min_c3_idx, C3.shape)

        opt_launch = ld[launch_idx]
        opt_arrival = ad[arr_idx]
        opt_c3 = C3[arr_idx, launch_idx]
        opt_tof = TOF[arr_idx, launch_idx]

        print(f"\n🏆 Optimal Transfer Found:")
        print(f"   • Launch Date:  {opt_launch.strftime('%Y-%m-%d')}")
        print(f"   • Arrival Date: {opt_arrival.strftime('%Y-%m-%d')}")
        print(f"   • C3 Energy:    {opt_c3:.2f} km²/s²")
        print(f"   • Duration:     {opt_tof:.1f} days")
    except ValueError:
        print("\n⚠️  No valid trajectories found in this window.")
    
    print("\n📊 Generating visualizations...")

    # Existing plotting
    plot_porkchop(ld, ad, C3, TOF, filename='astrochop.png')
    print(f"   • Plot saved to: astrochop.png")

    # --- New Mesh Generation Logic ---
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

    x_mean = np.mean(x_axis)
    y_mean = np.mean(y_axis)
    grid.x_axis -= x_mean
    grid.y_axis -= y_mean

    mesh.generate_mesh(z_scale=50.0, morph_type='linear')

    # Export
    write_vtp('earth_mars_porkchop.vtp', mesh)
    print(f"   • 3D Mesh saved to: earth_mars_porkchop.vtp")

    print("\n✅ Done.\n")

if __name__ == "__main__":
    main()
