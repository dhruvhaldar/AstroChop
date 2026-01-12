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

    launch_days = (end_launch - start_launch).days
    arrival_days = (end_arrival - start_arrival).days
    
    print(f"📅 Launch Window:  {start_launch.strftime('%Y-%m-%d')} to {end_launch.strftime('%Y-%m-%d')} ({launch_days} days)")
    print(f"📅 Arrival Window: {start_arrival.strftime('%Y-%m-%d')} to {end_arrival.strftime('%Y-%m-%d')} ({arrival_days} days)")

    # Estimate Flight Time Range
    min_tof = (start_arrival - end_launch).days
    max_tof = (end_arrival - start_launch).days
    print(f"⏳ Flight Time:    ~{min_tof} to ~{max_tof} days")

    # Generate dates
    launch_dates = [start_launch + timedelta(days=i) for i in range(0, (end_launch - start_launch).days, 5)]
    arrival_dates = [start_arrival + timedelta(days=i) for i in range(0, (end_arrival - start_arrival).days, 5)]
    
    total_traj = len(launch_dates) * len(arrival_dates)
    print(f"🚀 Computing {total_traj:,} trajectories...")
    
    ld, ad, C3, Vinf, TOF = generate_porkchop(launch_dates, arrival_dates, 'earth', 'mars', verbose=False)
    print("✨ Solution calculated.")

    # Find and display the optimal transfer (lowest C3)
    optimal_transfer = None
    try:
        min_idx = np.nanargmin(C3)
        unraveled = np.unravel_index(min_idx, C3.shape)

        # C3 is (n_arrival, n_launch) -> (row, col)
        opt_arrival_idx = unraveled[0]
        opt_launch_idx = unraveled[1]

        opt_launch_date = ld[opt_launch_idx]
        opt_arrival_date = ad[opt_arrival_idx]
        opt_c3 = C3[unraveled]
        opt_tof = TOF[unraveled]
        opt_vinf = Vinf[unraveled]

        # Pass rich data for annotation (dates, c3, tof, vinf)
        optimal_transfer = (opt_launch_date, opt_arrival_date, opt_c3, opt_tof, opt_vinf)

        print(f"\n🏆 Optimal Transfer Found:")
        print(f"   • Launch:  {opt_launch_date.strftime('%Y-%m-%d')}")
        print(f"   • Arrival: {opt_arrival_date.strftime('%Y-%m-%d')} (TOF: {opt_tof:.1f} days / {opt_tof/30.44:.1f} months)")
        print(f"   • Energy:  {opt_c3:.2f} km²/s² (C3)")
        print(f"   • Dep V_∞: {np.sqrt(opt_c3):.2f} km/s")
        print(f"   • Arr V_∞: {opt_vinf:.2f} km/s")

    except ValueError:
        # np.nanargmin raises ValueError if all values are NaN
        print("\n⚠️ No valid transfer window found in this range.")
    
    print("\n📊 Generating visualizations...")

    try:
        # Existing plotting
        plot_title = f"Earth-Mars Porkchop ({start_launch.year}): Min C3 = {opt_c3:.2f} km²/s²" if optimal_transfer else f"Earth-Mars Porkchop Plot ({start_launch.year} Opportunity)"
        plot_porkchop(ld, ad, C3, TOF, filename='astrochop.png', optimal_transfer=optimal_transfer, title=plot_title)
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
        print(f"     (💡 Tip: Open this file with ParaView to explore the 3D energy landscape!)")

        print("\n✅ Done.\n")

    except (ValueError, OSError) as e:
        print(f"\n❌ Error generating output files: {e}")
        # Exit with error code so CI/CD knows something failed
        import sys
        sys.exit(1)

if __name__ == "__main__":
    main()
