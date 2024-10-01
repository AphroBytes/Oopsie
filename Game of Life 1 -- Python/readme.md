## Game of Life: A Fun, Fancy, & (Maybe) Fast Simulation

This here's a Python program that brings Conway's Game of Life to life! We've made it super fast, with a few fancy features. 

**What Makes This Game Special?**

* **Super Efficient:**  We use a special "dictionary trick" to only store the cells that are alive, saving a ton of space.
* **Blazing Fast:**  We've whipped up some code magic with Numba and Cython, making our calculations super speedy!
* **Multi-Threading Mayhem:**  This program uses 16 threads at once, making it run even faster. It's like having 16 tiny helpers working together!
* **Pattern Detective:**  This code can recognize patterns in the game, kinda like figuring out a secret code!
* **MinIO Storage:**  We use MinIO to store all the cool patterns we find, like a secret treasure chest!
* **Fancy Visualization (Coming Soon):** We're working on making the game look really pretty with matplotlib, like a colorful moving picture! 

**Getting Ready to Play:**

* **You'll Need:**
    * Python 3.7 or newer (don't worry, if you have Python it's probably new enough)
    * `cython` (for super fast code)
    * `numba` (also for super fast code)
    * `matplotlib` (for the pretty pictures, coming soon)
    * `dask` (for multitasking with threads)
    * `distributed` (for more multitasking with threads)
    * `patternmatching` (for the pattern detective work)
    * `scikit-learn` (for more pattern magic)
    * `minio` (for the secret treasure chest of patterns)

* **Installation:**
    1. **MinIO:**  Use the magic words:
        ```bash
        brew install minio 
        ```
        (If you don't have `brew`, you can find MinIO install instructions online)
    2. **Libraries:**  Type this into your computer's command line:
        ```bash
        pip install cython numba matplotlib dask distributed patternmatching scikit-learn minio
		OR 
	    pip install -r requirements.txt
        ``` 
    3. **Start the MinIO Server:**
        ```bash
        minio server /path/to/data
        ```
        (Change `/path/to/data` to where you want to store your patterns)

* **Configuration:**  In the code, you'll need to tell it where your MinIO server is. Replace these things with the right info:
    * `MINIO_ENDPOINT`
    * `MINIO_ACCESS_KEY`
    * `MINIO_SECRET_KEY`

**How to Play:**

1. **Save the code:** Copy and paste the code into a file called `game_of_life.py`.
2. **Run the game:**  In your computer's command line, type:
    ```bash
    python game_of_life.py
    ```

**What Happens:**

* The game will run and start making patterns.
* The patterns get saved to your MinIO server.
* You'll see messages in your command line saying when patterns get saved.

**What's Next:**

* We're gonna make the game even better by:
    * Adding really pretty pictures with `matplotlib`.
    * Making it more robust by adding error messages and logging.
    * Making the pattern detection even more accurate and efficient. 

**Important Note:**

This code is all about making the Game of Life fast and memory-efficient, so it can handle lots of cells! The pattern analysis is focused on finding patterns that are unique and can reproduce themselves. There's always room for improvement, so feel free to play around and make it your own!
