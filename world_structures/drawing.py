# --- START OF FILE drawing.py ---
import pygame
import random # Needed for wall sprite choice if not done in generation
import math # Needed potentially if angles used directly (though generate_wall_tile_data handles it)
from .world_constants import * # Import all constants needed for drawing
from .utils import apply_camera_to_point, apply_camera_to_rect # Import camera utils

def draw_world_background(screen, camera_x, camera_y, world_elements, game_state):
    """Draws the base background (grass, zones, paths or dungeon tiles)"""
    screen_rect_for_culling = screen.get_rect()

    if game_state == "dungeon":
        dungeon_grid = world_elements.get("dungeon_grid")
        if not dungeon_grid: return
        # Calculate visible tile range
        start_col = max(0, int(camera_x // DUNGEON_TILE_SIZE)); end_col = min(DUNGEON_GRID_WIDTH, int((camera_x + SCREEN_WIDTH) // DUNGEON_TILE_SIZE) + 1)
        start_row = max(0, int(camera_y // DUNGEON_TILE_SIZE)); end_row = min(DUNGEON_GRID_HEIGHT, int((camera_y + SCREEN_HEIGHT) // DUNGEON_TILE_SIZE) + 1)
        # Draw visible tiles
        for y in range(start_row, end_row):
            for x in range(start_col, end_col):
                # Check bounds just in case calculation went slightly off
                if 0 <= y < len(dungeon_grid) and 0 <= x < len(dungeon_grid[y]):
                    tile_type = dungeon_grid[y][x]
                    world_tile_x = x * DUNGEON_TILE_SIZE; world_tile_y = y * DUNGEON_TILE_SIZE
                    tile_screen_x, tile_screen_y = apply_camera_to_point(world_tile_x, world_tile_y, camera_x, camera_y)
                    # Only draw if tile is actually on screen
                    if tile_screen_x < SCREEN_WIDTH and tile_screen_x + DUNGEON_TILE_SIZE > 0 and tile_screen_y < SCREEN_HEIGHT and tile_screen_y + DUNGEON_TILE_SIZE > 0:
                        tile_rect_screen = pygame.Rect(tile_screen_x, tile_screen_y, DUNGEON_TILE_SIZE, DUNGEON_TILE_SIZE)
                        if tile_type == TILE_WALL: pygame.draw.rect(screen, DUNGEON_COLOR_WALL, tile_rect_screen)
                        elif tile_type == TILE_FLOOR: pygame.draw.rect(screen, DUNGEON_COLOR_FLOOR, tile_rect_screen)

    elif game_state == "overworld":
        screen.fill(GRASS_COLOR_BASE)
        forest_poly_points = world_elements.get("forest_poly_points", []); kingdom_poly_points = world_elements.get("kingdom_poly_points", [])

        # Draw Forest Ground
        if forest_poly_points:
            forest_poly_screen = [apply_camera_to_point(p[0], p[1], camera_x, camera_y) for p in forest_poly_points]
            # Basic polygon culling: check if bounding box intersects screen
            if len(forest_poly_screen) > 2:
                min_x = min(p[0] for p in forest_poly_screen); max_x = max(p[0] for p in forest_poly_screen); min_y = min(p[1] for p in forest_poly_screen); max_y = max(p[1] for p in forest_poly_screen)
                poly_rect_forest = pygame.Rect(min_x, min_y, max_x - min_x, max_y - min_y)
                if screen_rect_for_culling.colliderect(poly_rect_forest):
                    pygame.draw.polygon(screen, FOREST_GROUND_COLOR, forest_poly_screen)

        # Draw Kingdom Ground
        if kingdom_poly_points:
            kingdom_poly_screen = [apply_camera_to_point(p[0], p[1], camera_x, camera_y) for p in kingdom_poly_points]
            if len(kingdom_poly_screen) > 2:
                min_x = min(p[0] for p in kingdom_poly_screen); max_x = max(p[0] for p in kingdom_poly_screen); min_y = min(p[1] for p in kingdom_poly_screen); max_y = max(p[1] for p in kingdom_poly_screen)
                poly_rect_kingdom = pygame.Rect(min_x, min_y, max_x - min_x, max_y - min_y)
                if screen_rect_for_culling.colliderect(poly_rect_kingdom):
                    pygame.draw.polygon(screen, KINGDOM_GROUND_COLOR, kingdom_poly_screen)

        # Draw Path
        path_info = world_elements.get("path_info")
        if path_info:
            path_start_screen = apply_camera_to_point(*path_info["start"], camera_x, camera_y); path_end_screen = apply_camera_to_point(*path_info["end"], camera_x, camera_y)
            # Use clip line for efficiency - only draws the visible part
            path_clip = screen_rect_for_culling.clipline(path_start_screen, path_end_screen)
            if path_clip: pygame.draw.line(screen, path_info["color"], path_clip[0], path_clip[1], path_info["width"])


def draw_world_details(screen, camera_x, camera_y, world_elements, game_state):
    """Draws details like grass and trees (sorted)."""
    if game_state == "overworld":
        camera_world_rect = pygame.Rect(camera_x, camera_y, SCREEN_WIDTH, SCREEN_HEIGHT)
        screen_rect_for_culling = screen.get_rect()
        loaded_sprites = world_elements.get("loaded_sprites", {}) # Get loaded sprites dict

        # Draw Grass Details
        grass_details = world_elements.get("grass_details", [])
        for detail in grass_details:
             # Check if detail rect exists and is valid
            if 'rect' in detail and isinstance(detail['rect'], pygame.Rect):
                if camera_world_rect.colliderect(detail['rect']):
                    detail_screen_rect = apply_camera_to_rect(detail['rect'], camera_x, camera_y)
                    # Check if the transformed rect is still on screen
                    if screen_rect_for_culling.colliderect(detail_screen_rect):
                         # Ensure color exists and is valid
                         color = detail.get('color', (0, 255, 0)) # Default to green if missing
                         pygame.draw.rect(screen, color, detail_screen_rect)

        # Draw Forest Trees (Sorted)
        forest_trees = world_elements.get("forest_trees", [])
        tree_sprite_info = loaded_sprites.get('tree')

        if tree_sprite_info and forest_trees: # Only proceed if sprite and trees exist
            # Sort trees by the bottom of their collider for correct draw order
            forest_trees_sorted = sorted(forest_trees, key=lambda t: t['collider'].bottom)
            tree_sprite = tree_sprite_info['surface']
            sprite_w = tree_sprite_info['width']
            sprite_h = tree_sprite_info['height']

            for tree in forest_trees_sorted:
                collider_rect = tree['collider']
                # Anchor sprite drawing based on the bottom-center of the collider
                anchor_world_x = collider_rect.centerx
                anchor_world_y = collider_rect.bottom
                # Calculate top-left corner for blitting
                sprite_world_draw_x = anchor_world_x - sprite_w // 2
                sprite_world_draw_y = anchor_world_y - sprite_h # Draw sprite above the anchor y
                # Bounding box for the visual sprite (used for culling)
                sprite_world_bbox = pygame.Rect(sprite_world_draw_x, sprite_world_draw_y, sprite_w, sprite_h)

                # Culling: Check if the sprite's bounding box is within the camera view
                if camera_world_rect.colliderect(sprite_world_bbox):
                    # Convert world draw coordinates to screen coordinates
                    draw_screen_x, draw_screen_y = apply_camera_to_point(sprite_world_draw_x, sprite_world_draw_y, camera_x, camera_y)
                    # Final Culling: Check if the sprite is actually visible on the screen surface
                    sprite_screen_rect = pygame.Rect(draw_screen_x, draw_screen_y, sprite_w, sprite_h)
                    if screen_rect_for_culling.colliderect(sprite_screen_rect):
                        screen.blit(tree_sprite, (draw_screen_x, draw_screen_y))


def draw_kingdom_structures(screen, camera_x, camera_y, world_elements):
    """Draws kingdom walls (ROTATED tiles), towers, gatehouses, and buildings, sorted by Y."""
    camera_world_rect = pygame.Rect(camera_x, camera_y, SCREEN_WIDTH, SCREEN_HEIGHT)
    screen_rect_for_culling = screen.get_rect()

    wall_tiles = world_elements.get("wall_tiles", []) # List of {'pos': (cx,cy), 'angle': a, 'sprite_key': k}
    kingdom_structures = world_elements.get("kingdom_structures", []) # List of {'base_rect': r} (Buildings)
    wall_towers = world_elements.get("wall_towers", [])         # List of {'base_rect': r}
    gatehouses = world_elements.get("gatehouses", [])           # List of {'base_rect': r}
    loaded_sprites = world_elements.get("loaded_sprites", {})

    drawable_items = [] # Combine all kingdom elements for Y-sorting

    # --- 1. Add Wall Tiles to Sort List ---
    wall_sprite_front_info = loaded_sprites.get('wall_front')
    wall_sprite_back_info = loaded_sprites.get('wall_back')
    # Use a dictionary mapping the keys used in generation to the loaded sprite info
    wall_surfaces = {}
    if wall_sprite_front_info:
        wall_surfaces['wall_front'] = wall_sprite_front_info
    if wall_sprite_back_info:
        wall_surfaces['wall_back'] = wall_sprite_back_info

    for tile_data in wall_tiles:
        sprite_key = tile_data['sprite_key']
        sprite_info = wall_surfaces.get(sprite_key) # Efficient lookup
        if sprite_info:
            # Use tile's center Y for sorting walls
            drawable_items.append({
                'type': 'wall_tile',
                'data': tile_data,          # Contains pos, angle, sprite_key
                'sprite_info': sprite_info, # Contains surface, width, height
                'y_sort': tile_data['pos'][1] # Sort by center y
            })

    # --- 2. Add Gatehouses to Sort List ---
    gatehouse_sprite_info = loaded_sprites.get('gatehouse')
    if gatehouse_sprite_info:
        for gh in gatehouses: # Loop will run 0 or 1 time
            drawable_items.append({
                'type': 'gatehouse',
                'data': gh, # Contains base_rect
                'sprite_info': gatehouse_sprite_info,
                'y_sort': gh['base_rect'].bottom # Sort by bottom of base collider
            })

    # --- 3. Add Wall Towers to Sort List ---
    tower_sprite_info = loaded_sprites.get('tower')
    if tower_sprite_info:
        for tower in wall_towers:
             drawable_items.append({
                'type': 'tower',
                'data': tower, # Contains base_rect
                'sprite_info': tower_sprite_info,
                'y_sort': tower['base_rect'].bottom # Sort by bottom of base collider
            })

    # --- 4. Add Buildings to Sort List ---
    building_sprite_info = loaded_sprites.get('building')
    if building_sprite_info:
        for structure in kingdom_structures:
             drawable_items.append({
                'type': 'building',
                'data': structure, # Contains base_rect
                'sprite_info': building_sprite_info,
                'y_sort': structure['base_rect'].bottom # Sort by bottom of base collider
            })

    # --- 5. Sort all items by Y-coordinate ---
    drawable_items.sort(key=lambda x: x['y_sort'])

    # --- 6. Draw Sorted Items ---
    for item in drawable_items:
        item_type = item['type']
        item_data = item['data']
        sprite_info = item['sprite_info']
        base_sprite_surface = sprite_info['surface'] # Original, unrotated surface

        if item_type == 'wall_tile':
            world_center_x, world_center_y = item_data['pos']
            angle = item_data['angle']
            sprite_key = item_data['sprite_key']

            # --- Rotate Wall Tile ---
            rotated_surface = pygame.transform.rotate(base_sprite_surface, angle)

            # Get the rect of the *rotated* surface and position its center
            rotated_rect = rotated_surface.get_rect(center=(world_center_x, world_center_y))

            # Use the rotated rect's bounding box for culling
            sprite_world_bbox = rotated_rect

            # Get the top-left position for blitting the rotated surface
            draw_world_x = rotated_rect.left
            draw_world_y = rotated_rect.top
            surface_to_blit = rotated_surface

        else: # Buildings, Towers, Gatehouses (no rotation needed here)
            base_rect = item_data['base_rect']
            sprite_w = sprite_info['width']
            sprite_h = sprite_info['height']
            # Anchor bottom-center of base_rect
            anchor_world_x = base_rect.centerx
            anchor_world_y = base_rect.bottom
            # Calculate top-left corner for blitting
            draw_world_x = anchor_world_x - sprite_w // 2
            draw_world_y = anchor_world_y - sprite_h
            # Bounding box for culling
            sprite_world_bbox = pygame.Rect(draw_world_x, draw_world_y, sprite_w, sprite_h)
            surface_to_blit = base_sprite_surface # Blit original surface

        # Common drawing logic (culling and blitting)
        if camera_world_rect.colliderect(sprite_world_bbox):
            draw_screen_x, draw_screen_y = apply_camera_to_point(draw_world_x, draw_world_y, camera_x, camera_y)

            # Use the calculated screen coordinates for the final blit position rect
            # Note: For rotated walls, the blit rect is based on the rotated surface size
            blit_rect_screen = surface_to_blit.get_rect(topleft=(draw_screen_x, draw_screen_y))

            # Final Culling: Check if the screen rect intersects the screen
            if screen_rect_for_culling.colliderect(blit_rect_screen):
                screen.blit(surface_to_blit, blit_rect_screen.topleft)


# --- END OF FILE drawing.py ---