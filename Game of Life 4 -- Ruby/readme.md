Welcome to the Conway's Game of Life simulator!

This program brings the fascinating world of Conway's Game of Life to your screen, with a touch of Ruby magic and parallel processing.

What is the Game of Life?

It's a cellular automaton, meaning it's a system that evolves based on simple rules. Imagine a grid of cells, each either alive or dead. The rules for each cell are:

Born: A dead cell becomes alive if it has exactly three live neighbours.
Survive: A live cell survives if it has two or three live neighbours.
Die: A live cell dies if it has fewer than two live neighbours (underpopulation) or more than three (overpopulation).

How to Play:

Install Ruby: If you don't have Ruby installed, you can download it from
https://www.ruby-lang.org/en/
.
Install Dependencies: Make sure you have the required gems installed (e.g., dask, minio, matplotlib, patternmatching). You can use gem install for this.

Run the Script: Open a terminal and run the script using ruby game_of_life.rb.
Watch the Magic: Enjoy the mesmerizing patterns that emerge from the simple rules of the Game of Life. The program will visualize the evolving grid and save interesting patterns to MinIO for later analysis.

Get Creative:

Change the Initial Conditions: Modify the generate_initial_conditions method to experiment with different starting configurations of alive cells.
Customize the Visualization: Play with the Matplotlib options in the update_grid_thread method to adjust colors, sizes, and more.
Explore Pattern Matching: Dive deeper into the analyze_patterns method and tweak the parameters of the pattern matching algorithm to see how different patterns are identified.
Let the patterns surprise you!

P.S. Don't forget to configure the MinIO access details in the beginning of the script to store those awesome patterns you discover.