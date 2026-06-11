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
    
    # def create_drones(self):
    #     for i in range(self.graph.nb_drones):
    #         new_drone = Drone(i, self.graph.start_hub)
    #         self.drones.append(new_drone)

    def create_drones(self):
        """Create drones and divide them equally across the available paths."""
        nb_paths = len(self.all_paths)
        for i in range(self.graph.nb_drones):
            new_drone = Drone(i, self.graph.start_hub)
            # Assign path by round-robin: drone 0 -> path 0, drone 1 -> path 1, drone 2 -> path 0, ...
            new_drone.path = self.all_paths[i % nb_paths]
            self.drones.append(new_drone)


    def run(self):
        """
        Keep looping as long as there is at least one 
        drone that hasn't reached the end_hub
        """
        """ Initialize the starting hub with all the drones at once """
        self.graph.start_hub.curr_drones: int = self.graph.nb_drones
        
        """ Begin the main simulation loop, processing one turn per iteration """
        while True:
            """ Increment the turn counter at the start of each round """
            self.turns += 1
            """ Track all valid movements made during this specific turn """
            turn_movements: list[str] = []
            """ Assume all drones have finished until proven otherwise """
            all_arrived: bool = True

            """ Keep track of how many drones are actively flying on each connection road right now """
            conn_usage: dict[Connection, int] = {}

            """ Sort drones so those closest to the finish line get priority to move first """
            self.drones.sort(key=lambda d: d.path_index, reverse=True)

            """ Evaluate each drone one by one to see if it can move this turn """
            for drone in self.drones:
                
                """ Handle drones that are currently mid-flight toward a restricted zone """
                if drone.in_trans is not None:
                    """ Tick down the remaining flight time """
                    drone.turns_remaining -= 1
                    """ If flight time is zero, the drone lands in the restricted zone """
                    if drone.turns_remaining == 0:
                        drone.path_index += 1
                        drone.current_zone = self.graph.zone_dict[drone.path[drone.path_index]]
                        drone.in_trans = None
                        turn_movements.append(f"D{drone.drone_id}-{drone.current_zone.name}")
                    """ Since this drone is still busy, not all drones have arrived """
                    all_arrived = False
                    continue

                """ Dynamically assign the best path while waiting at the start hub """
                # if not drone.path or drone.path_index == 0:
                #     best_path = None
                #     best_score = 999999999
                    
                #     for p in self.all_paths:
                #         # Find out how many drones are actively flying on this path right now
                #         active_traffic = sum(1 for d in self.drones if d.path == p and d.path_index > 0)
                        
                #         # Calculate the actual simulation cost of the path
                #         path_cost = sum(self.graph.zone_cost(z) for z in p if z not in [self.graph.start_hub.name, self.graph.end_hub.name])
                        
                #         # Score is traffic congestion + actual path cost
                #         score = active_traffic + len(p)
                        
                #         if score < best_score:
                #             best_score = score
                #             best_path = p
                            
                #     drone.path = best_path


                """ Skip evaluating this drone if it is already sitting at the final destination """
                if (drone.path_index == len(drone.path) - 1):
                    continue
                
                """ We found a drone that hasn't finished, so keep the simulation running """
                all_arrived = False
                
                """ Identify the drone's current location and where it wants to go next """
                curr_zone = drone.path[drone.path_index]
                next_zone = drone.path[drone.path_index + 1]

                """ Search the graph to find the exact Connection object linking these two zones """
                active_conn = None
                for conn in self.graph.connection_dict[curr_zone]:
                    if conn.zone_1 == next_zone or conn.zone_2 == next_zone:
                        active_conn = conn
                        break
                
                """ Check if the connection road is already maxed out with other drones """
                current_traffic = conn_usage.get(active_conn, 0)
                if current_traffic >= active_conn.max_capacity:
                    continue

                """ Check if the destination zone is already full (except if it's the final end hub) """
                curr_drones = self.graph.zone_dict[next_zone].curr_drones
                max_drones = self.graph.zone_dict[next_zone].max_drones
                if curr_drones >= max_drones and next_zone != self.graph.end_hub.name:
                    continue
                
                """ The drone survives both traffic checks, so we officially let it move """
                conn_usage[active_conn] = current_traffic + 1

                """ Get the target zone object to check its type """
                next_zone_object = self.graph.zone_dict[next_zone]
                
                """ Handle movement if the destination is a restricted zone """
                if next_zone_object.type == "restricted":
                    """ Remove the drone from its current zone immediately """
                    self.graph.zone_dict[drone.path[drone.path_index]].curr_drones -= 1
                    """ Mark it as in-transit with a mandatory 1-turn wait time """
                    drone.in_trans = active_conn
                    drone.turns_remaining = 1
                    """ Reserve the space in the destination zone so no one else steals it while we fly """
                    self.graph.zone_dict[next_zone].curr_drones += 1
                    """ Log the movement onto the connection string for the terminal output """
                    conn_name = f"{active_conn.zone_1}-{active_conn.zone_2}"
                    turn_movements.append(f"D{drone.drone_id}-{conn_name}")

                else:
                    """ Handle standard movement for normal and priority zones """
                    """ Remove the drone from its current zone """
                    self.graph.zone_dict[drone.path[drone.path_index]].curr_drones -= 1
                    """ Immediately advance its path index and update its current zone """
                    drone.path_index += 1
                    drone.current_zone = self.graph.zone_dict[drone.path[drone.path_index]]
                    """ Occupy space in the new zone """
                    self.graph.zone_dict[drone.path[drone.path_index]].curr_drones += 1
                    """ Log the arrival at the zone for the terminal output """
                    turn_movements.append(f"D{drone.drone_id}-{drone.current_zone.name}")

            """ If every single drone is at the end_hub, print final stats and stop the loop """
            if all_arrived == True:
                print(" ".join(turn_movements))
                print(f"Total turn {self.turns}")
                print(f"All paths: {self.all_paths}")
                break
            else:
                """ Otherwise, just print the movements for this turn and continue to the next one """
                print(" ".join(turn_movements))
                