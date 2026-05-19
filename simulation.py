from models import Graph, Drone, Connection
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
        self.graph.start_hub.curr_drones: int = self.graph.nb_drones
        while True:
            self.turns += 1
            turn_movements: list[str] = []
            all_arrived: bool = True
            conn_usage: dict[Connection, int] = {}
            self.drones.sort(key=lambda d: d.path_index, reverse=True)
            for drone in self.drones:
                if (drone.path_index == len(drone.path) - 1):
                    continue

                all_arrived = False
                
                curr_zone = drone.path[drone.path_index]
                next_zone = drone.path[drone.path_index + 1]

                #  Find the exact Connection object between the current zone and the next zone
                active_conn = None
                for conn in self.graph.connection_dict[curr_zone]:
                    if conn.zone_1 == next_zone or conn.zone_2 == next_zone:
                        active_conn = conn
                        break
                
                # Check if the connection road is too crowded
                current_traffic = conn_usage.get(active_conn, 0)
                if current_traffic >= active_conn.max_capacity:
                    continue

                # Check if the destination zone is too crowded
                curr_drones = self.graph.zone_dict[next_zone].curr_drones
                max_drones = self.graph.zone_dict[next_zone].max_drones
                if curr_drones >= max_drones and next_zone != self.graph.end_hub.name:
                    continue
                
                # If we survive both checks, we move
                conn_usage[active_conn] = current_traffic + 1

                self.graph.zone_dict[drone.path[drone.path_index]].curr_drones -= 1
                drone.path_index += 1
                drone.current_zone = self.graph.zone_dict[drone.path[drone.path_index]]
                self.graph.zone_dict[drone.path[drone.path_index]].curr_drones += 1
                turn_movements.append(f"D{drone.drone_id}-{drone.current_zone.name}")
            if all_arrived == True:
                break
            else:
                print(" ".join(turn_movements))