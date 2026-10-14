from __future__ import annotations

import csv
import random
from collections import deque
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

KEYS = "abcdef"
DOORS = "ABCDF"
VALID_KEY_DOOR_PAIRS = [("a", "A"), ("b", "B"), ("c", "C"), ("d", "D"), ("f", "F")]
DIRECTIONS = ((-1, 0), (1, 0), (0, -1), (0, 1))
KEY_TO_DOOR = {key: key.upper() for key in KEYS}
KEY_BITS = {key: 1 << index for index, key in enumerate(KEYS)}


def validate_grid(grid: Sequence[Sequence[str]]) -> tuple[Tuple[int, int], Tuple[int, int], set[str], set[str]]:
    if grid is None or not grid:
        raise ValueError("The maze grid cannot be empty.")
    if len(grid) < 2:
        raise ValueError("Maze size must be at least 2x2.")
    size = len(grid)
    if any(len(row) != size for row in grid):
        raise ValueError("The maze must be square and contain the same number of columns in every row.")

    allowed = set(".#SEabcdefABCDEF")
    start_positions: list[Tuple[int, int]] = []
    exit_positions: list[Tuple[int, int]] = []
    key_types: set[str] = set()
    door_types: set[str] = set()

    for r, row in enumerate(grid):
        for c, cell in enumerate(row):
            if cell not in allowed:
                raise ValueError(f"Invalid cell {cell!r} at row {r + 1}, column {c + 1}.")
            if cell == "S":
                start_positions.append((r, c))
            elif cell == "E":
                exit_positions.append((r, c))
            elif cell in KEYS:
                key_types.add(cell)
            elif cell in DOORS:
                door_types.add(cell.lower())

    if len(start_positions) != 1:
        raise ValueError("The maze must contain exactly one start cell (S).")
    if len(exit_positions) != 1:
        raise ValueError("The maze must contain exactly one exit cell (E).")

    missing_doors = sorted(door_types - key_types)
    if missing_doors:
        missing = ", ".join(sorted(letter.upper() for letter in missing_doors))
        raise ValueError(f"Door(s) {missing} have no matching key in the maze.")

    return start_positions[0], exit_positions[0], key_types, door_types


def read_grid_csv(filename: str | Path) -> list[list[str]]:
    rows: list[list[str]] = []
    with open(filename, newline="", encoding="utf-8-sig") as handle:
        for raw_row in csv.reader(handle):
            if not raw_row or all(not cell.strip() for cell in raw_row):
                continue
            if len(raw_row) == 1 and len(raw_row[0].strip()) > 1 and "," not in raw_row[0]:
                row = list(raw_row[0].strip())
            else:
                row = [cell.strip() for cell in raw_row]
            rows.append(row)

    if not rows:
        raise ValueError("The CSV file is empty.")

    size = len(rows)
    if any(len(row) != size for row in rows):
        raise ValueError("The CSV grid must be square with the same number of cells in every row.")

    validate_grid(rows)
    return rows


def solve_maze(grid: Sequence[Sequence[str]]) -> tuple[int, list[tuple[int, int, int]], int]:
    start, exit_pos, _, _ = validate_grid(grid)
    size = len(grid)
    start_state = (start[0], start[1], 0)
    queue: deque[tuple[int, int, int]] = deque([start_state])
    distance: dict[tuple[int, int, int], int] = {start_state: 0}
    parent: dict[tuple[int, int, int], tuple[int, int, int] | None] = {start_state: None}
    final_state: tuple[int, int, int] | None = None

    while queue:
        row, col, mask = queue.popleft()
        if (row, col) == exit_pos:
            final_state = (row, col, mask)
            break

        for dr, dc in DIRECTIONS:
            next_row = row + dr
            next_col = col + dc
            if not (0 <= next_row < size and 0 <= next_col < size):
                continue

            cell = grid[next_row][next_col]
            if cell == "#":
                continue

            if cell in DOORS and not (mask & KEY_BITS.get(cell.lower(), 0)):
                continue

            next_mask = mask
            if cell in KEYS:
                next_mask |= KEY_BITS[cell]

            next_state = (next_row, next_col, next_mask)
            if next_state in distance:
                continue

            distance[next_state] = distance[(row, col, mask)] + 1
            parent[next_state] = (row, col, mask)
            queue.append(next_state)

    if final_state is None:
        return -1, [], len(distance)

    path_states: list[tuple[int, int, int]] = []
    cursor = final_state
    while cursor is not None:
        path_states.append(cursor)
        cursor = parent[cursor]
    path_states.reverse()
    return distance[final_state], path_states, len(distance)


def shortest_path(grid: Sequence[Sequence[str]]) -> tuple[int, list[tuple[int, int, int]]]:
    distance, path, _ = solve_maze(grid)
    return distance, path


def generate_random_maze(size: int, key_count: int, seed: int | None = None) -> list[list[str]]:
    if not isinstance(size, int):
        raise ValueError("Maze size must be an integer.")
    if size < 2:
        raise ValueError("Maze size must be at least 2x2.")
    if not 1 <= key_count <= 6:
        raise ValueError("Number of key-door pairs must be between 1 and 6.")
    if key_count > len(VALID_KEY_DOOR_PAIRS):
        raise ValueError(f"The exit uses 'E', so the maze supports at most {len(VALID_KEY_DOOR_PAIRS)} distinct key-door pairs.")

    required_min_size = max(5, key_count + 3)
    if size < required_min_size:
        raise ValueError(f"For T={key_count}, choose N >= {required_min_size}.")

    rng = random.Random(seed)
    grid = [["#" for _ in range(size)] for _ in range(size)]

    route: list[Tuple[int, int]] = [(1, 1)]
    for row in range(1, size - 1):
        if row % 2 == 1:
            cols = range(1, size - 1)
        else:
            cols = range(size - 2, 0, -1)
        for col in cols:
            if (row, col) == (1, 1):
                continue
            route.append((row, col))
    if route[-1] != (size - 2, size - 2):
        route.append((size - 2, size - 2))

    for r, c in route:
        grid[r][c] = "."
    grid[1][1] = "S"
    grid[size - 2][size - 2] = "E"

    corridor = route[1:-1]
    if len(corridor) < 2 * key_count:
        raise ValueError("The generated corridor is too short to place the requested key-door pairs.")

    selected_pairs = VALID_KEY_DOOR_PAIRS[:key_count]
    key_letters = [pair[0] for pair in selected_pairs]
    door_letters = [pair[1] for pair in selected_pairs]
    for index in range(key_count):
        key_r, key_c = corridor[2 * index]
        door_r, door_c = corridor[2 * index + 1]
        grid[key_r][key_c] = key_letters[index]
        grid[door_r][door_c] = door_letters[index]

    for r in range(size):
        for c in range(size):
            if (r, c) in route:
                continue
            if r in (0, size - 1) or c in (0, size - 1):
                continue
            if rng.random() < 0.35:
                grid[r][c] = "."

    # Guarantee the path remains valid after randomization.
    distance, _, _ = solve_maze(grid)
    if distance < 0:
        raise ValueError("Maze generation failed validation; try a different size or key count.")
    return grid


def export_path_csv(grid: Sequence[Sequence[str]], path: Iterable[Tuple[int, int, int]], filename: str | Path) -> None:
    output = [list(row) for row in grid]
    for row, col, _ in path:
        if output[row][col] == ".":
            output[row][col] = "x"
    path_obj = Path(filename)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    with open(path_obj, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerows(output)
