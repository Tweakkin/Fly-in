from models import Graph, Drone, Connection
from typing import Optional

class Simulation:
    def __init__(self, graph: Graph):
        self.graph: Graph = graph
        self.drones: list[Drone] = []
        self.turns: int = 0
        graph.find_multiple_paths(graph.start_hub.name, graph.end_hub.name)
        self.all_paths = self.graph.all_paths
        if self.all_paths is None:
            raise ValueError("No valid path exists between start and end!")
    
    def create_drones(self):
        for i in range(self.graph.nb_drones):
            new_drone = Drone(i, self.graph.start_hub)
            self.drones.append(new_drone)


    def run(self):
        """
        Keep looping as long as there is at least one 
        drone that hasn't reached the end_hub
        """
        self.graph.start_hub.curr_drones: int = self.graph.nb_drones
        
        # Loop through turns
        while True:
            self.turns += 1
            turn_movements: list[str] = []
            all_arrived: bool = True

            # Mark what connections are being used
            conn_usage: dict[Connection, int] = {}

            # Sort drones so we can start from whoever is in front
            self.drones.sort(key=lambda d: d.path_index, reverse=True)

            for drone in self.drones:
                
                # For a drone that is joining a restricted zone
                if drone.in_trans is not None:
                    drone.turns_remaining -= 1
                    if drone.turns_remaining == 0:
                        drone.path_index += 1
                        drone.current_zone = self.graph.zone_dict[drone.path[drone.path_index]]
                        drone.in_trans = None
                        turn_movements.append(f"D{drone.drone_id}-{drone.current_zone.name}")
                    all_arrived = False
                    continue

                if not drone.path:
                    drone.path = min(self.all_paths, key=self.drones_in_path)

                # Check if the Drone has reached the end hub
                if (drone.path_index == len(drone.path) - 1):
                    continue
                
                # There is a drone that hasn't reached the end hub.
                all_arrived = False
                
                # Mark our current zone, and our destination
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

                # The drone is leaving a zone, and start traveling to a restricted zone
                next_zone_object = self.graph.zone_dict[next_zone]
                if next_zone_object.type == "restricted":
                    self.graph.zone_dict[drone.path[drone.path_index]].curr_drones -= 1
                    drone.in_trans = active_conn
                    drone.turns_remaining = 1
                    # reserving the next zone even tho we didn't reach it
                    self.graph.zone_dict[next_zone].curr_drones += 1
                    conn_name = f"{active_conn.zone_1}-{active_conn.zone_2}"
                    turn_movements.append(f"D{drone.drone_id}-{conn_name}")

                # The drone leaves a zone, and joins a normal zone
                else:
                    self.graph.zone_dict[drone.path[drone.path_index]].curr_drones -= 1
                    drone.path_index += 1
                    drone.current_zone = self.graph.zone_dict[drone.path[drone.path_index]]
                    self.graph.zone_dict[drone.path[drone.path_index]].curr_drones += 1
                    turn_movements.append(f"D{drone.drone_id}-{drone.current_zone.name}")

            if all_arrived == True:
                print(" ".join(turn_movements))
                print(f"Total turn {self.turns}")
                print(f"All paths: {self.all_paths}")
                break
            else:
                print(" ".join(turn_movements))
    
    def drones_in_path(self, path: list[str]) -> int:
        num_using = 0
        for drone in self.drones:
            if (drone.path == path) and (len(drone.path) - 1 > drone.path_index):
                num_using += 1
        return (num_using * self.get_traffic_penalty(path)) + self.get_path_cost(path)

    def get_path_cost(self, path: list[str]) -> int:
        cost = 0

        for zone_name in path[1:]:
            cost += self.graph.zone_cost(zone_name)
        return cost

    def get_traffic_penalty(self, path: list[str]) -> float:
        highest_penalty = 0.0
        
        # 1. Check zones
        for zone_name in path[1:-1]:
            zone = self.graph.zone_dict[zone_name]
            
            # Calculate the true penalty based on the zone's capacity
            if zone.type == "restricted":
                penalty = 2.0 / zone.max_drones
            else:
                penalty = 1.0 / zone.max_drones
                
            if penalty > highest_penalty:
                highest_penalty = penalty
                
        # 2. Check connections
        for i in range(len(path) - 1):
            curr_zone = path[i]
            next_zone = path[i+1]
            
            for conn in self.graph.connection_dict[curr_zone]:
                if conn.zone_1 == next_zone or conn.zone_2 == next_zone:
                    penalty = 1.0 / conn.max_capacity
                    if penalty > highest_penalty:
                        highest_penalty = penalty
                    break
                    
        return highest_penalty if highest_penalty > 0 else 1.0

