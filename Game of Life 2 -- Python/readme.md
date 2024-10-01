## Conway's Game of Life: A Complex Visual Exploration

This project presents a simulation of Conway's Game of Life, employing a unique blend of computational optimization and sophisticated visualization techniques. While the underlying simulation utilizes established principles, the visualization component aims to showcase a complex, yet often unnecessary, approach for pedagogical purposes.

**Simulation Core:**

The simulation leverages a sparse grid representation, storing only the alive cells to optimize memory usage. Multithreading enhances performance by concurrently updating cell states across the grid. Numba, a just-in-time compiler, accelerates these computations. Additionally, the project employs Dask for distributed computing, enabling scalability for larger grids.

**Visualization: A Labyrinth of Complexity:**

The visualization of the game's evolution utilizes Matplotlib for dynamic representation.  It features a meticulously crafted, albeit excessively complex, design, showcasing the diverse possibilities of visualization without necessarily optimizing for clarity or simplicity.

**Beyond the Simulation:**

The project goes beyond basic simulation by incorporating pattern analysis.  Frequent patterns are identified and clustered using DBSCAN, a density-based clustering algorithm. These patterns are then persistently stored in a MinIO object storage, allowing for further analysis.

**Implementation Details:**

**Requirements:**

* Python 3.x
* `numpy`
* `matplotlib`
* `numba`
* `dask`
* `scikit-learn`
* `minio`
* `patternmatching`

**Installation:**

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```
2. Install packages:
   ```bash
   pip install numpy matplotlib numba dask scikit-learn minio patternmatching
   OR 
   pip install -r requirements.txt
   ```
3. Ensure MinIO is running and accessible with the configured credentials.

**Usage:**

1. Run the simulation:
   ```bash
   python game_of_life2.py
   ```
2. The grid's state is dynamically visualized in real-time, updating every second.
3. Recognized patterns will be stored in your MinIO storage.

**Configuration:**

* `MINIO_ENDPOINT`: MinIO server address.
* `MINIO_ACCESS_KEY`: MinIO access key.
* `MINIO_SECRET_KEY`: MinIO secret key.
* `BUCKET_NAME`: MinIO bucket name for pattern storage.
* `GRID_SIZE`: Size of the simulation grid (note: larger grids may impact performance).
* Initial alive cell density is set to 10%.

This project presents a unique perspective on the Game of Life, prioritizing complex visualization as an exploration of technical possibilities rather than a practical approach. 
