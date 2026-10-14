import csv

import pytest

from maze_lab.logic import generate_random_maze, read_grid_csv, shortest_path, solve_maze, validate_grid


def test_n_lt_2_is_invalid():
    with pytest.raises(ValueError):
        validate_grid([["S"]])


def test_start_adjacent_to_exit_has_distance_one():
    grid = [["S", "E"], [".", "."]]
    distance, path = shortest_path(grid)
    assert distance == 1
    assert len(path) == 2


def test_same_cell_with_different_key_mask_counts_as_distinct_state():
    grid = [
        ["S", "a", "A"],
        ["#", "#", "."],
        [".", ".", "E"],
    ]
    distance, _ = shortest_path(grid)
    assert distance == 4


def test_keys_are_collected_before_doors():
    grid = [
        ["S", "a", "A", "."],
        ["#", "#", "#", "."],
        ["#", "#", "#", "E"],
        ["#", "#", "#", "."],
    ]
    distance, _ = shortest_path(grid)
    assert distance == 5


def test_doors_block_movement_without_keys():
    grid = [
        ["S", ".", "A"],
        ["#", "#", "."],
        [".", "a", "E"],
    ]
    distance, _ = shortest_path(grid)
    assert distance == -1


def test_multiple_key_door_pairs_are_supported():
    grid = [
        ["S", "a", "A", "b", "B", "E"],
        ["#", "#", "#", "#", "#", "#"],
        ["#", "#", "#", "#", "#", "#"],
        ["#", "#", "#", "#", "#", "#"],
        ["#", "#", "#", "#", "#", "#"],
        ["#", "#", "#", "#", "#", "#"],
    ]
    distance, _ = shortest_path(grid)
    assert distance == 5


def test_unsolvable_maze_returns_minus_one():
    grid = [
        ["S", "#", "E"],
        ["#", "#", "#"],
        ["#", "#", "#"],
    ]
    distance, _ = shortest_path(grid)
    assert distance == -1


def test_invalid_csv_dimensions_raise_error(tmp_path):
    csv_path = tmp_path / "invalid.csv"
    csv_path.write_text("S,.,.\n#,#,E\n", encoding="utf-8")
    with pytest.raises(ValueError):
        read_grid_csv(csv_path)


def test_exactly_one_start_and_exit_are_required():
    grid = [["S", "E", "E"], [".", ".", "."], [".", ".", "."]]
    with pytest.raises(ValueError):
        validate_grid(grid)


def test_generated_mazes_are_always_solvable():
    for size in range(5, 21):
        max_pairs = min(5, size - 3)
        for key_count in range(1, max_pairs + 1):
            grid = generate_random_maze(size, key_count, seed=size * 17 + key_count)
            distance, _, _ = solve_maze(grid)
            assert distance >= 0, f"Generated maze for size={size}, keys={key_count} was unsolvable"


def test_csv_round_trip_export(tmp_path):
    grid = [
        ["S", ".", ".", "."],
        ["#", "a", ".", "."],
        ["#", "A", ".", "E"],
        ["#", "#", ".", "."],
    ]
    csv_path = tmp_path / "maze.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerows(grid)

    loaded = read_grid_csv(csv_path)
    distance, path = shortest_path(loaded)
    assert distance >= 0

    solution_path = tmp_path / "solution.csv"
    with open(solution_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerows([[cell for cell in row] for row in loaded])

    assert solution_path.exists()
    loaded_solution = read_grid_csv(solution_path)
    assert len(loaded_solution) == len(loaded)
    assert all(len(row) == len(loaded) for row in loaded_solution)
