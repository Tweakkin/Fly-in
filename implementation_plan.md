# Fly-in Project — Complete Subject Analysis

Full line-by-line audit of every subject requirement vs. your current implementation.

---

## ✅ Summary of Performance Benchmarks

Your algorithm performance is **excellent** — you meet or beat every single target:

| Map | Target | Your Result | Status |
|-----|--------|-------------|--------|
| Easy 1 — Linear path (2 drones) | ≤ 6 | **4** | ✅ |
| Easy 2 — Simple fork (4 drones) | ≤ 8 | **4** | ✅ |
| Easy 3 — Basic capacity (4 drones) | ≤ 6 | **4** | ✅ |
| Medium 1 — Dead end trap (5 drones) | ≤ 12 | **8** | ✅ |
| Medium 2 — Circular loop (6 drones) | ≤ 15 | **15** | ✅ |
| Medium 3 — Priority puzzle (5 drones) | ≤ 12 | **9** | ✅ |
| Hard 1 — Maze nightmare (8 drones) | ≤ 30 | **13** | ✅ |
| Hard 2 — Capacity hell (12 drones) | ≤ 35 | **16** | ✅ |
| Hard 3 — Ultimate challenge (15 drones) | ≤ 45 | **27** | ✅ |
| Challenger — Impossible dream (25 drones) | ≤ 45 | **45** | ✅ 🏆 |

---

## 🔴 CRITICAL — Unhandled Crash (Program crashes = "non-functional" per subject)

> [!CAUTION]
> **Crash: No path found between start and end → `ZeroDivisionError`**
> When a map has no valid path (e.g., only blocked zones connect start to end, or no connections exist), your program prints `"These are the paths i found: []"` then crashes with an unhandled `ZeroDivisionError: integer modulo by zero` in [simulation.py:20](file:///home/yboukhmi/Desktop/flyin/simulation.py#L20).
>
> The subject states: *"If your program crashes due to unhandled exceptions during the review, it will be considered non-functional."*

**Root cause**: [find_multiple_paths()](file:///home/yboukhmi/Desktop/flyin/models.py#L209) sets `self.all_paths = []` when no path is found. The `Simulation.__init__` checks `if self.all_paths is None` but `[]` is not `None`. Then `create_drones()` does `(i + 1) % nb_paths` where `nb_paths = 0`.

**Fix needed**: Check `if not self.all_paths` instead of `if self.all_paths is None`, or raise a proper error and catch it.

---

## 🔴 CRITICAL — Missing Required Files

> [!CAUTION]
> The following **mandatory** files are completely missing from your project:

### 1. `Makefile` — **MISSING** (Mandatory, Chapter III.2)
The subject requires a Makefile with these rules:
- `install` — Install project dependencies
- `run` — Execute the main script
- `debug` — Run with Python's built-in debugger (pdb)
- `clean` — Remove `__pycache__`, `.mypy_cache`, etc.
- `lint` — Run `flake8 .` and `mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs`
- `lint-strict` (optional) — Run `flake8 .` and `mypy . --strict`

### 2. `README.md` — **MISSING** (Mandatory, Chapter VIII)
Must include:
- First line: *This project has been created as part of the 42 curriculum by \<login\>.*
- "Description" section
- "Instructions" section (compilation, installation, execution)
- "Resources" section (references + AI usage description)
- Algorithm choices and implementation strategy
- Documentation of visual representation features

### 3. `.gitignore` — **MISSING** (Chapter III.3)
Must exclude Python artifacts (`__pycache__`, `.mypy_cache`, `*.pyc`, etc.)

---

## 🔴 CRITICAL — Flake8 Violations (Mandatory compliance)

> [!WARNING]
> Subject: *"Your project must adhere to the flake8 coding standard."*
> Currently: **100+ flake8 errors** across all 3 main files.

### Key violation categories:

| Category | Count | Examples |
|----------|-------|---------|
| `E501` Line too long (>79 chars) | ~50+ | Throughout all files |
| `W293` Blank line with whitespace | ~10 | Various |
| `W291` Trailing whitespace | ~5 | Various |
| `E302` Expected 2 blank lines | ~5 | Between top-level classes |
| `E303` Too many blank lines | ~5 | Inside functions |
| `F401` Unused imports | 2 | `contextlib` in models.py, `Optional` in simulation.py |
| `E712` Comparison to True | 1 | `simulation.py:124` — `if all_arrived == True` → should be `if all_arrived:` |
| `E203` Whitespace before `:` | 1 | `models.py:183` |
| `W292` No newline at end of file | 1 | `simulation.py:131` |

---

## 🔴 CRITICAL — Mypy Type Errors (Mandatory compliance)

> [!WARNING]
> Subject: *"All functions must pass mypy without errors."* using flags: `--warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs`
> Currently: **13 mypy errors** in models.py and simulation.py.

### Errors:

| File | Error | Issue |
|------|-------|-------|
| [models.py:209](file:///home/yboukhmi/Desktop/flyin/models.py#L209) | `no-untyped-def` | `find_multiple_paths()` missing return type annotation |
| [simulation.py:9](file:///home/yboukhmi/Desktop/flyin/simulation.py#L9) | `union-attr` | `graph.start_hub` could be `None` — not narrowed |
| [simulation.py:15](file:///home/yboukhmi/Desktop/flyin/simulation.py#L15) | `no-untyped-def` | `create_drones()` missing return type annotation |
| [simulation.py:19](file:///home/yboukhmi/Desktop/flyin/simulation.py#L19) | `arg-type` | `start_hub` is `Zone | None` but `Drone()` expects `Zone` |
| [simulation.py:24](file:///home/yboukhmi/Desktop/flyin/simulation.py#L24) | `no-untyped-def` | `run()` missing return type annotation |
| [simulation.py:30](file:///home/yboukhmi/Desktop/flyin/simulation.py#L30) | `misc`/`union-attr` | Declaring type on non-self attribute; `start_hub` could be None |
| [simulation.py:82](file:///home/yboukhmi/Desktop/flyin/simulation.py#L82) | `arg-type` | `active_conn` could be `None` |
| [simulation.py:83](file:///home/yboukhmi/Desktop/flyin/simulation.py#L83) | `union-attr` | `active_conn` could be `None` |
| [simulation.py:89](file:///home/yboukhmi/Desktop/flyin/simulation.py#L89) | `union-attr` | `end_hub` could be `None` |
| [simulation.py:93](file:///home/yboukhmi/Desktop/flyin/simulation.py#L93) | `index` | Dict index with `Connection | None` |
| [simulation.py:108](file:///home/yboukhmi/Desktop/flyin/simulation.py#L108) | `union-attr` ×2 | `active_conn` could be `None` |

---

## 🟡 MEDIUM — Missing Docstrings (PEP 257)

> [!IMPORTANT]
> Subject: *"Include docstrings in functions and classes following PEP 257 to document purpose, parameters, and returns."*

### Functions missing docstrings:

| File | Function/Method |
|------|----------------|
| [models.py:50](file:///home/yboukhmi/Desktop/flyin/models.py#L50) | `Graph.add_zone()` |
| [models.py:53](file:///home/yboukhmi/Desktop/flyin/models.py#L53) | `Graph.add_connection()` |
| [models.py:239](file:///home/yboukhmi/Desktop/flyin/models.py#L239) | `Graph.zone_cost()` |
| [simulation.py:15](file:///home/yboukhmi/Desktop/flyin/simulation.py#L15) | `Simulation.create_drones()` — has a comment but not a proper docstring |

> [!NOTE]
> Several methods use inline `""" ... """` comments mid-function (e.g., throughout `simulation.py`). While not harmful, these are unconventional — proper docstrings go at the start of the function, and inline explanations should use `#` comments.

---

## 🟡 MEDIUM — Parser Error Messages Missing Line Numbers

> [!IMPORTANT]
> Subject: *"Any parsing error must stop the program and return a clear error message indicating the line and cause."*

### Problem:
When `connection:` has a malformed zone reference (e.g., `connection: s` with no dash, or `connection: a-b-c` with extra dashes), the `ValueError` from `zone1, zone2 = core[1].split('-')` at [parser.py:97](file:///home/yboukhmi/Desktop/flyin/parser.py#L97) is caught by the generic handler at line 129, which prints:

```
Parsing Error: not enough values to unpack (expected 2, got 1)
```

This **doesn't include the line number** — violating the subject's requirement. You need a try-except around line 97 to provide a proper message like: `"Line X: Connection must have format <zone1>-<zone2>"`.

---

## 🟡 MEDIUM — Unused Import

| File | Import | Issue |
|------|--------|-------|
| [models.py:1](file:///home/yboukhmi/Desktop/flyin/models.py#L1) | `import contextlib` | Never used — flake8 `F401` |
| [simulation.py:2](file:///home/yboukhmi/Desktop/flyin/simulation.py#L2) | `from typing import Optional` | Never used — flake8 `F401` |

---

## 🟡 MEDIUM — `import contextlib` and Missing `__all__` 

The `import contextlib` in [models.py](file:///home/yboukhmi/Desktop/flyin/models.py#L1) serves no purpose. Remove it.

---

## 🟢 Simulation Output Format — **CORRECT ✅**

Subject requires:
- Each turn = one line ✅
- Format: `D<ID>-<zone>` or `D<ID>-<connection>` ✅
- Drones that don't move are omitted ✅
- Space-separated movements ✅
- Simulation ends when all drones reach end ✅
- Final line: `Total turn <N>` ✅

---

## 🟢 Zone Occupancy Rules — **CORRECT ✅**

- Default max 1 drone per zone ✅
- `max_drones=N` supported ✅
- Start zone: all drones share initially ✅ (see [simulation.py:30](file:///home/yboukhmi/Desktop/flyin/simulation.py#L30))
- End zone: unlimited arrivals ✅ (see [simulation.py:89](file:///home/yboukhmi/Desktop/flyin/simulation.py#L89))
- Capacity check before movement ✅

---

## 🟢 Movement & Turn Mechanics — **CORRECT ✅**

- Normal zones: 1 turn ✅
- Restricted zones: 2 turns (1 turn on connection + 1 turn arrive) ✅
- Blocked zones: inaccessible ✅ (BFS and Dijkstra skip them)
- Priority zones: 1 turn, preferred in pathfinding ✅ (lower cost in `zone_cost()`)
- Drones moving out free capacity same turn ✅
- Connection capacity (max_link_capacity) enforced ✅
- Restricted transit drones MUST arrive next turn ✅ (`turns_remaining = 1`)
- Drones can wait in place ✅

---

## 🟢 Pathfinding Algorithm — **CORRECT ✅**

- BFS for basic shortest path ✅
- Dijkstra with weighted costs ✅
- Multiple path discovery (penalty-based) ✅
- Drone distribution across paths ✅
- No forbidden graph libraries used ✅

---

## 🟢 Parser Validation — **MOSTLY CORRECT** (with caveats above)

- `nb_drones` must be first non-comment line ✅
- `nb_drones` positive integer ✅
- Negative rejected ✅
- Zero rejected ✅
- Duplicate `nb_drones` rejected ✅
- Exactly one `start_hub` and `end_hub` ✅
- Duplicate zone names rejected ✅
- Dashes in zone names rejected ✅
- Spaces in zone names rejected ✅
- Connections reference previously defined zones ✅
- Duplicate connections (including reverse) rejected ✅
- Self-connection rejected ✅
- Invalid zone types rejected ✅
- Invalid metadata keys rejected ✅
- `max_drones` must be positive integer ✅
- `max_link_capacity` must be positive integer ✅
- Nested brackets rejected ✅
- Missing closing bracket rejected ✅
- Content after bracket rejected ✅
- Comments handled (full-line `#` and inline) ✅
- Blank lines handled ✅
- File not found handled ✅
- Permission error handled ✅
- Usage message when no args ✅

---

## 🟢 Visual Representation — **PRESENT ✅**

- Tkinter visualizer ([visualizer.py](file:///home/yboukhmi/Desktop/flyin/visualizer.py)) ✅
- Pygame visualizer ([visualizer_pygame.py](file:///home/yboukhmi/Desktop/flyin/visualizer_pygame.py)) ✅
- Both display the network, zones, connections, drone movements ✅
- Animated drone movement ✅
- Zone types color-coded ✅
- Hubs visually distinguished ✅

---

## 🟢 Object-Oriented Design — **CORRECT ✅**

- `Zone`, `Connection`, `Graph`, `Drone` classes in [models.py](file:///home/yboukhmi/Desktop/flyin/models.py) ✅
- `Parser` class in [parser.py](file:///home/yboukhmi/Desktop/flyin/parser.py) ✅
- `Simulation` class in [simulation.py](file:///home/yboukhmi/Desktop/flyin/simulation.py) ✅

---

## 🟢 Python 3.10+ — **CORRECT ✅**

Uses modern type hints syntax (`dict[str, Zone]`, `list[str]`, `Optional[...]`) ✅

---

## Full Issues Checklist — Priority Order

| # | Severity | Issue | Fix Difficulty |
|---|----------|-------|---------------|
| 1 | 🔴 CRITICAL | **Crash on no-path maps** (ZeroDivisionError) | Easy — 3 lines |
| 2 | 🔴 CRITICAL | **Makefile missing** | Easy — create file |
| 3 | 🔴 CRITICAL | **README.md missing** | Medium — write docs |
| 4 | 🔴 CRITICAL | **.gitignore missing** | Easy — create file |
| 5 | 🔴 CRITICAL | **100+ flake8 errors** (line length, whitespace, etc.) | Medium — reformatting |
| 6 | 🔴 CRITICAL | **13 mypy errors** (missing type annotations, None checks) | Medium — type fixes |
| 7 | 🟡 MEDIUM | Parser error for malformed connections lacks line number | Easy — 5 lines |
| 8 | 🟡 MEDIUM | Missing docstrings on some methods | Easy — add docstrings |
| 9 | 🟡 MEDIUM | Unused imports (`contextlib`, `Optional`) | Trivial — delete |
| 10 | 🟡 LOW | Inline `"""` comments should be `#` comments | Cosmetic |

> [!IMPORTANT]
> Issues 1-6 are **mandatory requirements** that will cause you to fail peer review if not fixed. Issue 1 in particular is the most dangerous — a single crash during evaluation = "non-functional" per the subject.

## Open Questions

1. **Do you want me to fix all of these issues?** I can fix them all systematically.
2. **What is your 42 login** (needed for the README.md first line)?
3. **Do you want a `requirements.txt`** for the Makefile `install` target? (pygame is a dependency for the visualizer)
