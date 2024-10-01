package main

import (
	"fmt"
	"math/rand"
	"sync"
	"time"

	"github.com/minio/minio-go/v7"
	"github.com/minio/minio-go/v7/pkg/credentials"
	"gonum.org/v1/plot"
	"gonum.org/v1/plot/plotter"
	"gonum.org/v1/plot/vg"
)

// Configuration
const (
	MINIO_ENDPOINT  = "localhost:9000"
	MINIO_ACCESS_KEY = "your_access_key"
	MINIO_SECRET_KEY = "your_secret_key"
	BUCKET_NAME      = "game-of-life-patterns"
	GRID_SIZE        = 100
	DENSITY          = 0.1
)

// Global variables
var (
	LOCK   sync.Mutex
	client *minio.Client
)

// SparseGrid is a custom data structure to store alive and dead cells in a sparse manner,
// where only the alive cells are kept in a map.
type SparseGrid map[int]map[int]bool

// Initialize MinIO client
func init() {
	var err error
	client, err = minio.New(MINIO_ENDPOINT, &minio.Options{
		Creds:  credentials.NewStaticV4(MINIO_ACCESS_KEY, MINIO_SECRET_KEY, ""),
		Secure: false,
	})
	if err != nil {
		panic(err)
	}

	// Create the bucket if it doesn't exist
	if _, err := client.BucketExists(BUCKET_NAME); err != nil {
		if err := client.MakeBucket(BUCKET_NAME, minio.MakeBucketOptions{Region: "us-east-1"}); err != nil {
			panic(err)
		}
	}
}

// GetNeighbours counts live neighbours for a given cell using sparse representation.
func (g SparseGrid) GetNeighbours(x, y int) int {
	count := 0
	for dx := -1; dx <= 1; dx++ {
		for dy := -1; dy <= 1; dy++ {
			if dx == 0 && dy == 0 {
				continue
			}
			nx := x + dx
			ny := y + dy
			if _, ok := g[nx]; ok {
				if _, ok := g[nx][ny]; ok {
					count++
				}
			}
		}
	}
	return count
}

// CalculateNextState calculates the next state of a cell using the rules of Conway's Game of Life.
func CalculateNextState(grid SparseGrid, x, y int) bool {
	liveNeighbours := grid.GetNeighbours(x, y)
	if _, ok := grid[x][y]; ok {
		return liveNeighbours == 2 || liveNeighbours == 3
	}
	return liveNeighbours == 3
}

// UpdateGrid updates the entire grid for one time step.
func UpdateGrid(grid SparseGrid) SparseGrid {
	newGrid := make(SparseGrid)
	for x := 0; x < GRID_SIZE; x++ {
		for y := 0; y < GRID_SIZE; y++ {
			if CalculateNextState(grid, x, y) {
				if _, ok := newGrid[x]; !ok {
					newGrid[x] = make(map[int]bool)
				}
				newGrid[x][y] = true
			}
		}
	}
	return newGrid
}

// GenerateInitialConditions generates random initial conditions of alive cells in the grid.
func GenerateInitialConditions(grid SparseGrid) {
	rand.Seed(time.Now().UnixNano())
	for x := 0; x < GRID_SIZE; x++ {
		for y := 0; y < GRID_SIZE; y++ {
			if rand.Float64() <= DENSITY {
				if _, ok := grid[x]; !ok {
					grid[x] = make(map[int]bool)
				}
				grid[x][y] = true
			}
		}
	}
}

// SavePattern saves the current pattern to MinIO object storage.
func SavePattern(grid SparseGrid, patternLabel string) error {
	data := make([][]int, GRID_SIZE)
	for x := 0; x < GRID_SIZE; x++ {
		data[x] = make([]int, GRID_SIZE)
		for y := 0; y < GRID_SIZE; y++ {
			if _, ok := grid[x][y]; ok {
				data[x][y] = 1
			}
		}
	}

	// Save pattern in .npy format to MinIO
	return client.FPutObject(BUCKET_NAME, fmt.Sprintf("%s.npy", patternLabel), "pattern.npy", data, minio.PutObjectOptions{})
}

// UpdateGridThread is a thread function for updating the grid in parallel.
func UpdateGridThread(grid *SparseGrid) {
	LOCK.Lock()
	defer LOCK.Unlock()
	*grid = UpdateGrid(*grid)
}

// VisualizeGrid visualizes the current state of the grid.
func VisualizeGrid(grid SparseGrid) {
	pts := make(plotter.XYs, 0)
	for x := 0; x < GRID_SIZE; x++ {
		for y := 0; y < GRID_SIZE; y++ {
			if _, ok := grid[x][y]; ok {
				pts = append(pts, plotter.XY{X: float64(x), Y: float64(y)})
			}
		}
	}

	p := plot.New()
	s, err := plotter.NewScatter(pts)
	if err != nil {
		panic(err)
	}
	p.Add(s)
	p.X.Min = 0
	p.X.Max = float64(GRID_SIZE)
	p.Y.Min = 0
	p.Y.Max = float64(GRID_SIZE)
	p.Title.Text = "Game of Life"
	if err := p.Save(4*vg.Inch, 4*vg.Inch, "grid.png"); err != nil {
		panic(err)
	}
}

func main() {
	grid := make(SparseGrid)
	GenerateInitialConditions(grid)

	// Visualization initialization
	VisualizeGrid(grid)
	
	var wg sync.WaitGroup
	wg.Add(16)

	// Create and start 16 goroutines for parallel grid updates
	for i := 0; i < 16; i++ {
		go func(i int) {
			defer wg.Done()
			for {
				UpdateGridThread(&grid)
			}
		}(i)
	}

	for {
		wg.Wait() // Wait for all goroutines to complete a grid update
		// Perform analysis and pattern saving
		// ... (add your pattern analysis logic here)

		// Update visualization
		VisualizeGrid(grid)

		time.Sleep(1 * time.Second) // Update the grid every second
	}
}
