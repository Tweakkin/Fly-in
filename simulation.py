from models import Graph, Drone, Connection
from typing import Optional
import sys

# ANSI color codes for terminal output
COLORS = {
    "red": "\033[91m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "blue": "\033[94m",
    "magenta": "\033[95m",
    "cyan": "\033[96m",
    "orange": "\033[38;5;208m",
    "gray": "\033[90m",
    "white": "\033[97m",
    "purple": "\033[38;5;129m",
    "brown": "\033[38;5;130m",
    "black": "\033[38;5;240m",
    "crimson": "\033[38;5;196m",
    "darkred": "\033[38;5;52m",
    "gold": "\033[38;5;220m",
    "lime": "\033[38;5;118m",
    "maroon": "\033[38;5;88m",
    "violet": "\033[38;5;135m",
    "rainbow": "\033[38;5;199m",
}
RESET = "\033[0m"
BOLD = "\033[1m"


def colorize(text: str, color_name: Optional[str]) -> str:
    """Wrap text in ANSI color codes if a color is provided."""
    if not color_name:
        return text
    code = COLORS.get(color_name.lower(), "")
    if code:
        return f"{code}{text}{RESET}"
    return text


class Simulation:
    def __init__(self, graph: Graph) -> None:
        self.graph: Graph = graph
        self.drones: list[Drone] = []
        self.turns: int = 0
        assert graph.start_hub is not None
        assert graph.end_hub is not None
        graph.find_multiple_paths(
            graph.start_hub.name, graph.end_hub.name
        )
        self.all_paths = self.graph.all_paths
        if self.all_paths is None:
            print("No valid path exists between start and end!")
            sys.exit(1)

    def create_drones(self) -> None:
        """Create drones and divide them equally
        across the available paths."""
        nb_paths = len(self.all_paths)
        for i in range(self.graph.nb_drones):
            assert self.graph.start_hub is not None
            new_drone = Drone(i, self.graph.start_hub)
            new_drone.path = self.all_paths[(i + 1) % nb_paths]
            self.drones.append(new_drone)

    def run(self) -> None:
        """
        Keep looping as long as there is at least one
        drone that hasn't reached the end_hub
        """
        assert self.graph.start_hub is not None
        assert self.graph.end_hub is not None
        # Initialize the starting hub with all drones
        self.graph.start_hub.curr_drones = self.graph.nb_drones

        # Begin the main simulation loop
        while True:
            # Track all valid movements this turn
            turn_movements: list[str] = []
            # Assume all drones finished until proven otherwise
            all_arrived: bool = True

            # Track drones flying on each connection
            conn_usage: dict[Connection, int] = {}

            # Sort drones so closest to finish move first
            self.drones.sort(
                key=lambda d: d.path_index, reverse=True
            )

            # Evaluate each drone to see if it can move
            for drone in self.drones:

                # Handle drones mid-flight to restricted zone
                if drone.in_trans is not None:
                    # Tick down the remaining flight time
                    drone.turns_remaining -= 1
                    # If zero, the drone lands in restricted zone
                    if drone.turns_remaining == 0:
                        drone.path_index += 1
                        zone = self.graph.zone_dict[
                            drone.path[drone.path_index]
                        ]
                        drone.current_zone = zone
                        drone.in_trans = None
                        turn_movements.append(
                            colorize(
                                f"D{drone.drone_id}"
                                f"-{drone.current_zone.name}",
                                drone.current_zone.color,
                            )
                        )
                    # This drone is still busy
                    all_arrived = False
                    continue

                # Skip if already at final destination
                if (drone.path_index == len(drone.path) - 1):
                    continue

                # Drone hasn't finished, keep sim running
                all_arrived = False

                # Identify current location and next target
                curr_zone = drone.path[drone.path_index]
                next_zone = drone.path[drone.path_index + 1]

                # Find the Connection linking these two zones
                active_conn = None
                for conn in self.graph.connection_dict[
                    curr_zone
                ]:
                    if (conn.zone_1 == next_zone
                            or conn.zone_2 == next_zone):
                        active_conn = conn
                        break

                if active_conn is None:
                    continue

                # Check if connection is maxed out
                current_traffic = conn_usage.get(
                    active_conn, 0
                )
                if current_traffic >= active_conn.max_capacity:
                    continue

                # Check if destination zone is full
                # (except the final end hub)
                curr_drones = (
                    self.graph.zone_dict[next_zone].curr_drones
                )
                max_drones = (
                    self.graph.zone_dict[next_zone].max_drones
                )
                end_hub_name = self.graph.end_hub.name
                if (curr_drones >= max_drones
                        and next_zone != end_hub_name):
                    continue

                # Drone passes checks, let it move
                conn_usage[active_conn] = current_traffic + 1

                # Get the target zone object
                next_zone_object = (
                    self.graph.zone_dict[next_zone]
                )

                # Handle movement to a restricted zone
                if next_zone_object.type == "restricted":
                    # Remove drone from current zone
                    path_zone = drone.path[drone.path_index]
                    self.graph.zone_dict[
                        path_zone
                    ].curr_drones -= 1
                    # Mark as in-transit with 1-turn wait
                    drone.in_trans = active_conn
                    drone.turns_remaining = 1
                    # Reserve space in destination zone
                    self.graph.zone_dict[
                        next_zone
                    ].curr_drones += 1
                    # Log the movement for terminal output
                    conn_name = (
                        f"{active_conn.zone_1}"
                        f"-{active_conn.zone_2}"
                    )
                    turn_movements.append(
                        colorize(
                            f"D{drone.drone_id}-{conn_name}",
                            next_zone_object.color,
                        )
                    )

                else:
                    # Handle standard movement
                    # Remove drone from current zone
                    path_zone = drone.path[drone.path_index]
                    self.graph.zone_dict[
                        path_zone
                    ].curr_drones -= 1
                    # Advance path index and update zone
                    drone.path_index += 1
                    zone = self.graph.zone_dict[
                        drone.path[drone.path_index]
                    ]
                    drone.current_zone = zone
                    # Occupy space in new zone
                    path_zone = drone.path[drone.path_index]
                    self.graph.zone_dict[
                        path_zone
                    ].curr_drones += 1
                    # Log the arrival for terminal output
                    turn_movements.append(
                        colorize(
                            f"D{drone.drone_id}"
                            f"-{drone.current_zone.name}",
                            drone.current_zone.color,
                        )
                    )

            # If every drone is at end_hub, print and stop
            if all_arrived:
                total_msg = colorize(
                    f'Total turn {self.turns}', 'green'
                )
                print(f"{BOLD}{total_msg}{RESET}")
                break
            else:
                # Increment turn counter
                self.turns += 1
                # Print movements for this turn
                turn_label = colorize(
                    f"T{self.turns}", "cyan"
                )
                movements = ' '.join(turn_movements)
                print(f"{turn_label} {movements}")
