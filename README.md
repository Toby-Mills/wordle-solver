# wordle-solver
simple Python scripts using Pandas to solve Wordle puzzles.

By analysing letter frequencies, and assigning a score to all possible guesses (based on current game-state), it selects words to guess.

the project consists of two main parts:

* **wordle-solver**: the script that generates the next guess, based on the current game-state

* **wordle-server**: a test bed that automates selecting a random word (from the list), and invoking Wordle-Solver to solve the puzzle.
After each guess, it updates the game-state and invokes Wordle-Solver to get the next guess.

**Note:**
the game-state is loaded from a CSV file called 'Wordle Game State.csv', which has one line per guess made, with letters comma separated. Each letter can have a prefix to indicate the result. '+' means that the letter is in the correct position, '-' means that the letter is not in that, or any other position, '~' means that the letter is in the word, but not in that position.
