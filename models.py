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

    def add_zone(self, zone_object: Zone) -> None:
        self.zone_dict[zone_object.name] = zone_object

    def add_connection(self, connection_object: Connection) -> None:
        if connection_object.zone_1 not in self.connection_dict:
            self.connection_dict[connection_object.zone_1] = []
        if connection_object.zone_2 not in self.connection_dict:
            self.connection_dict[connection_object.zone_2] = []
            
        self.connection_dict[connection_object.zone_1].append(connection_object)
        self.connection_dict[connection_object.zone_2].append(connection_object)
