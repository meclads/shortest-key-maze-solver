from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox

from .logic import (
    DOORS,
    KEYS,
    export_path_csv,
    generate_random_maze,
    read_grid_csv,
    shortest_path,
    solve_maze,
)

PAIR_COLORS = {
    "a": "#F9C74F",
    "b": "#4CC9F0",
    "c": "#A78BFA",
    "d": "#FB7185",
    "e": "#34D399",
    "f": "#F472B6",
}

KEY_BADGE_INVENTORY = {
    "a": "A",
    "b": "B",
    "c": "C",
    "d": "D",
    "e": "E",
    "f": "F",
}


class MazeLabApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("MazeLab — Maze with Keys & Doors")
        self.root.configure(bg="#0B1220")
        self.root.geometry("1200x760")
        self.root.minsize(980, 660)

        self.grid: list[list[str]] | None = None
        self.path: list[tuple[int, int, int]] = []
        self.distance = -1
        self.visited_states = 0
        self.animation_index = 0
        self.animation_running = False
        self.animation_job: str | None = None
        self.player_position: tuple[int, int] | None = None
        self.collected_keys: set[str] = set()
        self.unlocked_doors: set[str] = set()

        self.size_var = tk.StringVar(value="9")
        self.key_count_var = tk.StringVar(value="2")
        self.speed_var = tk.StringVar(value="380")

        self._build_main_layout()
        self._set_status("READY")
        self._update_inventory_status(set())
        self._update_stats()
        self.draw()

    def _build_main_layout(self) -> None:
        header = tk.Frame(self.root, bg="#0B1220", pady=18, padx=20)
        header.pack(fill="x")

        brand = tk.Label(header, text="MazeLab", font=("Segoe UI", 24, "bold"), fg="#5EEAD4", bg="#0B1220")
        brand.pack(anchor="w")
        title = tk.Label(header, text="Maze with Keys & Doors", font=("Segoe UI", 18, "bold"), fg="white", bg="#0B1220")
        title.pack(anchor="w")
        subtitle = tk.Label(header, text="Find the optimal route through a dynamic maze", font=("Segoe UI", 10), fg="#A6B5D0", bg="#0B1220")
        subtitle.pack(anchor="w")

        self.status_badge = tk.Label(header, text="READY", bg="#5EEAD4", fg="#0B1220", font=("Segoe UI", 9, "bold"), padx=12, pady=4)
        self.status_badge.pack(anchor="e", side="right", pady=(0, 20))

        controls = tk.Frame(self.root, bg="#111C2E", pady=12, padx=16)
        controls.pack(fill="x")

        size_group = tk.Frame(controls, bg="#111C2E")
        size_group.pack(side="left", padx=(0, 14))
        tk.Label(size_group, text="Grid size", bg="#111C2E", fg="#DCE7F7", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        size_box = tk.Spinbox(size_group, from_=2, to=25, textvariable=self.size_var, width=6, justify="center", font=("Segoe UI", 10))
        size_box.pack(anchor="w")

        key_group = tk.Frame(controls, bg="#111C2E")
        key_group.pack(side="left", padx=(0, 14))
        tk.Label(key_group, text="Key pairs", bg="#111C2E", fg="#DCE7F7", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        key_box = tk.Spinbox(key_group, from_=1, to=6, textvariable=self.key_count_var, width=6, justify="center", font=("Segoe UI", 10))
        key_box.pack(anchor="w")

        speed_group = tk.Frame(controls, bg="#111C2E")
        speed_group.pack(side="left", padx=(0, 14))
        tk.Label(speed_group, text="Speed (ms)", bg="#111C2E", fg="#DCE7F7", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        speed_box = tk.Spinbox(speed_group, from_=100, to=1500, textvariable=self.speed_var, width=7, justify="center", font=("Segoe UI", 10))
        speed_box.pack(anchor="w")

        action_buttons = [
            ("Load CSV", self.load_csv),
            ("Generate Maze", self.generate_maze),
            ("Find Shortest Path", self.find_shortest_path),
            ("Play / Pause", self.toggle_animation),
            ("Reset", self.reset_view),
            ("Export Path CSV", self.export_path),
        ]
        for text, command in action_buttons:
            button = tk.Button(controls, text=text, bg="#1C2945", fg="white", activebackground="#22355D", activeforeground="white", borderwidth=0, padx=12, pady=8, command=command, font=("Segoe UI", 10, "bold"))
            button.pack(side="left", padx=(0, 8))

        main = tk.Frame(self.root, bg="#0B1220", padx=20, pady=18)
        main.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(main, width=720, height=720, bg="#F4F8FF", highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True, padx=(0, 16))

        sidebar = tk.Frame(main, bg="#111C2E", width=280, padx=16, pady=16)
        sidebar.pack(side="right", fill="y")
        sidebar.pack_propagate(False)

        self.status_label = tk.Label(sidebar, text="Load a maze to begin.", bg="#111C2E", fg="#EAF2FF", justify="left", wraplength=230, font=("Segoe UI", 10), padx=4)
        self.status_label.pack(anchor="w", pady=(0, 18))

        stats_frame = tk.Frame(sidebar, bg="#111C2E")
        stats_frame.pack(fill="x", pady=(0, 18))
        tk.Label(stats_frame, text="Statistics", bg="#111C2E", fg="#9FB3CE", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 8))

        self.shortest_value = tk.Label(stats_frame, text="-", bg="#111C2E", fg="white", font=("Segoe UI", 12, "bold"), anchor="w")
        self.shortest_value.pack(anchor="w", pady=2)
        self.visited_value = tk.Label(stats_frame, text="-", bg="#111C2E", fg="white", font=("Segoe UI", 12, "bold"), anchor="w")
        self.visited_value.pack(anchor="w", pady=2)
        self.keys_value = tk.Label(stats_frame, text="-", bg="#111C2E", fg="white", font=("Segoe UI", 12, "bold"), anchor="w")
        self.keys_value.pack(anchor="w", pady=2)
        self.step_value = tk.Label(stats_frame, text="-", bg="#111C2E", fg="white", font=("Segoe UI", 12, "bold"), anchor="w")
        self.step_value.pack(anchor="w", pady=2)

        inventory_frame = tk.Frame(sidebar, bg="#111C2E")
        inventory_frame.pack(fill="x", pady=(12, 18))
        tk.Label(inventory_frame, text="Keys collected", bg="#111C2E", fg="#9FB3CE", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 8))
        self.inventory_labels: dict[str, tk.Label] = {}
        for key in KEYS:
            label = tk.Label(inventory_frame, text=f"{key.upper()} — not collected", bg="#111C2E", fg="#9FB3CE", anchor="w", justify="left", font=("Segoe UI", 9), width=16)
            label.pack(anchor="w", pady=1)
            self.inventory_labels[key] = label

        legend_frame = tk.Frame(sidebar, bg="#111C2E")
        legend_frame.pack(fill="x")
        tk.Label(legend_frame, text="Legend", bg="#111C2E", fg="#9FB3CE", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 8))
        for key, label_text in (
            ("S", "Start"),
            ("E", "Exit"),
            (".", "Open cell"),
            ("#", "Wall"),
            ("path", "Path"),
        ):
            row = tk.Frame(legend_frame, bg="#111C2E")
            row.pack(fill="x", pady=2)
            swatch = tk.Label(row, width=3, height=1, bg=self._legend_color(key), borderwidth=1, relief="solid")
            swatch.pack(side="left")
            tk.Label(row, text=label_text, bg="#111C2E", fg="#EAF2FF", font=("Segoe UI", 9)).pack(side="left", padx=(8, 0))

        for key in KEYS:
            row = tk.Frame(legend_frame, bg="#111C2E")
            row.pack(fill="x", pady=2)
            swatch = tk.Label(row, width=3, height=1, bg=PAIR_COLORS[key], borderwidth=1, relief="solid")
            swatch.pack(side="left")
            tk.Label(row, text=f"Key {key.upper()}", bg="#111C2E", fg="#EAF2FF", font=("Segoe UI", 9)).pack(side="left", padx=(8, 0))

    def _legend_color(self, symbol: str) -> str:
        if symbol == "S":
            return "#22C55E"
        if symbol == "E":
            return "#EF4444"
        if symbol == "#":
            return "#090F1A"
        if symbol == "path":
            return "#5EEAD4"
        return "#FFFFFF"

    def _set_status(self, state: str) -> None:
        state = state.upper()
        palette = {
            "READY": ("#5EEAD4", "#0B1220"),
            "SOLVING": ("#FBBF24", "#0B1220"),
            "SOLVED": ("#34D399", "#0B1220"),
            "NO PATH": ("#F87171", "#0B1220"),
        }
        bg, fg = palette.get(state, palette["READY"])
        self.status_badge.config(text=state, bg=bg, fg=fg)

    def load_csv(self) -> None:
        filename = filedialog.askopenfilename(title="Open maze CSV", filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if not filename:
            return
        try:
            self.grid = read_grid_csv(filename)
            self._reset_runtime_state()
            self._set_status("READY")
            self.status_label.config(text=f"Loaded maze from {filename}.")
            self._update_inventory_status(set())
            self.draw()
        except ValueError as exc:
            messagebox.showerror("Invalid CSV", str(exc))

    def generate_maze(self) -> None:
        try:
            size = int(self.size_var.get())
            key_count = int(self.key_count_var.get())
            self.grid = generate_random_maze(size, key_count)
            self._reset_runtime_state()
            self._set_status("READY")
            self.status_label.config(text=f"Generated a solvable {size}x{size} maze with {key_count} key pairs.")
            self._update_inventory_status(set())
            self.draw()
        except ValueError as exc:
            messagebox.showerror("Invalid maze generation", str(exc))

    def find_shortest_path(self) -> None:
        if self.grid is None:
            messagebox.showinfo("No maze loaded", "Load a CSV file or generate a maze first.")
            return
        try:
            self.distance, self.path, self.visited_states = solve_maze(self.grid)
        except ValueError as exc:
            messagebox.showerror("Invalid maze", str(exc))
            return

        self._cancel_animation()
        self.animation_index = 0
        self.player_position = None
        self.collected_keys = set()
        self.unlocked_doors = set()
        self._update_inventory_status(set())

        if self.distance < 0:
            self._set_status("NO PATH")
            self.status_label.config(text="No path found from the start to the exit.")
        else:
            self._set_status("SOLVED")
            self.status_label.config(text=f"Shortest path length: {self.distance} moves.")
        self._update_stats()
        self.draw()

    def toggle_animation(self) -> None:
        if self.grid is None:
            messagebox.showinfo("No maze loaded", "Load a CSV file or generate a maze first.")
            return
        if not self.path and self.distance < 0:
            self.find_shortest_path()
        if self.distance < 0 or not self.path:
            return

        self.animation_running = not self.animation_running
        if self.animation_running:
            self._set_status("SOLVING")
            self.status_label.config(text=f"Animating shortest path from start to exit ({self.distance} moves).")
            self._schedule_animation()
        else:
            self._cancel_animation()
            self._set_status("SOLVED")
            self.status_label.config(text=f"Animation paused at step {self.animation_index + 1}.")
            self.draw()

    def _schedule_animation(self) -> None:
        if not self.animation_running:
            return
        delay = max(80, int(self.speed_var.get()))
        self.animation_job = self.root.after(delay, self._advance_animation)

    def _advance_animation(self) -> None:
        if not self.animation_running:
            return
        if self.animation_index >= len(self.path):
            self.animation_running = False
            self.player_position = (self.path[-1][0], self.path[-1][1])
            self._set_status("SOLVED")
            self.status_label.config(text=f"Arrival complete. Shortest path length: {self.distance}.")
            self._update_stats()
            self.draw()
            return

        row, col, _ = self.path[self.animation_index]
        cell = self.grid[row][col]
        if cell in KEYS:
            self.collected_keys.add(cell)
            self.status_label.config(text=f"Collected key {cell.upper()} at ({row + 1}, {col + 1}).")
        elif cell in DOORS:
            self.unlocked_doors.add(cell.lower())
            self.status_label.config(text=f"Unlocked door {cell} at ({row + 1}, {col + 1}).")
        else:
            if cell == "E":
                self.status_label.config(text=f"Reached the exit at ({row + 1}, {col + 1}).")
            else:
                self.status_label.config(text=f"Step {self.animation_index + 1} of {self.distance}: ({row + 1}, {col + 1}).")

        self.player_position = (row, col)
        self.animation_index += 1
        self._update_inventory_status(self.collected_keys)
        self._update_stats()
        self.draw()
        self._schedule_animation()

    def _cancel_animation(self) -> None:
        self.animation_running = False
        if self.animation_job is not None:
            self.root.after_cancel(self.animation_job)
            self.animation_job = None

    def reset_view(self) -> None:
        self._cancel_animation()
        self.animation_index = 0
        self.player_position = None
        self.collected_keys = set()
        self.unlocked_doors = set()
        self.path = []
        self.distance = -1
        self.visited_states = 0
        self._update_inventory_status(set())
        self._set_status("READY")
        self.status_label.config(text="Maze reset. Load a CSV or generate a new maze.")
        self._update_stats()
        self.draw()

    def export_path(self) -> None:
        if self.grid is None:
            messagebox.showinfo("No maze loaded", "Load a CSV file or generate a maze first.")
            return
        if self.distance < 0 or not self.path:
            self.find_shortest_path()
        if self.distance < 0 or not self.path:
            messagebox.showwarning("No path", "There is no valid route to export.")
            return

        filename = filedialog.asksaveasfilename(
            title="Save solution CSV",
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
            initialfile="maze_solution.csv",
        )
        if not filename:
            return
        try:
            export_path_csv(self.grid, self.path, filename)
            messagebox.showinfo("Export complete", f"Shortest path CSV saved to:\n{filename}")
        except Exception as exc:  # pragma: no cover - GUI fallback
            messagebox.showerror("Export failed", str(exc))

    def _reset_runtime_state(self) -> None:
        self.path = []
        self.distance = -1
        self.visited_states = 0
        self.animation_index = 0
        self.player_position = None
        self.collected_keys = set()
        self.unlocked_doors = set()
        self._cancel_animation()

    def _update_inventory_status(self, keys: set[str]) -> None:
        for key in KEYS:
            label = self.inventory_labels[key]
            if key in keys:
                label.config(text=f"{key.upper()} — collected", fg="#5EEAD4", font=("Segoe UI", 9, "bold"))
            else:
                label.config(text=f"{key.upper()} — not collected", fg="#9FB3CE", font=("Segoe UI", 9))

    def _update_stats(self) -> None:
        self.shortest_value.config(text=f"Shortest path: {self.distance if self.distance >= 0 else '-'}")
        self.visited_value.config(text=f"Visited BFS states: {self.visited_states}")
        self.keys_value.config(text=f"Keys collected: {len(self.collected_keys)}")
        self.step_value.config(text=f"Current animation step: {self.animation_index}")

    def draw(self) -> None:
        self.canvas.delete("all")
        if self.grid is None:
            self.canvas.create_text(360, 300, text="Load a CSV or generate a maze to begin", fill="#64748B", font=("Segoe UI", 18))
            return

        size = len(self.grid)
        canvas_w = max(self.canvas.winfo_width(), 400)
        canvas_h = max(self.canvas.winfo_height(), 400)
        cell_size = max(18, min((canvas_w - 30) // size, (canvas_h - 30) // size))
        offset_x = max(10, (canvas_w - (cell_size * size)) // 2)
        offset_y = max(10, (canvas_h - (cell_size * size)) // 2)
        path_cells = {(r, c) for r, c, _ in self.path}

        for r, row in enumerate(self.grid):
            for c, value in enumerate(row):
                x1 = offset_x + c * cell_size
                y1 = offset_y + r * cell_size
                x2 = x1 + cell_size
                y2 = y1 + cell_size

                fill = "#FFFFFF"
                text = ""
                outline = "#E2E8F0"

                if value == "#":
                    fill = "#090F1A"
                    outline = "#090F1A"
                elif value == "S":
                    fill = "#22C55E"
                    text = "S"
                elif value == "E":
                    fill = "#EF4444"
                    text = "E"
                elif value in KEYS:
                    fill = PAIR_COLORS.get(value, "#FFFFFF")
                    text = value.upper()
                    if value in self.collected_keys:
                        fill = "#F0FDFA"
                        text = "" 
                elif value in DOORS:
                    fill = PAIR_COLORS.get(value.lower(), "#FFFFFF")
                    text = value
                    if value.lower() in self.unlocked_doors:
                        fill = "#F0FDFA"
                        text = "✓"

                if (r, c) in path_cells and value not in {"#", "S", "E"} and value not in KEYS and value not in DOORS:
                    fill = "#5EEAD4"
                    outline = "#2DD4BF"

                self.canvas.create_rectangle(x1, y1, x2, y2, fill=fill, outline=outline, width=1)
                if text:
                    self.canvas.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=text, fill="#0B1220" if value not in {"S", "E"} else "white", font=("Segoe UI", max(9, int(cell_size * 0.32)), "bold"))

        if self.player_position is not None:
            r, c = self.player_position
            x1 = offset_x + c * cell_size + cell_size * 0.18
            y1 = offset_y + r * cell_size + cell_size * 0.18
            x2 = offset_x + c * cell_size + cell_size * 0.82
            y2 = offset_y + r * cell_size + cell_size * 0.82
            self.canvas.create_oval(x1, y1, x2, y2, fill="#2563EB", outline="#E2E8F0", width=2)


def main() -> None:
    root = tk.Tk()
    app = MazeLabApp(root)
    root.mainloop()
