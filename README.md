*This project has been created as part of the 42 curriculum by yboukhmi.*

# Fly-in — Drone Fleet Routing Simulator

## Description

Fly-in is a drone fleet simulation system that efficiently routes multiple drones from a central start zone to a target end zone across a network of connected zones. The project reads a map file describing zones, connections, and constraints, then computes optimized paths and simulates the turn-by-turn movement of all drones while respecting:

- **Zone occupancy limits** (`max_drones`)
- **Connection capacity constraints** (`max_link_capacity`)
- **Zone types** with different movement costs: `normal` (1 turn), `restricted` (2 turns), `priority` (1 turn, preferred), and `blocked` (inaccessible)
- **Simultaneous drone movement** with conflict-free scheduling

The goal is to deliver all drones in the fewest possible simulation turns.

## Instructions

### Prerequisites

- Python 3.10 or later

### Installation

```bash
make install
```

### Running the Simulation

```bash
make run MAP=<path_to_map_file>
```

Or manually:

```bash
python3 main.py <path_to_map_file>
```

**Example:**

```bash
python3 main.py maps/maps/easy/01_linear_path.txt
```

**Output format** — each line represents one simulation turn:

```
D0-waypoint1
D0-waypoint2 D1-waypoint1
D0-goal D1-waypoint2
D1-goal
Total turn 4
```

### Debug Mode

```bash
make debug MAP=<path_to_map_file>
```

### Linting

```bash
make lint
```

### Cleaning

```bash
make clean
```

## Algorithm Choices and Implementation Strategy

### Architecture

The project follows an object-oriented design with clear separation of concerns:

| Module | Responsibility |
|--------|---------------|
| `models.py` | Data structures — `Zone`, `Connection`, `Graph`, `Drone` classes |
| `parser.py` | Input parsing with full validation and error reporting |
| `simulation.py` | Turn-based simulation engine with conflict resolution |

### Pathfinding

The routing algorithm uses a **two-phase approach**:

1. **Weighted Dijkstra** — Finds the shortest path from start to end, using zone-type-based costs:
   - `normal`: cost 1000
   - `priority`: cost 999 (slightly cheaper to encourage usage)
   - `restricted`: cost 2000 (discouraged due to 2-turn movement cost)
   - `blocked`: skipped entirely

2. **Penalty-based path diversification** — After finding the first path, all zones on that path have their costs doubled. A second Dijkstra run then naturally finds an alternative path that avoids the first one. This distributes drones across multiple routes, reducing bottlenecks.

Drones are assigned to paths in a round-robin fashion across the discovered routes.

### Simulation Engine

The simulation processes one turn at a time:

- **Priority scheduling**: Drones are sorted by `path_index` (descending), so drones closest to the destination move first. This creates a cascading effect where a frontmost drone vacates a zone, allowing the one behind it to advance in the same turn.
- **Connection capacity tracking**: A per-turn `conn_usage` dictionary ensures no connection exceeds its `max_link_capacity`.
- **Zone capacity enforcement**: Before moving into a zone, the simulation checks `curr_drones < max_drones` (with an exception for the end zone, which has unlimited capacity).
- **Restricted zone handling**: When a drone targets a restricted zone, it enters the connection for 1 turn, then arrives the next turn. The destination space is reserved immediately to prevent capacity violations, since drones on connections **must** arrive and cannot wait.

### Parser

The parser performs strict validation on every line:

- `nb_drones` must be the first non-comment line and a positive integer
- Exactly one `start_hub` and one `end_hub` must exist
- Zone names must be unique and cannot contain dashes or spaces
- Connections must reference previously defined zones
- Duplicate and self-connections are rejected
- All metadata keys and values are validated
- Any error stops execution with a clear message indicating the line number and cause

## Visual Representation

The simulation provides visual feedback through **colored terminal output**:

- **Turn labels** are color-coded for easy scanning
- **Drone movements** are displayed with zone-specific colors matching their `color` metadata
- **Final result** (total turns) is highlighted in bold green
- The turn-by-turn format makes it easy to trace each drone's journey and identify bottlenecks or waiting patterns

This terminal-based approach provides clear, immediate feedback without requiring any additional dependencies.

## Resources

### References

- [Dijkstra's Algorithm — Wikipedia](https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm) — Foundation for the weighted shortest path implementation
- [Breadth-First Search — Wikipedia](https://en.wikipedia.org/wiki/Breadth-first_search) — Used for basic shortest path discovery
- [Python `typing` module documentation](https://docs.python.org/3/library/typing.html) — Type hints and static typing
- [Pygame documentation](https://www.pygame.org/docs/) — Graphical visualizer implementation
- [Tkinter documentation](https://docs.python.org/3/library/tkinter.html) — Lightweight visualizer implementation
- [PEP 257 — Docstring Conventions](https://peps.python.org/pep-0257/) — Documentation style guide

### AI Usage

AI tools were used during development for the following tasks:

- **Code review and debugging**: Identifying edge cases in parser validation and simulation logic
- **Documentation**: Assisting with docstring writing and README structure
- **Refactoring suggestions**: Improving code readability and type safety

All AI-generated content was reviewed, understood, and validated before integration. The core algorithm design, pathfinding strategy, and simulation logic were developed independently.
