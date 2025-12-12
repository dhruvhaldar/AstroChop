from datetime import datetime, timedelta
import numpy as np
from plotter import generate_porkchop, plot_porkchop

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
    
    print("Plotting...")
    plot_porkchop(ld, ad, C3, TOF, filename='astrochop.png')
    print("Done.")

if __name__ == "__main__":
    main()
