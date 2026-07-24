from typing import Optional, Union


class Zone:
    """
    Represents an isolated location on the map.
    It holds data about its position and rules, but knows nothing
    about which other zones it connects to.
    """
    def __init__(
        self,
        name: str,
        x: int,
        y: int,
        zone_type: str = "normal",
        color: Optional[str] = None,
        max_drones: int = 1,
    ) -> None:
        self.name: str = name
        self.x: int = x
        self.y: int = y
        self.type: str = zone_type
        self.color: Union[str, None] = color
        self.max_drones: int = max_drones
        self.curr_drones: int = 0


class Connection:
    """
    Represents a road between two Zones.
    It knows the names of the two zones it links and how many drones
    can travel on it at once.
    """
    def __init__(
        self, name1: str, name2: str, max_capacity: int = 1
    ) -> None:
        self.zone_1: str = name1
        self.zone_2: str = name2
        self.max_capacity: int = max_capacity


class Graph:
    """
    Manages the overall structure of the map.
    - zone_dict: A dictionary mapping zone names to their
                 corresponding Zone objects.
    - connection_dict: You give it a zone name, and it gives
                       you a list of all Connections touching
                       that zone.
    """
    def __init__(self) -> None:
        self.zone_dict: dict[str, Zone] = {}
        self.connection_dict: dict[str, list[Connection]] = {}
        self.nb_drones: int = 0
        self.start_hub: Optional[Zone] = None
        self.end_hub: Optional[Zone] = None
        self.all_paths: list[list[str]] = []

    def add_zone(self, zone_object: Zone) -> None:
        self.zone_dict[zone_object.name] = zone_object

    def add_connection(
        self, connection_object: Connection
    ) -> None:
        if connection_object.zone_1 not in self.connection_dict:
            self.connection_dict[connection_object.zone_1] = []
        if connection_object.zone_2 not in self.connection_dict:
            self.connection_dict[connection_object.zone_2] = []

        self.connection_dict[
            connection_object.zone_1
        ].append(connection_object)
        self.connection_dict[
            connection_object.zone_2
        ].append(connection_object)

    def weighted_shortest_path(
        self,
        start_zone: str,
        end_zone: str,
        cost_overrides: Optional[dict[str, int]] = None
    ) -> Optional[list[str]]:
        """
        Dijkstra shortest path with optional cost overrides.
        cost_overrides: dict mapping zone_name -> custom cost.
        If a zone is in cost_overrides, that cost is used
        instead of zone_cost().
        """
        if cost_overrides is None:
            cost_overrides = {}
        queue: list[tuple[int, list[str]]] = [
            (0, [start_zone])
        ]
        # Initialize best known costs to reach each zone
        best_costs: dict[str, int] = {start_zone: 0}

        # Loop while there are paths left to explore
        # in the queue
        while queue:
            # Sort the queue so we always process the
            # lowest-cost path first
            queue.sort(key=lambda item: item[0])
            curr_cost, curr_path = queue.pop(0)
            curr_zone = curr_path[-1]

            if curr_zone == end_zone:
                return curr_path

            # Retrieve all connection lines touching
            # the current zone
            curr_connections = self.connection_dict.get(
                curr_zone, []
            )

            # Iterate through each connection to explore
            # neighboring zones
            for connec in curr_connections:
                if connec.zone_1 == curr_zone:
                    neighbor = connec.zone_2
                else:
                    neighbor = connec.zone_1

                # Skip this neighbor if the zone is blocked
                neighbor_zone = self.zone_dict[neighbor]
                if neighbor_zone.type == "blocked":
                    continue

                # Use the override cost if available,
                # otherwise get the normal zone cost
                step_cost = cost_overrides.get(
                    neighbor, self.zone_cost(neighbor)
                )
                # Calculate the new total cost to reach
                # this neighbor
                new_cost = curr_cost + step_cost

                # If this is a cheaper path to the neighbor,
                # record it and add to queue
                if (
                    neighbor not in best_costs
                    or new_cost < best_costs[neighbor]
                ):
                    best_costs[neighbor] = new_cost
                    new_path = list(curr_path)
                    new_path.append(neighbor)
                    queue.append((new_cost, new_path))

        # Return None if no path to the destination
        # could be found
        return None

    def find_multiple_paths(
        self, start_zone: str, end_zone: str
    ) -> None:
        """
        1. Find the cheapest path with normal costs.
        2. Double the cost of every zone on that path.
        3. Find a second cheapest path (Dijkstra avoids
           the expensive first path).
        4. Keep both paths (if the second one is different).
        """
        self.all_paths = []

        # first shortest path with normal costs
        first_path = self.weighted_shortest_path(
            start_zone, end_zone
        )
        if first_path is None:
            return
        self.all_paths.append(first_path)

        # penalize the cost of zones on the
        # first path heavily
        cost_overrides: dict[str, int] = {}
        for zone_name in first_path:
            cost_overrides[zone_name] = (
                self.zone_cost(zone_name) * 2
            )

        # find second path with inflated costs
        second_path = self.weighted_shortest_path(
            start_zone, end_zone, cost_overrides
        )

        # Only add if it's actually different from the first
        if (
            second_path is not None
            and second_path != first_path
        ):
            self.all_paths.append(second_path)

    def zone_cost(self, zone_name: str) -> int:
        zone = self.zone_dict[zone_name]

        if zone.type == "restricted":
            return 2000
        elif zone.type == "normal":
            return 1000
        elif zone.type == "priority":
            return 500
        return 0


class Drone:
    """
    Represents a single drone in the simulation.
    Tracks its id, current zone, and in-transit state
    when crossing a restricted zone over multiple turns.
    """
    def __init__(
        self,
        drone_id: int,
        current_zone: Zone,
        in_trans: Optional[Connection] = None,
        turns_remaining: int = 0,
    ) -> None:
        self.drone_id: int = drone_id
        self.current_zone: Zone = current_zone

        # Is this drone currently on a connection
        # instead of inside a zone?
        self.in_trans: Optional[Connection] = in_trans

        self.turns_remaining: int = turns_remaining
        self.path: list[str] = []
        self.path_index: int = 0
