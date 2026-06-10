import sys
import io
import re
import math
import tkinter as tk
from parser import Parser
from simulation import Simulation

def safe_color(root, color, fallback="lightblue"):
    """Return color if Tkinter recognises it, otherwise return fallback."""
    try:
        root.winfo_rgb(color)
        return color
    except tk.TclError:
        return fallback

def draw_graph(map_file):
    # 1. Parse the map
    parser = Parser()
    parser.parse_file(map_file)
    graph = parser.graph

    if not graph.start_hub or not graph.end_hub:
        print("Missing start or end hub.")
        return

    # 2. Run simulation and capture output
    sim = Simulation(graph)
    sim.create_drones()
    
    # Capture standard output to get the turn movements
    old_stdout = sys.stdout
    captured_output = io.StringIO()
    sys.stdout = captured_output
    sim.run()
    sys.stdout = old_stdout
    
    sim_output = captured_output.getvalue().strip().split('\n')
    
    # Filter only lines that look like turns (containing drone movements)
    turns_data = []
    for line in sim_output:
        line = line.strip()
        if not line or line.startswith("Before") or line.startswith("After") or line.startswith("=") or line.startswith("running") or line.startswith("Total") or line.startswith("Chosen"):
            continue
        turns_data.append(line)

    # 3. Initialize tkinter
    root = tk.Tk()
    root.title(f"Fly-in Animated Visualizer: {map_file}")
    
    canvas_width = 800
    canvas_height = 600
    canvas = tk.Canvas(root, width=canvas_width, height=canvas_height, bg="white")
    canvas.pack(fill=tk.BOTH, expand=True)

    # Find bounding box to scale coordinates
    zones = list(graph.zone_dict.values())
    min_x = min(z.x for z in zones)
    max_x = max(z.x for z in zones)
    min_y = min(z.y for z in zones)
    max_y = max(z.y for z in zones)

    pad = 60
    range_x = max(max_x - min_x, 1)
    range_y = max(max_y - min_y, 1)

    def scale_x(x):
        return pad + (x - min_x) * ((canvas_width - 2 * pad) / range_x)
    
    def scale_y(y):
        return canvas_height - (pad + (y - min_y) * ((canvas_height - 2 * pad) / range_y))

    # --- Draw Static Map ---
    drawn_edges = set()
    for zone_name, connections in graph.connection_dict.items():
        for conn in connections:
            z1 = conn.zone_1
            z2 = conn.zone_2
            edge = tuple(sorted([z1, z2]))
            if edge not in drawn_edges:
                drawn_edges.add(edge)
                node1 = graph.zone_dict[z1]
                node2 = graph.zone_dict[z2]
                x1, y1 = scale_x(node1.x), scale_y(node1.y)
                x2, y2 = scale_x(node2.x), scale_y(node2.y)
                canvas.create_line(x1, y1, x2, y2, fill="gray", width=2)
                if conn.max_capacity > 1:
                    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
                    canvas.create_text(cx, cy - 10, text=f"cap:{conn.max_capacity}", fill="black")

    node_radius = 20
    for zone in zones:
        x = scale_x(zone.x)
        y = scale_y(zone.y)
        color = safe_color(root, zone.color) if zone.color else "lightblue"
        if not zone.color:
            if zone.type == "restricted": color = "orange"
            elif zone.type == "priority": color = "lightgreen"
            elif zone.type == "blocked": color = "black"

        if zone.name == graph.start_hub.name:
            canvas.create_rectangle(x - node_radius, y - node_radius, x + node_radius, y + node_radius, fill=color, outline="green", width=3)
        elif zone.name == graph.end_hub.name:
            canvas.create_rectangle(x - node_radius, y - node_radius, x + node_radius, y + node_radius, fill=color, outline="red", width=3)
        else:
            canvas.create_oval(x - node_radius, y - node_radius, x + node_radius, y + node_radius, fill=color, outline="black")
        
        label = f"{zone.name}\n(max:{zone.max_drones})"
        if zone.type != "normal":
            label += f"\n{zone.type}"
        canvas.create_text(x, y + node_radius + 15, text=label, fill="black", justify=tk.CENTER)

    # Store drones current locations (initially all at start_hub)
    drone_locations = {}
    for i in range(graph.nb_drones):
        drone_locations[str(i)] = graph.start_hub.name

    turn_index = 0
    drone_dots = {} # map drone_id to canvas oval item
    drone_texts = {} # map drone_id to canvas text item
    drone_actual_coords = {} # track exact (x,y) for smooth animation

    turn_label = canvas.create_text(canvas_width/2, 20, text="Turn: 0", font=("Arial", 16, "bold"), fill="black")

    def get_coords(location_name, d_id_str):
        """Returns (x, y) target for a drone including an offset to prevent total overlapping."""
        if '-' in location_name:
            z1, z2 = location_name.split('-')
            n1 = graph.zone_dict.get(z1)
            n2 = graph.zone_dict.get(z2)
            if n1 and n2:
                cx, cy = (scale_x(n1.x) + scale_x(n2.x))/2, (scale_y(n1.y) + scale_y(n2.y))/2
            else:
                cx, cy = scale_x(graph.start_hub.x), scale_y(graph.start_hub.y)
        else:
            node = graph.zone_dict.get(location_name)
            if node:
                cx, cy = scale_x(node.x), scale_y(node.y)
            else:
                cx, cy = scale_x(graph.start_hub.x), scale_y(graph.start_hub.y)
                
        # Offset drones in a circle around the zone center
        offset_idx = int(d_id_str)
        radius = 15
        angle = (2 * math.pi * offset_idx) / max(graph.nb_drones, 1)
        ox = radius * math.cos(angle)
        oy = radius * math.sin(angle)
        return cx + ox, cy + oy

    # Initialize drone visual items
    for d_id, loc in drone_locations.items():
        dx, dy = get_coords(loc, d_id)
        drone_actual_coords[d_id] = (dx, dy)
        drone_dots[d_id] = canvas.create_oval(dx-6, dy-6, dx+6, dy+6, fill="red", outline="black")
        drone_texts[d_id] = canvas.create_text(dx, dy-10, text=f"D{d_id}", fill="darkred", font=("Arial", 8))

    def animate_turn(frames_left, target_coords):
        if frames_left <= 0:
            # Snap to exact target to finish turn
            for d_id, (tx, ty) in target_coords.items():
                drone_actual_coords[d_id] = (tx, ty)
                canvas.coords(drone_dots[d_id], tx-6, ty-6, tx+6, ty+6)
                canvas.coords(drone_texts[d_id], tx, ty-10)
            
            # Wait half a second before starting next turn
            root.after(500, next_turn)
            return

        # Interpolate coordinates smoothly
        for d_id, (tx, ty) in target_coords.items():
            cx, cy = drone_actual_coords[d_id]
            nx = cx + (tx - cx) * 0.15 # 15% closer each frame
            ny = cy + (ty - cy) * 0.15
            drone_actual_coords[d_id] = (nx, ny)
            canvas.coords(drone_dots[d_id], nx-6, ny-6, nx+6, ny+6)
            canvas.coords(drone_texts[d_id], nx, ny-10)
            
        root.after(50, animate_turn, frames_left - 1, target_coords)

    def next_turn():
        nonlocal turn_index
        
        if turn_index < len(turns_data):
            turn_line = turns_data[turn_index]
            canvas.itemconfig(turn_label, text=f"Turn: {turn_index + 1}\n{turn_line}")
            
            # Parse movements in this turn using regex to handle spaces inside brackets
            matches = re.findall(r'<D(\d+)>-<\s*([^>]+)>|D(\d+)-([^\s]+)', turn_line)
            for m in matches:
                d_id_str = m[0] if m[0] else m[2]
                dest = m[1] if m[1] else m[3]
                drone_locations[d_id_str] = dest.strip()
            
            # Calculate new target coords for all drones
            target_coords = {}
            for d_id, loc in drone_locations.items():
                target_coords[d_id] = get_coords(loc, d_id)
                
            turn_index += 1
            # Start smooth animation for this turn (20 frames)
            animate_turn(20, target_coords)
        else:
            canvas.itemconfig(turn_label, text=f"Simulation Finished! (Total Turns: {turn_index})")

    # Start animation loop after 1 second
    root.after(1000, next_turn)
    root.mainloop()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python visualizer.py <map_file.txt>")
        sys.exit(1)
    
    draw_graph(sys.argv[1])
