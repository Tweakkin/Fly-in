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
        Opens the map file, reads it line by line, and builds
        the Graph. Each line is identified by its prefix
        (nb_drones, hub, start_hub, end_hub, connection) and
        parsed accordingly. Metadata inside [...] brackets is
        extracted and validated. Raises and stops the program
        on any parsing error, printing the line number and
        cause.
        """
        try:
            with open(filepath, 'r') as file:
                line_number: int = 0
                nb_drones_found: bool = False
                for line in file:
                    line_number += 1
                    if line.strip().startswith("#"):
                        continue
                    if not line.strip():
                        continue
                    # Strip inline comments (after '#')
                    if '#' in line:
                        line = line.split('#')[0]
                    if not line.strip():
                        continue
                    if (not nb_drones_found
                            and not line.startswith(
                                "nb_drones:")):
                        raise ValueError(
                            f"Line {line_number}: "
                            f"First non-comment line "
                            f"must define nb_drones!"
                        )
                    if line.startswith("nb_drones:"):
                        if self.graph.nb_drones > 0:
                            raise ValueError(
                                f"Line {line_number}: "
                                f"'nb_drones' cannot "
                                f"appear multiple times!"
                            )
                        parts = line.split()
                        if len(parts) != 2:
                            raise ValueError(
                                f"Line {line_number}: "
                                f"Expected "
                                f"'nb_drones: <number>'"
                            )
                        try:
                            nb = int(parts[1].strip())
                        except ValueError:
                            raise ValueError(
                                f"Line {line_number}: "
                                f"'nb_drones' must be "
                                f"an integer"
                            )
                        if nb <= 0:
                            raise ValueError(
                                f"Line {line_number}: "
                                f"'nb_drones' should be "
                                f"a positive integer!"
                            )
                        self.graph.nb_drones = nb
                        nb_drones_found = True
                    elif (line.startswith("hub:")
                            or line.startswith(
                                "start_hub:")
                            or line.startswith(
                                "end_hub:")):
                        core_part = (
                            line.split('[')[0]
                            if '[' in line
                            else line
                        )
                        core = core_part.strip().split()
                        if len(core) != 4:
                            raise ValueError(
                                f"Line {line_number}: "
                                f"Expected "
                                f"'<type> <name> <x> <y>'"
                            )
                        try:
                            x, y = (
                                int(core[2]),
                                int(core[3]),
                            )
                        except ValueError:
                            raise ValueError(
                                f"Line {line_number}: "
                                f"Coordinates must be "
                                f"integers"
                            )

                        if '[' in line:
                            bracket_part = (
                                line.split('[', 1)[1]
                            )
                            if '[' in bracket_part:
                                raise ValueError(
                                    f"Line {line_number}"
                                    f": Nested or extra "
                                    f"'[' not allowed "
                                    f"in metadata"
                                )
                            if ']' not in bracket_part:
                                raise ValueError(
                                    f"Line {line_number}"
                                    f": Missing closing "
                                    f"']' for metadata"
                                )
                            token_str, after_bracket = (
                                bracket_part.split(
                                    ']', 1
                                )
                            )
                            if after_bracket.strip():
                                after = (
                                    after_bracket.strip()
                                )
                                raise ValueError(
                                    f"Line "
                                    f"{line_number}: "
                                    f"Unexpected content"
                                    f" after metadata: "
                                    f"'{after}'"
                                )
                            data = (
                                Parser
                                .metadata_validator(
                                    token_str,
                                    "zone",
                                    line_number,
                                )
                            )
                            if (line.startswith("end_hub:")
                                    and "max_drones"
                                    in token_str):
                                raise ValueError(
                                    f"Line {line_number}"
                                    f": 'max_drones' is "
                                    f"not allowed on "
                                    f"end_hub"
                                )
                            zone = Zone(
                                core[1], x, y,
                                data['zone'],
                                data['color'],
                                data['max_drones'],
                            )
                        else:
                            zone = Zone(
                                core[1], x, y
                            )
                        zone_keys = (
                            self.graph.zone_dict.keys()
                        )
                        if zone.name in zone_keys:
                            raise ValueError(
                                f"Line {line_number}: "
                                f"Duplicate zone name: "
                                f"{zone.name}"
                            )
                        elif ((" " in zone.name)
                                or ('-' in zone.name)):
                            raise ValueError(
                                f"Line {line_number}: "
                                f"Zone names cannot "
                                f"contain dashes or "
                                f"spaces: {zone.name}"
                            )
                        self.graph.add_zone(zone)
                        if line.startswith("start_hub:"):
                            if (self.graph.start_hub
                                    is not None):
                                raise ValueError(
                                    f"Line "
                                    f"{line_number}: "
                                    f"Duplicate "
                                    f"'start_hub' "
                                    f"definition!"
                                )
                            self.graph.start_hub = zone
                        elif line.startswith("end_hub:"):
                            if (self.graph.end_hub
                                    is not None):
                                raise ValueError(
                                    f"Line "
                                    f"{line_number}: "
                                    f"Duplicate "
                                    f"'end_hub' "
                                    f"definition!"
                                )
                            self.graph.end_hub = zone

                    elif line.startswith("connection:"):
                        core_part = (
                            line.split('[')[0]
                            if '[' in line
                            else line
                        )
                        core = core_part.strip().split()
                        if len(core) != 2:
                            raise ValueError(
                                f"Line {line_number}: "
                                f"Expected 'connection:"
                                f" <zone1>-<zone2>', "
                                f"got {len(core)} tokens"
                            )
                        zone1, zone2 = (
                            core[1].split('-')
                        )
                        if '[' in line:
                            bracket_part = (
                                line.split('[', 1)[1]
                            )
                            if '[' in bracket_part:
                                raise ValueError(
                                    f"Line {line_number}"
                                    f": Nested or extra "
                                    f"'[' not allowed "
                                    f"in metadata"
                                )
                            if ']' not in bracket_part:
                                raise ValueError(
                                    f"Line {line_number}"
                                    f": Missing closing "
                                    f"']' for metadata"
                                )
                            token_str, after_bracket = (
                                bracket_part.split(
                                    ']', 1
                                )
                            )
                            if after_bracket.strip():
                                after = (
                                    after_bracket.strip()
                                )
                                raise ValueError(
                                    f"Line "
                                    f"{line_number}: "
                                    f"Unexpected content"
                                    f" after metadata: "
                                    f"'{after}'"
                                )
                            data = (
                                Parser
                                .metadata_validator(
                                    token_str,
                                    "connection",
                                    line_number,
                                )
                            )
                        else:
                            data = {
                                "max_link_capacity": 1
                            }
                        if zone1 == zone2:
                            raise ValueError(
                                f"Line {line_number}: "
                                f"Self-connection is "
                                f"not allowed: "
                                f"{zone1}-{zone2}"
                            )
                        z_dict = self.graph.zone_dict
                        if zone1 not in z_dict:
                            raise ValueError(
                                f"Line {line_number}: "
                                f"Connection references"
                                f" undefined zone: "
                                f"{zone1}"
                            )
                        if zone2 not in z_dict:
                            raise ValueError(
                                f"Line {line_number}: "
                                f"Connection references"
                                f" undefined zone: "
                                f"{zone2}"
                            )
                        sorted_pair = sorted(
                            [zone1, zone2]
                        )
                        pair: tuple[str, str] = (
                            sorted_pair[0],
                            sorted_pair[1],
                        )
                        if pair in self.seen_connections:
                            raise ValueError(
                                f"Line {line_number}: "
                                f"Duplicate connection"
                                f": {zone1}-{zone2}"
                            )
                        self.seen_connections.append(
                            pair
                        )
                        cap = data["max_link_capacity"]
                        self.graph.add_connection(
                            Connection(
                                zone1, zone2, cap
                            )
                        )
                    else:
                        raise ValueError(
                            f"Line {line_number}: "
                            f"Unrecognized line format"
                        )
                if (self.graph.start_hub is None
                        or self.graph.end_hub is None):
                    raise ValueError(
                        f"Line {line_number}: "
                        f"Exactly one 'start_hub' and "
                        f"one 'end_hub' must exist!"
                    )
        except FileNotFoundError:
            print(f"ERROR: {filepath} file not found")
            sys.exit(1)
        except ValueError as e:
            print(f"Parsing Error: {e}")
            sys.exit(1)
        except IndexError:
            print(
                f"Parsing Error: Line {line_number}:"
                f" Malformed line, missing required "
                f"fields.\n"
                f"  Expected formats:\n"
                f"    nb_drones: <number>\n"
                f"    hub: <name> <x> <y> [metadata]\n"
                f"    connection: <zone1>-<zone2>"
                f" [metadata]"
            )
            sys.exit(1)
        except PermissionError:
            print("ERROR: Permission access denied.")
            sys.exit(1)

    @staticmethod
    def metadata_validator(
        metadata: str,
        category: str,
        line_number: int,
    ) -> Dict[str, Any]:
        """
        Takes the raw metadata string (everything between
        [ and ]) and splits it into key=value pairs.
        Returns a dictionary with the parsed values. The
        'category' parameter tells it whether to expect
        zone keys (zone, color, max_drones) or connection
        keys (max_link_capacity). Raises ValueError if any
        key or value is invalid.
        """
        tokens: list[str] = metadata.split()
        data_dict: dict[str, Any] = {}
        valid_zones: List[str] = [
            "normal", "blocked",
            "restricted", "priority",
        ]
        if category == "zone":
            data_dict["zone"] = "normal"
            data_dict["color"] = None
            data_dict["max_drones"] = 1
            for data in tokens:
                data = data.strip()
                parts = data.split('=')
                if (parts[0] == "zone"
                        and len(parts) == 2):
                    if parts[1] in valid_zones:
                        data_dict["zone"] = parts[1]
                    else:
                        raise ValueError(
                            f"Line {line_number}: "
                            f"Invalid Zone type!"
                        )
                elif (parts[0] == "color"
                        and len(parts) == 2):
                    data_dict["color"] = str(parts[1])
                elif (parts[0] == "max_drones"
                        and len(parts) == 2):
                    try:
                        drones_max = int(parts[1])
                    except ValueError:
                        raise ValueError(
                            f"Line {line_number}: "
                            f"'max_drones' must be "
                            f"an integer"
                        )
                    if drones_max > 0:
                        data_dict["max_drones"] = (
                            drones_max
                        )
                    else:
                        raise ValueError(
                            f"Line {line_number}: "
                            f"'max_drones' should "
                            f"be > 0 !"
                        )
                else:
                    raise ValueError(
                        f"Line {line_number}: "
                        f"{parts[0]} isn't a valid "
                        f"metadata block"
                    )

        elif category == "connection":
            data_dict["max_link_capacity"] = 1
            for data in tokens:
                data = data.strip()
                parts = data.split('=')
                if (parts[0] == "max_link_capacity"
                        and len(parts) == 2):
                    try:
                        drones_max = int(parts[1])
                    except ValueError:
                        raise ValueError(
                            f"Line {line_number}: "
                            f"'max_link_capacity' "
                            f"must be an integer"
                        )
                    if drones_max > 0:
                        data_dict[
                            "max_link_capacity"
                        ] = drones_max
                    else:
                        raise ValueError(
                            f"Line {line_number}: "
                            f"'max_link_capacity' "
                            f"should be > 0 !"
                        )
                else:
                    raise ValueError(
                        f"Line {line_number}: "
                        f"{parts[0]} isn't a valid "
                        f"metadata block"
                    )
        else:
            raise ValueError(
                f"Line {line_number}: "
                f"Unknown category: {category}"
            )
        return data_dict
