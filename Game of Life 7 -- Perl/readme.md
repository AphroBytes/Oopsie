# Game of Life: A Perl-y Adventure in Conway's World

Yo, Perl ninjas! 👾 Ready to witness the wonders of Conway's Game of Life? This Perl script will bring the classic cellular automata simulation to life, complete with parallel processing, pattern detection, and MinIO object storage. Let’s dive in!

## Getting Started

### Prerequisites

Ensure you have Perl installed on your machine. You can download it from [Perl's official site](https://www.perl.org/get.html).

### Install Dependencies

Before running the script, you'll need to install some dependencies. Use the following command to install the required Perl modules:

```bash
perl -MCPAN -e 'install MinIO::Client Time::HiRes Math::Random Data::Dumper Parallel::ForkManager JSON'
```

### Configure MinIO

To store detected patterns, you'll need a MinIO server running. You can run MinIO locally or remotely. If you run it locally, use the default endpoint (`localhost:9000`) with your access and secret keys.

## Running the Simulation

Once you've installed the dependencies and set up MinIO, you can run the script by executing the following command in your terminal:

```bash
perl game_of_life.pl
```

### What to Expect

Watch the magic unfold! 🪄 The script generates a Game of Life simulation with parallel updates. The pattern analysis result, detected patterns will be stored in your specified MinIO bucket.

## Code Overview

Here's a quick breakdown of the core components of the script:

1. **Configuration Constants**: Tune the parameters such as grid size, number of threads, density of initial live cells, and maximum iterations.

2. **SparseGrid Class**: This class manages the state of the grid efficiently using a sparse representation.

3. **Game Logic**:
   - `calculate_next_state`: Determines the next state of a cell based on its neighbors.
   - `generate_initial_conditions`: Fills the grid based on the specified density of live cells.

4. **Parallel Processing**:
   - `update_grid_thread`: Handles the grid update across multiple threads to improve performance.

5. **Pattern Analysis**: 
   - `analyze_patterns`: Identifies live cells and counts them.
   - `save_pattern`: Saves the pattern data to a JSON file and uploads it to MinIO.

6. **Main Function**: Initializes the grid, starts the threads, and manages the simulation loop.

## Important File Structure

- The script expects to save pattern data as JSON files named in the format `pattern-X.json` where X is the iteration number.
- Files are uploaded to a specified MinIO bucket.

## Conclusion

Let’s code, let’s explore, let’s make the Game of Life come alive with Perl! 🚀

If you have any issues or suggestions, feel free to open an issue on this repository!

Happy coding! 🎉
