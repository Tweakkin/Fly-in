import sys
import io
import re
import math
import os
import pygame
from parser import Parser
from simulation import Simulation

# ── constants ────────────────────────────────────────────────────────────────
WIDTH, HEIGHT = 1400, 900
PAD           = 80
FPS           = 60
DRONE_SPEED   = 4        # pixels per frame — increase to move faster
NODE_RADIUS   = 28
DRONE_RADIUS  = 12
DRONE_SIZE    = 104      # pixel size to scale the drone sprite to
SNAP_DIST     = 2        # snap to target when this close (pixels)

WHITE  = (255, 255, 255)
BLACK  = (0,   0,   0)
GRAY   = (160, 160, 160)
RED    = (220,  50,  50)
GREEN  = (50,  180,  50)
BLUE   = (50,  120, 220)
ORANGE = (230, 140,  40)
YELLOW = (230, 210,  50)


# ── helpers ───────────────────────────────────────────────────────────────────

def color_for_zone(zone):
    if zone.type == "restricted": return ORANGE
    if zone.type == "priority":   return YELLOW
    if zone.type == "blocked":    return (80, 80, 80)
    return BLUE


def build_positions(graph):
    """zone_name -> (screen_x, screen_y)"""
    zones = list(graph.zone_dict.values())
    min_x = min(z.x for z in zones);  max_x = max(z.x for z in zones)
    min_y = min(z.y for z in zones);  max_y = max(z.y for z in zones)
    rx = max(max_x - min_x, 1)
    ry = max(max_y - min_y, 1)
    pos = {}
    for z in zones:
        sx = int(PAD + (z.x - min_x) / rx * (WIDTH  - 2 * PAD))
        sy = int(PAD + (z.y - min_y) / ry * (HEIGHT - 2 * PAD))
        sy = HEIGHT - sy          # flip y
        pos[z.name] = (sx, sy)
    return pos


def zone_screen_pos(location, drone_id, nb_drones, pos, graph):
    """
    Return the TARGET (x, y) for a drone given its location string.
    Drones at the same zone are spread in a small circle to avoid overlap.
    """
    if '-' in location:
        parts = location.split('-')
        z1, z2 = parts[0], parts[1]
        if z1 in pos and z2 in pos:
            cx = (pos[z1][0] + pos[z2][0]) // 2
            cy = (pos[z1][1] + pos[z2][1]) // 2
        else:
            cx, cy = pos[graph.start_hub.name]
    else:
        cx, cy = pos.get(location, pos[graph.start_hub.name])

    angle  = (2 * math.pi * drone_id) / max(nb_drones, 1)
    offset = 14
    return cx + offset * math.cos(angle), cy + offset * math.sin(angle)


def run_simulation(graph):
    sim = Simulation(graph)
    sim.create_drones()
    old_stdout = sys.stdout
    buf = io.StringIO()
    sys.stdout = buf
    sim.run()
    sys.stdout = old_stdout

    turns = []
    for line in buf.getvalue().strip().split('\n'):
        line = line.strip()
        if not line:
            continue
        if any(line.startswith(p) for p in
               ("Before", "After", "=", "running", "Total", "Chosen", "These", "All")):
            continue
        turns.append(line)
    return turns


def parse_turn(turn_line):
    moves = {}
    matches = re.findall(r'<D(\d+)>-<\s*([^>]+)>|D(\d+)-([^\s]+)', turn_line)
    for m in matches:
        d_id = m[0] if m[0] else m[2]
        dest = (m[1] if m[1] else m[3]).strip()
        moves[d_id] = dest
    return moves


# ── main ──────────────────────────────────────────────────────────────────────

def draw_graph(map_file):
    parser = Parser()
    parser.parse_file(map_file)
    graph = parser.graph

    if not graph.start_hub or not graph.end_hub:
        print("Missing start or end hub.")
        return

    turns_data = run_simulation(graph)

    pygame.init()
    screen   = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(f"Fly-in  –  {map_file}")
    clock    = pygame.time.Clock()
    font     = pygame.font.SysFont("monospace", 13)
    font_big = pygame.font.SysFont("monospace", 18, bold=True)

    # ── load assets ───────────────────────────────────────────────────────────
    base_dir   = os.path.dirname(os.path.abspath(__file__))
    background = pygame.image.load(os.path.join(base_dir, "background.jpg")).convert()
    background = pygame.transform.scale(background, (WIDTH, HEIGHT))

    drone_img_orig = pygame.image.load(os.path.join(base_dir, "drone.png")).convert_alpha()
    drone_img      = pygame.transform.scale(drone_img_orig, (DRONE_SIZE, DRONE_SIZE))

    pos = build_positions(graph)

    # ── drone state ───────────────────────────────────────────────────────────
    # current pixel positions (floats for smooth movement)
    drone_pos    = {}
    # target pixel positions
    drone_target = {}
    # logical location (zone name or connection string)
    drone_loc    = {}

    for i in range(graph.nb_drones):
        sid = str(i)
        tx, ty = zone_screen_pos(graph.start_hub.name, i, graph.nb_drones, pos, graph)
        drone_pos[sid]    = [tx, ty]
        drone_target[sid] = (tx, ty)
        drone_loc[sid]    = graph.start_hub.name

    turn_index = 0
    finished   = False

    # ── game loop ─────────────────────────────────────────────────────────────
    while True:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit(); return

        # ── move each drone toward its target ─────────────────────────────────
        all_arrived = True
        for sid in drone_pos:
            cx, cy = drone_pos[sid]
            tx, ty = drone_target[sid]
            dx, dy = tx - cx, ty - cy
            dist   = math.hypot(dx, dy)
            if dist > SNAP_DIST:
                all_arrived = False
                # move DRONE_SPEED pixels toward target
                step = DRONE_SPEED / dist
                drone_pos[sid][0] += dx * step
                drone_pos[sid][1] += dy * step
            else:
                # snap exactly
                drone_pos[sid][0] = tx
                drone_pos[sid][1] = ty

        # ── advance to next turn only when all drones have arrived ────────────
        if all_arrived and not finished:
            if turn_index < len(turns_data):
                moves = parse_turn(turns_data[turn_index])
                drone_loc.update(moves)
                # set new targets
                for sid, loc in drone_loc.items():
                    tx, ty = zone_screen_pos(loc, int(sid), graph.nb_drones, pos, graph)
                    drone_target[sid] = (tx, ty)
                turn_index += 1
            else:
                finished = True

        # ── draw ──────────────────────────────────────────────────────────────
        screen.blit(background, (0, 0))

        # edges
        drawn = set()
        for connections in graph.connection_dict.values():
            for conn in connections:
                edge = tuple(sorted([conn.zone_1, conn.zone_2]))
                if edge in drawn: continue
                drawn.add(edge)
                if conn.zone_1 in pos and conn.zone_2 in pos:
                    pygame.draw.line(screen, GRAY, pos[conn.zone_1], pos[conn.zone_2], 2)
                    if conn.max_capacity > 1:
                        mx = (pos[conn.zone_1][0] + pos[conn.zone_2][0]) // 2
                        my = (pos[conn.zone_1][1] + pos[conn.zone_2][1]) // 2
                        lbl = font.render(f"cap:{conn.max_capacity}", True, BLACK)
                        screen.blit(lbl, (mx, my - 14))

        # nodes
        for zone in graph.zone_dict.values():
            if zone.name not in pos: continue
            x, y  = pos[zone.name]
            color = color_for_zone(zone)
            if zone.name == graph.start_hub.name:
                bcol, bw = GREEN, 4
            elif zone.name == graph.end_hub.name:
                bcol, bw = RED, 4
            else:
                bcol, bw = BLACK, 2
            pygame.draw.circle(screen, color, (x, y), NODE_RADIUS)
            pygame.draw.circle(screen, bcol,  (x, y), NODE_RADIUS, bw)
            lbl = font.render(zone.name, True, BLACK)
            screen.blit(lbl, (x - lbl.get_width() // 2, y + NODE_RADIUS + 3))

        # drones
        for sid in drone_pos:
            x = int(drone_pos[sid][0])
            y = int(drone_pos[sid][1])
            # centre the sprite on the drone position
            rect = drone_img.get_rect(center=(x, y))
            screen.blit(drone_img, rect)
            lbl = font.render(f"D{sid}", True, WHITE)
            screen.blit(lbl, (x - lbl.get_width() // 2, y - DRONE_SIZE // 2 - 12))

        # HUD
        if finished:
            hud = font_big.render(f"Done!  {turn_index} turns", True, GREEN)
        else:
            hud = font_big.render(f"Turn {turn_index} / {len(turns_data)}", True, BLACK)
        screen.blit(hud, (10, 10))

        pygame.display.flip()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python visualizer_pygame.py <map_file.txt>")
        sys.exit(1)
    draw_graph(sys.argv[1])
