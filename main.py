from parser import Parser
from simulation import Simulation
import sys

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 main.py <map_file>")
        sys.exit()

    parser = Parser()
    parser.parse_file(sys.argv[1])

    sim = Simulation(parser.graph)
    sim.create_drones()
    sim.run()
