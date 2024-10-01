from threading import Thread, Lock
from time import sleep
from random import randint
from typing import Tuple, Dict, List
from cython import nogil
import numpy as np
import matplotlib.pyplot as plt
from numba import njit
from dask import delayed
from dask.distributed import Client
from patternmatching import pattern_matching
from sklearn.cluster import DBSCAN
from minio import Minio

# Configuration
MINIO_ENDPOINT = "localhost:9000"  # MinIO object storage endpoint
MINIO_ACCESS_KEY = "your_access_key"  # MinIO access key
MINIO_SECRET_KEY = "your_secret_key"  # MinIO secret key
BUCKET_NAME = "game-of-life-patterns"

# Global variables
GRID_SIZE = 100  # Initial grid size for visualization
LOCK = Lock()
CLIENT = Client(n_workers=16)  # Parallelize with Dask

# Visualization related global variables
fig, ax = plt.subplots()

# Initialize MinIO client
minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False,
)

if not minio_client.bucket_exists(BUCKET_NAME):
    minio_client.make_bucket(BUCKET_NAME)

class SparseGrid:
    """
    SparseGrid is a custom data structure to store alive and dead cells 
    in a sparse manner, where only the alive cells are kept in a dictionary.
    """
    def __init__(self):
        self.grid = {}  # Dictionary to represent the sparse grid

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
        Count live neighbours for a given cell using sparse representation.
        """
        count = 0
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0: continue
                neighbour_x = x + dx
                neighbour_y = y + dy
                if (neighbour_x, neighbour_y) in self.grid:
                    count += 1
        return count

@nogil
@njit
def _calculate_next_state(grid: np.ndarray, x: int, y: int, grid_size: int) -> int:
    """
    Calculates the next state of a cell using the rules of Conway's Game of Life.
    
    Args:
        grid (np.ndarray): The current state of the grid.
        x (int): x-coordinate of the cell.
        y (int): y-coordinate of the cell.
        grid_size (int): Size of the grid.

    Returns:
        int: The next state of the cell (1 for alive, 0 for dead).
    """
    live_neighbours = 0
    for dx in range(-1, 2):
        for dy in range(-1, 2):
            if dx == 0 and dy == 0: continue
            nx, ny = x + dx, y + dy
            if 0 <= nx < grid_size and 0 <= ny < grid_size:
                if grid[ny, nx] == 1:
                    live_neighbours += 1
    if grid[y, x] == 1:
        return int(live_neighbours in [2, 3])
    else:
        return int(live_neighbours == 3)

@nogil
@njit
def _update_grid(grid: np.ndarray, grid_size: int) -> np.ndarray:
    """
    Updates the entire grid for one time step.

    Args:
        grid (np.ndarray): The current state of the grid.
        grid_size (int): Size of the grid.

    Returns:
        np.ndarray: The updated state of the grid.
    """
    new_grid = np.zeros((grid_size, grid_size), dtype=np.int32)
    for y in range(grid_size):
        for x in range(grid_size):
            new_grid[y, x] = _calculate_next_state(grid, x, y, grid_size)
    return new_grid

def update_grid_thread(grid: SparseGrid, grid_size: int) -> None:
    """
    Thread function for updating the grid in parallel and also for visualization.

    Args:
        grid (SparseGrid): The sparse grid representation of the current Game of Life state.
        grid_size (int): Size of the grid.
    """
    global LOCK
    with LOCK:
        # Convert sparse grid to dense NumPy array
        dense_grid = np.zeros((grid_size, grid_size), dtype=np.int32)
        for key, value in grid.grid.items():
            dense_grid[key[1], key[0]] = value
        updated_grid = _update_grid(dense_grid, grid_size)
        
        # Update sparse grid from dense representation
        grid.grid.clear()
        for y in range(grid_size):
            for x in range(grid_size):
                if updated_grid[y, x] == 1:
                    grid[(x, y)] = 1
        
        # Visualization Code (Overly Complicated)
        ax.clear()
        ax.imshow(updated_grid, cmap='binary', interpolation='nearest')
        ax.set_title('Game of Life: Generation')
        plt.pause(0.01)  # Pause to update the visualization

def generate_initial_conditions(grid: SparseGrid, grid_size: int, density: float) -> None:
    """
    Generates random initial conditions of alive cells in the grid.

    Args:
        grid (SparseGrid): The sparse grid to be populated.
        grid_size (int): Size of the grid.
        density (float): The density of alive cells (from 0.0 to 1.0).
    """
    for y in range(grid_size):
        for x in range(grid_size):
            if randint(0, 100) / 100 <= density:
                grid[(x, y)] = 1

def analyze_patterns(grid: SparseGrid, grid_size: int) -> Dict[str, int]:
    """
    Analyzes the grid for repeating patterns using pattern matching and DBSCAN clustering.

    Args:
        grid (SparseGrid): The grid representation of the current Game of Life state.
        grid_size (int): Size of the grid.

    Returns:
        Dict[str, int]: A dictionary of pattern counts.
    """
    dense_grid = np.zeros((grid_size, grid_size), dtype=np.int32)
    for key, value in grid.grid.items():
        dense_grid[key[1], key[0]] = value

    patterns = pattern_matching.find_patterns(dense_grid)
    clustered_patterns = DBSCAN(eps=5, min_samples=3).fit_predict(patterns)
    pattern_counts = {}
    for cluster in clustered_patterns:
        if cluster in pattern_counts:
            pattern_counts[cluster] += 1
        else:
            pattern_counts[cluster] = 1
    return pattern_counts

def save_pattern(grid: SparseGrid, grid_size: int, pattern_label: str) -> None:
    """
    Saves the current pattern to MinIO object storage.

    Args:
        grid (SparseGrid): The grid representation of the current Game of Life state.
        grid_size (int): Size of the grid.
        pattern_label (str): Label for the pattern file.
    """
    dense_grid = np.zeros((grid_size, grid_size), dtype=np.int32)
    for key, value in grid.grid.items():
        dense_grid[key[1], key[0]] = value

    # Save pattern in .npy format to MinIO
    with open("pattern.npy", "wb") as f:
        np.save(f, dense_grid)
    minio_client.fput_object(BUCKET_NAME, f"{pattern_label}.npy", "pattern.npy")

def main() -> None:
    """
    Main function to run the Game of Life simulation with visualization.
    """
    grid = SparseGrid()
    generate_initial_conditions(grid, GRID_SIZE, 0.1)  # Initialize with 10% density

    # Visualization initialization
    plt.ion()
    
    threads = [Thread(target=update_grid_thread, args=(grid, GRID_SIZE)) for _ in range(16)]
    
    for thread in threads:
        thread.start()
    
    while True:
        for thread in threads:
            thread.join()
        pattern_counts = analyze_patterns(grid, GRID_SIZE)
        for pattern_index, count in pattern_counts.items():
            if count > 10:  # Save patterns appearing more than 10 times
                save_pattern(grid, GRID_SIZE, f"pattern_{pattern_index}")
                print(f"Saved pattern {pattern_index} to MinIO.")
        sleep(1)  # Update the grid every second

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Exiting...")
        CLIENT.shutdown()