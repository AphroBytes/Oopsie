Game of Life: A Bash Bash-tard's Adventure
Welcome to the Game of Life, a chaotic, but surprisingly mesmerizing simulation of life and death in a cellular world. This version is written in bash, for the ultimate in... well, it's not about efficiency. It's about fun! So buckle up, grab a comfy chair, and let's get this show on the road.

Here's how it works:

The Grid: The core of our world is a grid of cells. Each cell can be either alive (1) or dead (0).
The Rules: These cells follow a strict set of rules, like a miniature society with a draconian code:
Underpopulation: A living cell with less than 2 living neighbours dies.
Survival: A living cell with 2 or 3 living neighbours survives.
Overpopulation: A living cell with more than 3 living neighbours dies.
Birth: A dead cell with exactly 3 living neighbours becomes a living cell.
Time Marches On: Every generation, these rules are applied simultaneously to every cell, leading to a dazzling cascade of births, deaths, and pattern formation.
Running the Game:

Make sure you have Minio installed. This is your object storage where we'll save the fascinating patterns we find.
Configure your environment: Open the config.sh file and set the MINIO_ENDPOINT, MINIO_ACCESS_KEY, and MINIO_SECRET_KEY to match your Minio setup.
Run the script: Simply execute ./game_of_life.sh.
The Visuals:

This script doesn't involve any fancy graphics. Instead, it will print the grid state to your console, giving you a text-based visualization. Every second, the game will update, and if it encounters a pattern that repeats at least 10 times, it will be saved as a .npy file to your Minio bucket.

Why Bash?

Because sometimes, the most straightforward approach is the most fun! Bash is a versatile language, and while it's not ideal for computationally intensive tasks, it's perfectly capable of creating this simple, yet mesmerizing simulation.

So, fire up the script and enjoy the chaos!

