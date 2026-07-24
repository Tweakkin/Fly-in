*This project has been created as part of the 42 curriculum by yboukhmi.*

# Fly-in

## Description

Fly-in is a drone traffic simulation written in Python. The goal is to move a group of drones from a start hub to an end hub across a network of zones and connections, while respecting capacity limits on both zones and connections. The program reads a map file that defines the layout, then simulates the movement turn by turn until all drones arrive at the destination.

## Instructions

### Requirements

- Python 3.10 or higher

### Installation

```bash
make install
```

This installs `flake8` and `mypy` for linting and type checking.

### Running

```bash
make run MAP=path/to/your/map.txt
```

Or directly:

```bash
python3 main.py path/to/your/map.txt
```

### Linting

```bash
make lint
```

### Cleaning

```bash
make clean
```

## Map File Format

A map file is a plain text file that defines the simulation layout. Lines starting with `#` are comments. The file must contain:

- `nb_drones: <number>` — must be the first non-comment line
- `start_hub: <name> <x> <y>` — the starting zone for all drones
- `end_hub: <name> <x> <y>` — the destination zone
- `hub: <name> <x> <y>` — intermediate zones
- `connection: <zone1>-<zone2>` — a link between two zones

Zones and connections can have optional metadata in brackets:

```
hub: myzone 3 4 [zone=restricted color=red max_drones=5]
connection: zoneA-zoneB [max_link_capacity=3]
```

Zone types: `normal`, `blocked`, `restricted`, `priority`.

## Algorithm Choices

### Pathfinding — Weighted Dijkstra

The program uses Dijkstra's shortest-path algorithm to find routes from start to end. Each zone type has a different cost:

- **priority** zones cost 500 (preferred)
- **normal** zones cost 1000
- **restricted** zones cost 2000 (avoided when possible)
- **blocked** zones are skipped entirely

### Multiple Path Discovery

To spread drones across different routes, the program finds a second path by doubling the cost of every zone on the first path. This pushes Dijkstra to pick a different route. If the second path is different from the first, both are kept. Drones are then split evenly across all available paths.

### Turn-by-Turn Simulation

Each turn, drones are sorted by progress (closest to finish moves first). A drone can only move if:

1. The connection it wants to use is not at full capacity
2. The destination zone is not at full capacity

When entering a **restricted** zone, the drone spends one turn in transit on the connection before arriving. This models a delay for restricted areas.

## Visual Representation

The simulation uses ANSI color codes to make the terminal output easy to read:

- Each turn is printed on one line, showing which drones moved and where
- Turn labels are colored in **cyan**
- Each drone movement is colored based on the destination zone's color (set in the map file)
- A **rainbow** color option cycles through multiple colors character by character
- The final total turns message is shown in **green** and **bold**

This makes it simple to follow each drone's progress at a glance and quickly spot bottlenecks or unusual movements.

## Resources

- [Dijkstra's Algorithm — Wikipedia](https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm)
- [ANSI Escape Codes — Wikipedia](https://en.wikipedia.org/wiki/ANSI_escape_code)
- [Python Documentation](https://docs.python.org/3/)

### AI Usage

AI was used as a coding assistant for debugging type errors, writing this README, and reviewing code structure. All algorithm logic, parsing, and simulation code was written manually.
