import contextlib
from typing import Optional, Union

class Zone:
    """
    Represents an isolated location on the map.
    It holds data about its position and rules, but knows nothing
    about which other zones it connects to.
    """
    def __init__(self, name: str, x: int, y: int, zone_type: str = "normal", color: Optional[str] = None, max_drones: int = 1) -> None:
        self.name: str = name
        self.x: int = x
        self.y: int = y
        self.type: str = zone_type
        self.color: Union[str, None] = color
        self.max_drones: int = max_drones
        self.curr_drones: int = 0
    
    def __repr__(self) -> str:
        return f"{self.name}(type={self.type}, max={self.max_drones})"

class Connection:
    """
    Represents a road between two Zones. 
    It knows the names of the two zones it links and how many drones 
    can travel on it at once.
    """
    def __init__(self, name1: str, name2: str, max_capacity: int = 1) -> None:
        self.zone_1: str = name1
        self.zone_2: str = name2
        self.max_capacity: int = max_capacity
    
    def __repr__(self) -> str:
        return f"{self.zone_1}-{self.zone_2}(cap={self.max_capacity})"

class Graph:
    """
    Manages the overall structure of the map.
    - zone_dict: A dictionary mapping zone names to their corresponding Zone objects.
    - connection_dict: You give it a zone name, and it gives 
                       you a list of all Connections touching that zone.
    """
    def __init__(self) -> None:
        self.zone_dict: dict[str, Zone] = {}
        self.connection_dict: dict[str, list[Connection]] = {}
        self.nb_drones: int = 0
        self.start_hub: Optional[Zone] = None
        self.end_hub: Optional[Zone] = None

    def add_zone(self, zone_object: Zone) -> None:
        self.zone_dict[zone_object.name] = zone_object

    def add_connection(self, connection_object: Connection) -> None:
        if connection_object.zone_1 not in self.connection_dict:
            self.connection_dict[connection_object.zone_1] = []
        if connection_object.zone_2 not in self.connection_dict:
            self.connection_dict[connection_object.zone_2] = []
            
        self.connection_dict[connection_object.zone_1].append(connection_object)
        self.connection_dict[connection_object.zone_2].append(connection_object)


    def bfs_shortest_path(self, start_zone: str, end_zone: str) -> Optional[list[str]]:
        """
        Finds the shortest path between two zones using Breadth-First Search.
        How it works:
        1. Starts with a queue containing one path: just the start_zone.
        2. Pulls the first path from the queue and checks its last zone.
        3. If that zone is the destination, returns the path immediately.
        4. Otherwise, looks up all connections from that zone, finds each
           neighbor, and creates a new path (a copy + the neighbor) for
           each unvisited neighbor. Adds those new paths to the back of
           the queue.
        5. Repeats until the destination is found or the queue is empty.
        Returns the path as a list of zone name strings, or None if
        no path exists.
        """
        queue: list[list] = [[start_zone]]
        visited: set[str] = {start_zone}                
        
        while queue:
            curr_path = queue.pop(0)
            curr_zone = curr_path[-1]
            if curr_zone == end_zone:
                return curr_path
            curr_connections = self.connection_dict.get(curr_zone, [])
            for connec in curr_connections:
                if connec.zone_1 == curr_zone:
                    neighbor = connec.zone_2
                else:
                    neighbor = connec.zone_1

                neighbor_zone = self.zone_dict[neighbor]
                if neighbor_zone.type == "blocked":
                    continue

                if neighbor not in visited:
                    visited.add(neighbor)
                    new_path = list(curr_path)
                    new_path.append(neighbor)
                    queue.append(new_path)
        return None

    def weighted_shortest_path(
        self,
        start_zone: str,
        end_zone: str,
        ignored_zones: Optional[set[str]] = None
    ) -> Optional[list[str]]:
        if ignored_zones is None:
            ignored_zones = set()
        queue: list[tuple[int, list[str]]] = [(0, [start_zone])]
        best_costs: dict[str, int] = {start_zone: 0}

        while queue:
            queue.sort(key=lambda item: item[0])
            curr_cost, curr_path = queue.pop(0)
            curr_zone = curr_path[-1]

            if curr_zone == end_zone:
                return curr_path

            curr_connections = self.connection_dict.get(curr_zone, [])

            for connec in curr_connections:
                if connec.zone_1 == curr_zone:
                    neighbor = connec.zone_2
                else:
                    neighbor = connec.zone_1
                
                if neighbor in ignored_zones:
                    if (neighbor != start_zone) and (neighbor != end_zone):
                        continue

                neighbor_zone = self.zone_dict[neighbor]
                if neighbor_zone.type == "blocked":
                    continue

                new_cost = curr_cost + self.zone_cost(neighbor)

                if neighbor not in best_costs or new_cost < best_costs[neighbor]:
                    best_costs[neighbor] = new_cost

                    new_path = list(curr_path)
                    new_path.append(neighbor)

                    queue.append((new_cost, new_path))

        return None

    def find_multiple_paths(self, start_zone: str, end_zone: str):
        self.all_paths: Optional[list[list[str]]] = list()
        ignored_zones: Optional[set[str]] = set()
        while True:
            new_path = self.weighted_shortest_path(start_zone, end_zone, ignored_zones)
            if new_path == None:
                break
            for zone in new_path:
                ignored_zones.add(zone)
            self.all_paths.append(new_path)
        print(f"These are the paths i found: {self.all_paths}")


    def zone_cost(self, zone_name: str) -> int:
        zone = self.zone_dict[zone_name]

        if zone.type == "restricted":
            return 2
        return 1

class Drone:
    """
    Represents a single drone in the simulation.
    Tracks its id, current zone, and in-transit state
    when crossing a restricted zone over multiple turns.
    """
    def __init__(self, drone_id: int, current_zone: Zone, in_trans: Optional[Connection] = None,
                    turns_remaining: int = 0) -> None:
        self.drone_id: int = drone_id
        self.current_zone: Zone = current_zone

        # Is this drone currently on a connection instead of inside a zone?
        self.in_trans: Optional[Connection] = in_trans

        self.turns_remaining: int = turns_remaining
        self.path: list[str] = []
        self.path_index: int = 0
    
    def __repr__(self) -> str:
        return f"Drone({self.drone_id}, {self.current_zone})"
