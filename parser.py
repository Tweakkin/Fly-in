from models import Graph, Zone, Connection
from typing import Dict, List, Any
import sys

class Parser:
    """
    Reads a map text file and converts its raw strings into
    Zone and Connection objects, then stores them inside a Graph.
    Also validates every line for errors before accepting it.
    """
    def __init__(self) -> None:
        self.graph: Graph = Graph()
        self.seen_connections: list[tuple[str, str]] = []

    def parse_file(self, filepath: str) -> None:
        """
        Opens the map file, reads it line by line, and builds the Graph.
        Each line is identified by its prefix (nb_drones, hub, start_hub,
        end_hub, connection) and parsed accordingly. Metadata inside [...]
        brackets is extracted and validated. Raises and stops the program
        on any parsing error, printing the line number and cause.
        """
        try:
            with open(filepath, 'r') as file:
                line_number: int = 0
                for line in file:
                    line_number += 1
                    if line_number == 1 and not line.startswith("nb_drones:"):
                        raise ValueError(f"Line {line_number}: First line must define nb_drones!")
                    if line.strip().startswith("#"):
                        continue
                    if not line.strip():
                        continue
                    if line.startswith("nb_drones:"):
                        if self.graph.nb_drones > 0:
                            raise ValueError(f"Line {line_number}: 'nb_drones' cannot appear multiple times!")
                        try:
                            nb = int(line.split()[1].strip())
                        except ValueError:
                             raise ValueError(f"Line {line_number}: 'nb_drones' must be an integer")
                        if nb <= 0:
                            raise ValueError(f"Line {line_number}: 'nb_drones' should be a positive integer!")
                        self.graph.nb_drones = nb
                    elif line.startswith("hub:") or line.startswith("start_hub:") or line.startswith("end_hub:"):
                        core_part = line.split('[')[0] if '[' in line else line
                        core = core_part.strip().split()
                        try:
                            x, y = int(core[2]), int(core[3])
                        except ValueError:
                            raise ValueError(f"Line {line_number}: Coordinates must be integers")

                        if '[' in line:
                            token_str = line.strip().split('[')[1].replace("]", "")
                            data = Parser.metadata_validator(token_str, "zone", line_number)
                            zone = Zone(core[1], x, y, data['zone'], data['color'], data['max_drones'])
                        else:
                            zone = Zone(core[1], x, y)
                        if zone.name in self.graph.zone_dict.keys():
                            raise ValueError(f"Line {line_number}: Duplicate zone name: {zone.name}")
                        elif (" " in zone.name) or ('-' in zone.name):
                            raise ValueError(f"Line {line_number}: Zone names cannot contain dashes or spaces: {zone.name}")
                        self.graph.add_zone(zone)
                        if line.startswith("start_hub:"):
                            if self.graph.start_hub is not None:
                                raise ValueError(f"Line {line_number}: Duplicate 'start_hub' definition!")
                            self.graph.start_hub = zone
                        elif line.startswith("end_hub:"):
                            if self.graph.end_hub is not None:
                                raise ValueError(f"Line {line_number}: Duplicate 'end_hub' definition!")
                            self.graph.end_hub = zone

                    elif line.startswith("connection:"):
                        if '[' in line:
                            core_str, token_str = line.strip().split('[')
                            core = core_str.split()
                            zone1, zone2 = core[1].split('-')
                            token_str = token_str.replace(']', "")
                            data = Parser.metadata_validator(token_str, "connection", line_number)
                        else:
                            core = line.split()
                            zone1, zone2 = core[1].strip().split('-')
                            data = {"max_link_capacity": 1}
                        if zone1 == zone2:
                            raise ValueError(f"Line {line_number}: Self-connection is not allowed: {zone1}-{zone2}")
                        if zone1 not in self.graph.zone_dict:
                            raise ValueError(f"Line {line_number}: Connection references undefined zone: {zone1}")
                        if zone2 not in self.graph.zone_dict:
                            raise ValueError(f"Line {line_number}: Connection references undefined zone: {zone2}")
                        sorted_pair = sorted([zone1, zone2])
                        pair: tuple[str, str] = (sorted_pair[0], sorted_pair[1])
                        if pair in self.seen_connections:
                            raise ValueError(f"Line {line_number}: Duplicate connection: {zone1}-{zone2}")
                        self.seen_connections.append(pair)
                        self.graph.add_connection(Connection(zone1, zone2, data["max_link_capacity"]))
                    else:
                        raise ValueError(f"Line {line_number}: Unrecognized line format")
                if (self.graph.start_hub is None) or (self.graph.end_hub is None):
                    raise ValueError(f"Line {line_number}: Exactly one 'start_hub' and one 'end_hub' must exist!")
        except FileNotFoundError:
            print(f"ERROR: {filepath} file not found")
            sys.exit(1)
        except ValueError as e:
            print(f"Parsing Error: {e}")
            sys.exit(1)
        except IndexError:
            print(f"Parsing Error: Line {line_number}: Malformed line, missing required fields.\n"
                  f"  Expected formats:\n"
                  f"    nb_drones: <number>\n"
                  f"    hub: <name> <x> <y> [metadata]\n"
                  f"    connection: <zone1>-<zone2> [metadata]")
            sys.exit(1)
        except PermissionError:
            print("ERROR: Permission access denied.")
            sys.exit(1)

    @staticmethod
    def metadata_validator(metadata: str, category: str, line_number: int) -> Dict[str, Any]:
        """
        Takes the raw metadata string (everything between [ and ]) and
        splits it into key=value pairs. Returns a dictionary with the
        parsed values. The 'category' parameter tells it whether to
        expect zone keys (zone, color, max_drones) or connection keys
        (max_link_capacity). Raises ValueError if any key or value is invalid.
        """
        tokens: list = metadata.split()
        data_dict: dict = {}
        valid_zones: List[str] = ["normal", "blocked", "restricted", "priority"]
        try:
            if category == "zone":
                data_dict["zone"] = "normal"
                data_dict["color"] = None
                data_dict["max_drones"] = 1
                for data in tokens:
                    data = data.strip()
                    data = data.split('=')
                    if data[0] == "zone" and len(data) == 2:
                        if data[1] in valid_zones:
                            data_dict["zone"] = data[1]
                        else:
                            raise ValueError(f"Line {line_number}: Invalid Zone type!")
                    elif data[0] == "color" and len(data) == 2:
                        data_dict["color"] = str(data[1])
                    elif data[0] == "max_drones" and len(data) == 2:
                        try:
                            drones_max = int(data[1])
                        except ValueError:
                            raise ValueError(f"Line {line_number}: 'max_drones' must be an integer")
                        if drones_max > 0:
                            data_dict["max_drones"] = drones_max
                        else:
                            raise ValueError(f"Line {line_number}: 'max_drones' should be > 0 !")
                    else:
                        raise ValueError(f"Line {line_number}: {data[0]} isn't a valid metadata block")
            
            elif category == "connection":
                data_dict["max_link_capacity"] = 1
                for data in tokens:
                    data = data.strip()
                    data = data.split('=')
                    if data[0] == "max_link_capacity" and len(data) == 2:
                        try:
                            drones_max = int(data[1])
                        except ValueError:
                            raise ValueError(f"Line {line_number}: 'max_link_capacity' must be an integer")
                        if drones_max > 0:
                            data_dict["max_link_capacity"] = drones_max
                        else:
                            raise ValueError(f"Line {line_number}: 'max_link_capacity' should be > 0 !")
                    else:
                        raise ValueError(f"Line {line_number}: {data[0]} isn't a valid metadata block")
            else:
                raise ValueError(f"Line {line_number}: Unknown category: {category}")
        except ValueError as e:
            print(f"Parsing Error: Line {line_number}: {e}")
            sys.exit(1)
        return data_dict


        
    
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python parser.py <map_file>")
        sys.exit(1)
        
    parser = Parser()
    parser.parse_file(sys.argv[1])

    print(f"nb_drones: {parser.graph.nb_drones}")
    print(f"start_hub: {parser.graph.start_hub}")
    print(f"end_hub: {parser.graph.end_hub}")
    print(f"zones: {parser.graph.zone_dict}")
    print(f"connections: {parser.graph.connection_dict}")
