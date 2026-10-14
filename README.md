# MazeLab — Maze with Keys and Doors

A polished Python 3.10+ Tkinter maze solver and visualizer for shortest-path searches through dynamic key-door mazes.

## Features

- CSV maze import and validation
- Random solvable maze generation
- BFS shortest-path calculation using `(row, column, key_mask)` states
- Path export to CSV with preserved maze metadata
- Modern Tkinter dashboard with status controls and animation

## Run the app

From the project root:

```powershell
py app.py
```

If Tkinter is not installed in your Python distribution, install Python from python.org with the Tcl/Tk feature enabled.

## CSV format

Use a square grid, for example:

```csv
S,.,.,#,.,.,.
#,a,.,#,.,A,.
#,#,.,.,.,#,.
.,.,.,#,.,.,E
```

Allowed cell types are:

- `.` open cell
- `#` wall
- `S` start
- `E` exit
- `a`-`f` keys
- `A`-`F` door markers (with `E` reserved for the exit)

## Testing

```powershell
python -m pytest -q
```

## Project layout

- `app.py` — application entry point
- `maze_lab/logic.py` — validation, BFS, generation, and CSV export logic
- `maze_lab/gui.py` — Tkinter dashboard and animation
- `tests/test_maze_logic.py` — BFS and validation tests
