require 'thread'
require 'time'
require 'securerandom'
require 'numo/narray'
require 'matplotlib'
require 'dask'
require 'minio'
require 'patternmatching' 

# Configuration
MINIO_ENDPOINT = "localhost:9000"  # MinIO object storage endpoint
MINIO_ACCESS_KEY = "your_access_key"  # MinIO access key
MINIO_SECRET_KEY = "your_secret_key"  # MinIO secret key
BUCKET_NAME = "game-of-life-patterns"

# Global variables
GRID_SIZE = 100  # Initial grid size for visualization
LOCK = Mutex.new
CLIENT = Dask::Distributed::Client.new(n_workers: 16) # Parallelize with Dask

# Visualization related global variables
fig, ax = Matplotlib.pyplot.subplots

# Initialize MinIO client
minio_client = Minio::Client.new(
  MINIO_ENDPOINT,
  access_key: MINIO_ACCESS_KEY,
  secret_key: MINIO_SECRET_KEY,
  secure: false,
)

unless minio_client.bucket_exists?(BUCKET_NAME)
  minio_client.make_bucket(BUCKET_NAME)
end

class SparseGrid
  def initialize
    @grid = {} # Dictionary to represent the sparse grid
  end

  def [](key)
    @grid[key] || 0
  end

  def []=(key, value)
    if value == 0
      @grid.delete(key)
    else
      @grid[key] = value
    end
  end

  def length
    @grid.length
  end

  def get_neighbours(x, y)
    count = 0
    (-1..1).each do |dx|
      (-1..1).each do |dy|
        next if dx == 0 && dy == 0
        neighbour_x = x + dx
        neighbour_y = y + dy
        count += 1 if @grid.key?([neighbour_x, neighbour_y])
      end
    end
    count
  end
end

def calculate_next_state(grid, x, y, grid_size)
  live_neighbours = 0
  (-1..1).each do |dx|
    (-1..1).each do |dy|
      next if dx == 0 && dy == 0
      nx, ny = x + dx, y + dy
      if 0 <= nx && nx < grid_size && 0 <= ny && ny < grid_size
        live_neighbours += 1 if grid[ny, nx] == 1
      end
    end
  end
  if grid[y, x] == 1
    live_neighbours == 2 || live_neighbours == 3 ? 1 : 0
  else
    live_neighbours == 3 ? 1 : 0
  end
end

def update_grid(grid, grid_size)
  new_grid = Numo::Int32.zeros(grid_size, grid_size)
  (0...grid_size).each do |y|
    (0...grid_size).each do |x|
      new_grid[y, x] = calculate_next_state(grid, x, y, grid_size)
    end
  end
  new_grid
end

def update_grid_thread(grid, grid_size)
  LOCK.synchronize do
    dense_grid = Numo::Int32.zeros(grid_size, grid_size)
    grid.instance_variable_get(:@grid).each do |key, value|
      dense_grid[key[1], key[0]] = value
    end
    updated_grid = update_grid(dense_grid, grid_size)

    grid.instance_variable_get(:@grid).clear
    (0...grid_size).each do |y|
      (0...grid_size).each do |x|
        grid[(x, y)] = 1 if updated_grid[y, x] == 1
      end
    end

    ax.clear
    ax.imshow(updated_grid, cmap: 'binary', interpolation: 'nearest')
    ax.set_title('Game of Life: Generation')
    Matplotlib.pyplot.pause(0.01)
  end
end

def generate_initial_conditions(grid, grid_size, density)
  (0...grid_size).each do |y|
    (0...grid_size).each do |x|
      grid[(x, y)] = 1 if Random.rand < density    end
  end
end

def analyze_patterns(grid, grid_size)
  dense_grid = Numo::Int32.zeros(grid_size, grid_size)
  grid.instance_variable_get(:@grid).each do |key, value|
    dense_grid[key[1], key[0]] = value
  end

  patterns = PatternMatching.find_patterns(dense_grid)
  clustered_patterns = DBSCAN.new(eps: 5, min_samples: 3).fit_predict(patterns)
  pattern_counts = {}
  clustered_patterns.each do |cluster|
    if pattern_counts.key?(cluster)
    pattern_counts[cluster] ||= 0
      pattern_counts[cluster] += 1
  end
  pattern_counts
end

def save_pattern(grid, grid_size, pattern_label)
  grid.instance_variable_get(:@grid).each do |key, value|
  dense_grid = Numo::Int32.zeros(grid_size, grid_size)
    dense_grid[key[1], key[0]] = value
  end

  File.open("pattern.npy", "wb") do |f|
    Numo::NArray.to_file(f, dense_grid, 'binary', 'npy')
  end
  minio_client.fput_object(BUCKET_NAME, "#{pattern_label}.npy", "pattern.npy")
end

  def main
  grid = SparseGrid.new
  generate_initial_conditions(grid, GRID_SIZE, 0.1) # Initialize with 10% density

  Matplotlib.pyplot.ion

  threads = (0...16).map do
    Thread.new { update_grid_thread(grid, GRID_SIZE) }
  end

  loop do
    threads.each(&:join)
    pattern_counts = analyze_patterns(grid, GRID_SIZE)
    pattern_counts.each do |pattern_index, count|
      if count > 10 # Save patterns appearing more than 10 times
        save_pattern(grid, GRID_SIZE, "pattern_#{pattern_index}")
        puts "Saved pattern #{pattern_index} to MinIO."
      end
    end
    sleep(1) # Update the grid every second
  end
end

if __FILE__ == $0
  begin
    main
  rescue Interrupt
    puts "Exiting..."
    CLIENT.shutdown
  end
end
