from models import Graph, Zone, Connection

class Parser:
    def __init__(self):
        self.graph: Graph = Graph()

    def parse_file(self, filepath: str):
        try:
            with open(filepath, 'r') as file:
                for line in file:
                    if line.startswith("nb_drones"):
                        pass
                    elif line.startswith("hub") or line.startswith("start_hub") or line.startswith("end_hub"):
                        if '[' in line:
                            core, metadata = line.strip().split('[')
                            core = core.split()
                            metadata = metadata.replace("]", "").split()
                        else:
                            core = line.strip().split()
                        self.graph.add_zone(Zone(core[1], int(core[2]), int(core[3])))

                    elif line.startswith("connection"):
                        if '[' in line:
                            core, metadata = line.strip().split('[')
                            core = core.split()
                            zone1, zone2 = core[1].split('-')
                            metadata = metadata.replace("]", "").split()
                        else:
                            core = line.split()
                            zone1, zone2 = core[1].strip().split('-')
                        self.graph.add_connection(Connection(zone1, zone2))
        except FileNotFoundError:
            print(f"ERROR: {filepath} file not found")
        except PermissionError:
            print("ERROR: Permission access denied.")
        
    
if __name__ == "__main__":
    parser = Parser()
    parser.parse_file("./test_map.txt")
    print(parser.graph.zone_dict)
    print("_______________________________")
    print(parser.graph.connection_dict)