from models import Graph, Drone
from typing import Optional

class Simulation:
    def __init__(self, graph: Graph):
        self.graph: Graph = graph
        self.drones: list[Drone] = []
        self.turns: int = 0
        self.path: Optional[list[str]] = graph.bfs_shortest_path(graph.start_hub.name, graph.end_hub.name)
        if self.path is None:
            raise ValueError("No valid path exists between start and end!")
    
    def create_drones(self):
        for i in range(self.graph.nb_drones):
            new_drone = Drone(i, self.graph.start_hub)
            new_drone.path = self.path
            self.drones.append(new_drone)


    def run(self):
        """
        Keep looping as long as there is at least one 
        drone that hasn't reached the end_hub
        """
        while True:
            self.turns += 1
            turn_movements: list[str] = []
            all_arrived: bool = True
            for drone in self.drones:
                if drone.path_index == len(drone.path) - 1:
                    pass
                else:
                    all_arrived = False
                    drone.path_index += 1
                    drone.current_zone = self.graph.zone_dict[drone.path[drone.path_index]]
                    turn_movements.append(f"D{drone.drone_id}-{drone.current_zone.name}")
            if all_arrived == True:
                break
            else:
                print(" ".join(turn_movements))