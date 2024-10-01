#!/bin/bash

# Configuration
MINIO_ENDPOINT="localhost:9000"
MINIO_ACCESS_KEY="your_access_key"
MINIO_SECRET_KEY="your_secret_key"
BUCKET_NAME="game-of-life-patterns"
GRID_SIZE=100
DENSITY=0.1

# Initialize Minio client
function minio_client {
  mc --config ~/.mc --quiet
}

# Function to update the grid for one generation
function update_grid {
  local grid="$1"
  local new_grid=""

  for ((y=0; y<GRID_SIZE; y++)); do
    for ((x=0; x<GRID_SIZE; x++)); do
      local cell="${grid:$y*GRID_SIZE+x:1}"
      local neighbours=$(count_neighbours "$grid" "$x" "$y")

      if [[ "$cell" -eq 1 ]]; then
        if [[ "$neighbours" -eq 2 || "$neighbours" -eq 3 ]]; then
          new_grid="$new_grid1"
        else
          new_grid="$new_grid0"
        fi
      else
        if [[ "$neighbours" -eq 3 ]]; then
          new_grid="$new_grid1"
        else
          new_grid="$new_grid0"
        fi
      fi
    done
  done

  echo "$new_grid"
}

# Function to count the number of living neighbours for a cell
function count_neighbours {
  local grid="$1"
  local x="$2"
  local y="$3"
  local neighbours=0

  for ((dx=-1; dx<=1; dx++)); do
    for ((dy=-1; dy<=1; dy++)); do
      if [[ "$dx" -eq 0 && "$dy" -eq 0 ]]; then
        continue
      fi

      local nx=$((x + dx))
      local ny=$((y + dy))

      if [[ "$nx" -ge 0 && "$nx" -lt GRID_SIZE && "$ny" -ge 0 && "$ny" -lt GRID_SIZE ]]; then
        local neighbour_cell="${grid:$ny*GRID_SIZE+nx:1}"
        if [[ "$neighbour_cell" -eq 1 ]]; then
          ((neighbours++))
        fi
      fi
    done
  done

  echo "$neighbours"
}

# Function to generate random initial conditions for the grid
function generate_initial_conditions {
  local grid=""
  for ((i=0; i<GRID_SIZE*GRID_SIZE; i++)); do
    if ((RANDOM % 100 < DENSITY * 100)); then
      grid="$grid1"
    else
      grid="$grid0"
    fi
  done
  echo "$grid"
}

# Main function
function main {
  local grid=$(generate_initial_conditions)
  local generation=0

  while true; do
    echo "Generation $generation:"
    for ((y=0; y<GRID_SIZE; y++)); do
      echo "${grid:$y*GRID_SIZE:GRID_SIZE}"
    done

    grid=$(update_grid "$grid")
    ((generation++))
    sleep 1
  done
}

# Entry point
main