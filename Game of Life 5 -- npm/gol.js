const { Client } = require('dask');
const { MinioClient } = require('minio');
const { njit } = require('numba');
const { find_patterns } = require('patternmatching');
const { DBSCAN } = require('sklearn').cluster;
const { promisify } = require('util');

const MINIO_ENDPOINT = 'localhost:9000';
const MINIO_ACCESS_KEY = 'your_access_key';
const MINIO_SECRET_KEY = 'your_secret_key';
const BUCKET_NAME = 'game-of-life-patterns';

const GRID_SIZE = 100;
const NUM_WORKERS = 16;

const client = new Client({
  n_workers: NUM_WORKERS,
  threads_per_worker: 1
});

const minioClient = new MinioClient({
  endPoint: MINIO_ENDPOINT,
  accessKey: MINIO_ACCESS_KEY,
  secretKey: MINIO_SECRET_KEY,
  useSSL: false
});

const fputObject = promisify(minioClient.fputObject).bind(minioClient);

class SparseGrid {
  constructor() {
    this.grid = {};
  }

  get(key) {
    return this.grid[key] || 0;
  }

  set(key, value) {
    if (value === 0) {
      delete this.grid[key];
    } else {
      this.grid[key] = value;
    }
  }

  size() {
    return Object.keys(this.grid).length;
  }

  countNeighbours(x, y) {
    let count = 0;
    for (let dx = -1; dx <= 1; dx++) {
      for (let dy = -1; dy <= 1; dy++) {
        if (dx === 0 && dy === 0) continue;
        const neighbourX = x + dx;
        const neighbourY = y + dy;
        if (this.grid[`${neighbourX},${neighbourY}`]) {
          count++;
        }
      }
    }
    return count;
  }
}

@njit
function calculateNextState(grid, x, y, gridSize) {
  let liveNeighbours = 0;
  for (let dx = -1; dx <= 1; dx++) {
    for (let dy = -1; dy <= 1; dy++) {
      if (dx === 0 && dy === 0) continue;
      const nx = x + dx;
      const ny = y + dy;
      if (0 <= nx && nx < gridSize && 0 <= ny && ny < gridSize) {
        if (grid[ny][nx] === 1) {
          liveNeighbours++;
        }
      }
    }
  }
  if (grid[y][x] === 1) {
    return liveNeighbours === 2 || liveNeighbours === 3 ? 1 : 0;
  } else {
    return liveNeighbours === 3 ? 1 : 0;
  }
}

@njit
function updateGrid(grid, gridSize) {
  const newGrid = new Array(gridSize).fill(0).map(() => new Array(gridSize).fill(0));
  for (let y = 0; y < gridSize; y++) {
    for (let x = 0; x < gridSize; x++) {
      newGrid[y][x] = calculateNextState(grid, x, y, gridSize);
    }
  }
  return newGrid;
}

async function updateGridThread(grid, gridSize) {
  const denseGrid = new Array(gridSize).fill(0).map(() => new Array(gridSize).fill(0));
  for (const [key, value] of Object.entries(grid.grid)) {
    const [x, y] = key.split(',').map(Number);
    denseGrid[y][x] = value;
  }

  const updatedGrid = updateGrid(denseGrid, gridSize);

  grid.grid = {};
  for (let y = 0; y < gridSize; y++) {
    for (let x = 0; x < gridSize; x++) {
      if (updatedGrid[y][x] === 1) {
        grid.set(`${x},${y}`, 1);
      }
    }
  }
}

function generateInitialConditions(grid, gridSize, density) {
  for (let y = 0; y < gridSize; y++) {
    for (let x = 0; x < gridSize; x++) {
      if (Math.random() <= density) {
        grid.set(`${x},${y}`, 1);
      }
    }
  }
}

function analyzePatterns(grid, gridSize) {
  const denseGrid = new Array(gridSize).fill(0).map(() => new Array(gridSize).fill(0));
  for (const [key, value] of Object.entries(grid.grid)) {
    const [x, y] = key.split(',').map(Number);
    denseGrid[y][x] = value;
  }

  const patterns = find_patterns(denseGrid);
  const clusteredPatterns = new DBSCAN({ eps: 5, minSamples: 3 }).fit_predict(patterns);
  const patternCounts = {};
  for (const cluster of clusteredPatterns) {
    patternCounts[cluster] = (patternCounts[cluster] || 0) + 1;
  }
  return patternCounts;
}

async function savePattern(grid, gridSize, patternLabel) {
  const denseGrid = new Array(gridSize).fill(0).map(() => new Array(gridSize).fill(0));
  for (const [key, value] of Object.entries(grid.grid)) {
    const [x, y] = key.split(',').map(Number);
    denseGrid[y][x] = value;
  }

  await fputObject(BUCKET_NAME, `${patternLabel}.npy`, Buffer.from(JSON.stringify(denseGrid)));
}

async function main() {
  const grid = new SparseGrid();
  generateInitialConditions(grid, GRID_SIZE, 0.1); 

  let lastPatternCounts = {};

  while (true) {
    const promises = Array.from({ length: NUM_WORKERS }).map(() => updateGridThread(grid, GRID_SIZE));
    await Promise.all(promises);

    const patternCounts = analyzePatterns(grid, GRID_SIZE);
    for (const [patternIndex, count] of Object.entries(patternCounts)) {
      if (count > 10 && lastPatternCounts[patternIndex] !== count) {
        await savePattern(grid, GRID_SIZE, `pattern_${patternIndex}`);
        console.log(`Saved pattern ${patternIndex} to Minio.`);
        lastPatternCounts[patternIndex] = count;
      }
    }
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
}

client.run(main).then(() => client.close());
