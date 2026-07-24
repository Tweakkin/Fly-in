from models import Graph, Drone, Connection, Zone
from typing import Optional
import sys

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
}
RESET = "\033[0m"
BOLD = "\033[1m"


def colorize(text: str, color_name: Optional[str]) -> str:
    """Wrap text in ANSI color codes if a color is provided."""
    if not color_name:
        return text
    if color_name.lower() == "rainbow":
        rainbow_codes = [
            "\033[91m", "\033[93m", "\033[92m",
            "\033[96m", "\033[94m", "\033[95m",
        ]
        result = ""
        for i, char in enumerate(text):
            result += f"{rainbow_codes[i % len(rainbow_codes)]}{char}"
        return result + RESET
    code = COLORS.get(color_name.lower(), "")
    if code:
        return f"{code}{text}{RESET}"
    return text


class Simulation:
    def __init__(self, graph: Graph) -> None:
        self.graph: Graph = graph
        self.drones: list[Drone] = []
        self.turns: int = 0
        if graph.start_hub is None:
            print("Error: start_hub was not defined in the map file!")
            sys.exit()
        if graph.end_hub is None:
            print("Error: end_hub was not defined in the map file!")
            sys.exit()
        self.start_hub: Zone = graph.start_hub
        self.end_hub: Zone = graph.end_hub
        graph.find_multiple_paths(
            self.start_hub.name, self.end_hub.name
        )
        self.all_paths = self.graph.all_paths
        if len(self.all_paths) == 0:
            print("No valid path exists between start and end!")
            sys.exit()

    def create_drones(self) -> None:
        """Create drones and divide them equally
        across the available paths."""
        nb_paths = len(self.all_paths)
        for i in range(self.graph.nb_drones):
            new_drone = Drone(i, self.start_hub)
            new_drone.path = self.all_paths[i % nb_paths]
            self.drones.append(new_drone)

    def run(self) -> None:
        """
        Keep looping as long as there is at least one
        drone that hasn't reached the end_hub
        """

        """ Initialize the starting hub with all drones """
        if self.start_hub.max_drones >= self.graph.nb_drones:
            self.start_hub.curr_drones = self.graph.nb_drones
        else:
            print("Error: nb_drones is higher than start_hub max drones!")
            sys.exit()

        """For each drone sorted by progress, closest-to-finish first"""
        while True:
            """ Save all movements that happened this turn """
            turn_movements: list[str] = []

            """ Assume all drones finished until proven otherwise """
            all_arrived: bool = True

            """ Track connections capacity """
            conn_usage: dict[Connection, int] = {}

            """ Sort drones so closest to finish move first """
            self.drones.sort(
                key=lambda d: d.path_index, reverse=True
            )

            """ Evaluate each drone """
            for drone in self.drones:

                """ Start by handling mid-flight drones """
                if drone.in_trans is not None:
                    drone.turns_remaining -= 1
                    """ if 0, it has reached the restricted zone """
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
                    """ This drone is still busy """
                    all_arrived = False
                    continue

                """ Skip if already at end_hub """
                if (drone.path_index == len(drone.path) - 1):
                    continue

                """ Drone hasn't finished, keep sim running """
                all_arrived = False

                """ Identify current location and next target """
                curr_zone = drone.path[drone.path_index]
                next_zone = drone.path[drone.path_index + 1]

                """ Find the Connection linking these two zones """
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

                """ Skip if traffic is full """
                current_traffic = conn_usage.get(
                    active_conn, 0
                )
                if current_traffic >= active_conn.max_capacity:
                    continue

                """ Skip if zone is full """
                curr_drones = (
                    self.graph.zone_dict[next_zone].curr_drones
                )
                max_drones = (
                    self.graph.zone_dict[next_zone].max_drones
                )
                if curr_drones >= max_drones:
                    continue

                """ Survived both checks -> Drone can move """
                conn_usage[active_conn] = current_traffic + 1

                """ Get next Zone object """
                next_zone_object = (
                    self.graph.zone_dict[next_zone]
                )

                """ Handle moving to a restricted Zone """
                if next_zone_object.type == "restricted":
                    """ Remove drone from current zone """
                    path_zone = drone.path[drone.path_index]
                    self.graph.zone_dict[
                        path_zone
                    ].curr_drones -= 1

                    """ Mark as in-transit with 1-turn wait """
                    drone.in_trans = active_conn
                    drone.turns_remaining = 1

                    """ Reserve space in destination zone """
                    self.graph.zone_dict[
                        next_zone
                    ].curr_drones += 1

                    """ Log the movement for terminal output """
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
                    """ Handle moving to a normal Zone """

                    """ Remove drone from current zone """
                    path_zone = drone.path[drone.path_index]
                    self.graph.zone_dict[
                        path_zone
                    ].curr_drones -= 1

                    """ Advance path index and update Zone """
                    drone.path_index += 1
                    zone = self.graph.zone_dict[
                        drone.path[drone.path_index]
                    ]
                    drone.current_zone = zone

                    """ Occupy space in new zone """
                    path_zone = drone.path[drone.path_index]
                    self.graph.zone_dict[
                        path_zone
                    ].curr_drones += 1

                    """ Log the arrival for terminal output """
                    turn_movements.append(
                        colorize(
                            f"D{drone.drone_id}"
                            f"-{drone.current_zone.name}",
                            drone.current_zone.color,
                        )
                    )

            """ If no movement made -> All Drones arrived """
            if all_arrived:
                total_msg = colorize(
                    f'Total turn {self.turns}', 'green'
                )
                print(f"{BOLD}{total_msg}{RESET}")
                break
            else:
                """ Increment turn counter """
                self.turns += 1
                """ Print movement for this turn """
                turn_label = colorize(
                    f"T{self.turns}", "cyan"
                )
                movements = ' '.join(turn_movements)
                print(f"{turn_label} {movements}")
