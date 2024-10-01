from threading import Thread, Lock
from time import sleep
from random import randint
from typing import Tuple, Dict
from cython import nogil
import numpy as np
from numba import njit
import matplotlib.pyplot as plt
from dask import delayed
from dask.distributed import Client
from patternmatching import pattern_matching
from sklearn.cluster import DBSCAN
from minio import Minio

# Configuration
MINIO_ENDPOINT = "localhost:9000"  # Replace with your MinIO endpoint
MINIO_ACCESS_KEY = "your_access_key"  # Replace with your MinIO access key
MINIO_SECRET_KEY = "your_secret_key"  # Replace with your MinIO secret key
BUCKET_NAME = "game-of-life-patterns"

# Global variables
GRID_SIZE = 10000  # Initial grid size
CELL_STATES = {0: "Dead", 1: "Alive"}
lock = Lock()
client = Client(n_workers=16)  # Using 16 workers for parallelization

# Initialize MinIO client
minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False,
)
if not minio_client.bucket_exists(BUCKET_NAME):
    minio_client.make_bucket(BUCKET_NAME)

# Define sparse matrix representation
class SparseGrid:
    def __init__(self):
        self.grid = {}  # Use a dictionary for sparse representation

    def __getitem__(self, key: Tuple[int, int]) -> int:
        return self.grid.get(key, 0)

    def __setitem__(self, key: Tuple[int, int], value: int) -> None:
        if value == 0:
            self.grid.pop(key, None)
        else:
            self.grid[key] = value

    def __len__(self) -> int:
        return len(self.grid)

    def get_neighbours(self, x: int, y: int) -> int:
        """
        Counts live neighbours for a given cell using sparse representation.
        """
        count = 0
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                if dx == 0 and dy == 0:
                    continue
                neighbour_x = x + dx
                neighbour_y = y + dy
                if (neighbour_x, neighbour_y) in self.grid:
                    count += 1
        return count

@nogil
@njit
def _calculate_next_state(grid: np.ndarray, x: int, y: int, grid_size: int) -> int:
    """
    Calculates the next state of a cell using Numba for acceleration.
    """
    live_neighbours = 0
    for dx in range(-1, 2):
        for dy in range(-1, 2):
            if dx == 0 and dy == 0:
                continue
            nx = x + dx
            ny = y + dy
            if nx >= 0 and ny >= 0 and nx < grid_size and ny < grid_size:
                if grid[ny, nx] == 1:
                    live_neighbours += 1
    if grid[y, x] == 1:
        return 1 if live_neighbours in [2, 3] else 0
    else:
        return 1 if live_neighbours == 3 else 0

@nogil
@njit
def _update_grid(grid: np.ndarray, grid_size: int) -> np.ndarray:
    """
    Updates the entire grid using Numba for acceleration.
    """
    new_grid = np.zeros((grid_size, grid_size), dtype=np.int32)
    for y in range(grid_size):
        for x in range(grid_size):
            new_grid[y, x] = _calculate_next_state(grid, x, y, grid_size)
    return new_grid

def update_grid_thread(grid: SparseGrid, grid_size: int) -> None:
    """
    Thread function for updating the grid in parallel.
    """
    global lock
    with lock:
        # Convert the sparse grid to a dense NumPy array for Numba optimization
        dense_grid = np.zeros((grid_size, grid_size), dtype=np.int32)
        for key, value in grid.grid.items():
            dense_grid[key[1], key[0]] = value
        updated_grid = _update_grid(dense_grid, grid_size)
        # Convert the updated dense grid back to a sparse representation
        grid.grid = {}
        for y in range(grid_size):
            for x in range(grid_size):
                if updated_grid[y, x] == 1:
                    grid[(x, y)] = 1

def generate_initial_conditions(grid: SparseGrid, grid_size: int, density: float) -> None:
    """
    Generates random initial conditions for the Game of Life.
    """
    for y in range(grid_size):
        for x in range(grid_size):
            if randint(0, 100) / 100 <= density:
                grid[(x, y)] = 1

def analyze_patterns(grid: SparseGrid, grid_size: int) -> Dict[str, int]:
    """
    Analyzes the grid for repeating patterns using pattern matching and DBSCAN clustering.
    """
    # Convert sparse grid to a dense NumPy array for pattern matching
    dense_grid = np.zeros((grid_size, grid_size), dtype=np.int32)
    for key, value in grid.grid.items():
        dense_grid[key[1], key[0]] = value

    # Use pattern matching to identify potential patterns
    patterns = pattern_matching.find_patterns(dense_grid)

    # Use DBSCAN clustering to group similar patterns together
    clustered_patterns = DBSCAN(eps=5, min_samples=3).fit_predict(patterns)
    pattern_counts = {}
    for pattern_index, cluster in enumerate(clustered_patterns):
        if cluster not in pattern_counts:
            pattern_counts[cluster] = 0
        pattern_counts[cluster] += 1

    return pattern_counts

def save_pattern(grid: SparseGrid, grid_size: int, pattern_label: str) -> None:
    """
    Saves the current pattern to MinIO object storage.
    """
    # Convert sparse grid to a dense NumPy array for saving
    dense_grid = np.zeros((grid_size, grid_size), dtype=np.int32)
    for key, value in grid.grid.items():
        dense_grid[key[1], key[0]] = value

    # Save pattern to MinIO
    with open("pattern.npy", "wb") as f:
        np.save(f, dense_grid)
    minio_client.fput_object(BUCKET_NAME, f"{pattern_label}.npy", "pattern.npy")

def main() -> None:
    """
    Main function to run the Game of Life simulation.
    """
    grid = SparseGrid()
    generate_initial_conditions(grid, GRID_SIZE, 0.1)  # Initialize with 10% density
    threads = []
    for i in range(16):
        threads.append(Thread(target=update_grid_thread, args=(grid, GRID_SIZE)))
        threads[i].start()

    while True:
        for thread in threads:
            thread.join()
        pattern_counts = analyze_patterns(grid, GRID_SIZE)
        for pattern_index, count in pattern_counts.items():
            if count > 10:  # Save patterns that appear more than 10 times
                save_pattern(grid, GRID_SIZE, f"pattern_{pattern_index}")
                print(f"Saved pattern {pattern_index} to MinIO.")
        sleep(1)  # Update the grid every second

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Exiting...")
        client.shutdown()