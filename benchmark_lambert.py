
import time
import numpy as np
from lambert import lambert

def benchmark():
    # Setup a reasonably large problem
    N = 1000
    M = 1000
    print(f"Benchmarking Lambert with grid {N}x{M} = {N*M} points...")

    # Mock data
    r1 = np.random.rand(1, N, 3) * 1.5e8
    r2 = np.random.rand(M, 1, 3) * 2.2e8
    dt = np.random.rand(M, N) * 200 * 86400 # seconds

    mu = 1.327e11 # sun

    # Warmup
    print("Warmup...")
    lambert(r1[:, :10], r2[:10, :], dt[:10, :10], mu)

    # Run
    start_time = time.time()
    lambert(r1, r2, dt, mu)
    end_time = time.time()

    print(f"Execution time: {end_time - start_time:.4f} seconds")

if __name__ == "__main__":
    benchmark()
