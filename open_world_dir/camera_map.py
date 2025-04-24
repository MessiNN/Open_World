# --- START OF FILE camera_map.py ---
import pygame
import threading
import world_struct as world_struct_stable # Need WORLD_WIDTH/HEIGHT
# <<< NETWORK: Import player module for type hinting and ID check >>>
import enemies.player as player_module
# <<< NETWORK: Import network config for local player ID >>>
import NETconfig

# --- Camera State ---
camera_x = 0
camera_y = 0

# --- Map State & Constants ---
show_map = False
MAP_WIDTH = 200
MAP_HEIGHT = MAP_WIDTH
# <<< FIX: Use config for screen dimensions >>>
MAP_X = world_struct_stable.SCREEN_WIDTH - MAP_WIDTH - 10
MAP_Y = 10
MAP_BG_COLOR = (100, 100, 100, 200) # Semi-transparent gray
MAP_BORDER_COLOR = (255, 255, 255) # White
MAP_PLAYER_COLOR = (255, 0, 0) # Red for LOCAL player
MAP_OTHER_PLAYER_COLOR = (0, 0, 255) # Blue for other players
MAP_PLAYER_SIZE = 3 # Make slightly larger
# Zone Colors (Semi-transparent)
MAP_ZONE_FOREST_COLOR = (0, 80, 0, 180)
MAP_ZONE_KINGDOM_COLOR = (130, 130, 130, 180)
# Feature Colors (Semi-transparent)
MAP_WALL_COLOR = (80, 80, 80, 200)
MAP_PATH_COLOR = (210, 210, 210, 200)
MAP_TOWER_COLOR = (60, 60, 60, 200) # For towers and gatehouses

# --- Map Surface (Create once) ---
map_surface = pygame.Surface((MAP_WIDTH, MAP_HEIGHT), pygame.SRCALPHA) # Use SRCALPHA for transparency

# --- Helper Functions ---
def apply_camera_to_point(world_x, world_y):
    """Converts world coordinates to screen coordinates based on camera."""
    return int(world_x - camera_x), int(world_y - camera_y)

def get_camera_world_rect():
    """Returns a pygame.Rect representing the camera's view in world coordinates."""
    # <<< FIX: Use config for screen dimensions >>>
    return pygame.Rect(camera_x, camera_y, world_struct_stable.SCREEN_WIDTH, world_struct_stable.SCREEN_HEIGHT)

def update_camera(player_x, player_y, effective_world_width, effective_world_height):
    """Updates the camera position to follow the player, clamping to world bounds."""
    global camera_x, camera_y
    # <<< FIX: Use config for screen dimensions >>>
    target_camera_x = player_x - world_struct_stable.SCREEN_WIDTH // 2
    target_camera_y = player_y - world_struct_stable.SCREEN_HEIGHT // 2

    # Clamp camera to world boundaries
    # <<< FIX: Use config for screen dimensions >>>
    camera_x = max(0, min(target_camera_x, effective_world_width - world_struct_stable.SCREEN_WIDTH))
    camera_y = max(0, min(target_camera_y, effective_world_height - world_struct_stable.SCREEN_HEIGHT))

def toggle_map():
    """Toggles the map visibility."""
    global show_map
    show_map = not show_map

# --- Map Drawing Function ---
def world_to_map_coords(world_x, world_y, world_width, world_height):
    """Converts world coordinates to map coordinates."""
    map_rel_x = 0.0
    if world_width > 0:
         map_rel_x = max(0.0, min((world_x / world_width) * MAP_WIDTH, MAP_WIDTH - 1.0))
    map_rel_y = 0.0
    if world_height > 0:
        map_rel_y = max(0.0, min((world_y / world_height) * MAP_HEIGHT, MAP_HEIGHT - 1.0))
    return int(map_rel_x), int(map_rel_y)

# <<< MODIFIED to accept network_players list >>>
def draw_map_overlay(surface, local_player, world_data, world_width, world_height, game_state, network_players):
    """Draws the mini-map overlay onto the main surface, showing all players."""
    if not show_map:
        return

    w_to_map = lambda x, y: world_to_map_coords(x, y, world_width, world_height)

    # 1. Clear map surface
    map_surface.fill(MAP_BG_COLOR)

    # 2. Draw World Features (Overworld/Dungeon) - No changes needed here
    if game_state == "overworld":
        # Forest Zone
        if "forest_poly_points" in world_data:
            map_forest_boundary = [w_to_map(p[0], p[1]) for p in world_data["forest_poly_points"]]
            if len(map_forest_boundary) > 2:
                pygame.draw.polygon(map_surface, MAP_ZONE_FOREST_COLOR, map_forest_boundary)
        # Kingdom Zone
        if "kingdom_poly_points" in world_data:
            map_kingdom_boundary = [w_to_map(p[0], p[1]) for p in world_data["kingdom_poly_points"]]
            if len(map_kingdom_boundary) > 2:
                pygame.draw.polygon(map_surface, MAP_ZONE_KINGDOM_COLOR, map_kingdom_boundary)
        # Path
        if world_data.get("path_info"):
            path_info = world_data["path_info"]
            map_path_start = w_to_map(*path_info["start"]); map_path_end = w_to_map(*path_info["end"])
            pygame.draw.line(map_surface, MAP_PATH_COLOR, map_path_start, map_path_end, 2)
        # Walls
        if "kingdom_wall_vertices" in world_data and "gate_info" in world_data:
            map_wall_verts = [w_to_map(v[0], v[1]) for v in world_data["kingdom_wall_vertices"]]
            map_wall_verts_count = len(map_wall_verts)
            gate_info = world_data["gate_info"]; gate_segment_index = gate_info.get("segment_index", -1)
            for i in range(map_wall_verts_count):
                if i != gate_segment_index:
                    pygame.draw.line(map_surface, MAP_WALL_COLOR, map_wall_verts[i], map_wall_verts[(i + 1) % map_wall_verts_count], 2)
        # Towers & Gatehouses
        for structure_key in ["wall_towers", "gatehouses"]:
             if structure_key in world_data:
                 for item in world_data[structure_key]:
                     if 'base_rect' in item:
                         map_pos = w_to_map(item['base_rect'].centerx, item['base_rect'].centery)
                         pygame.draw.rect(map_surface, MAP_TOWER_COLOR, (map_pos[0]-1, map_pos[1]-1, 3, 3))

    elif game_state == "dungeon":
         if "dungeon_grid" in world_data:
             grid = world_data["dungeon_grid"]
             # <<< FIX: Use constants consistently >>>
             tile_size_world = world_struct_stable.DUNGEON_TILE_SIZE
             tile_size_map_x = max(1, int((MAP_WIDTH / world_width) * tile_size_world)) # Ensure at least 1 pixel
             tile_size_map_y = max(1, int((MAP_HEIGHT / world_height) * tile_size_world))
             for r_idx, row in enumerate(grid):
                 for c_idx, tile_type in enumerate(row):
                     map_x, map_y = w_to_map(c_idx * tile_size_world, r_idx * tile_size_world)
                     # <<< FIX: Use constants consistently >>>
                     if tile_type == world_struct_stable.TILE_WALL: # Use constant from world_constants
                         pygame.draw.rect(map_surface, MAP_WALL_COLOR, (map_x, map_y, tile_size_map_x, tile_size_map_y))
                     elif tile_type == world_struct_stable.TILE_FLOOR: # Use constant from world_constants
                         pygame.draw.rect(map_surface, MAP_PATH_COLOR, (map_x, map_y, tile_size_map_x, tile_size_map_y)) # Use path color for floor


    # 3. Draw Map Border
    pygame.draw.rect(map_surface, MAP_BORDER_COLOR, map_surface.get_rect(), 1)

    # 4. Draw ALL Player Positions
    # <<< ADDED: Iterate through network_players list >>>
    local_player_id = NETconfig.my_player_id # Get the ID of the player running this instance

    # Use a context manager for the lock if network_players can change during iteration
    with threading.Lock(): # Assuming network_players might be modified by network threads
        players_copy = list(network_players.values()) # Draw based on a snapshot

    for p in players_copy:
        if p: # Ensure player object exists
            map_player_x, map_player_y = w_to_map(p.x, p.y)
            # Use different colors for local vs other players
            player_color = MAP_PLAYER_COLOR if p.player_id == local_player_id else MAP_OTHER_PLAYER_COLOR
            pygame.draw.circle(map_surface, player_color, (map_player_x, map_player_y), MAP_PLAYER_SIZE)

    # 5. Blit the map surface onto the main screen
    surface.blit(map_surface, (MAP_X, MAP_Y))

# --- END OF FILE camera_map.py ---