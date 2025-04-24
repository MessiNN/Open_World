# --- START OF FILE loading.py ---
import pygame
import sys
import NETconfig as network

# Import necessary components from other modules
import world_struct as world_struct_stable
import combat_mech as combat_mech_stable
import npc_system as npc_system_stable


from asset.assets import *
from paths import *


TOTAL_LOADING_STEPS = 17 # Keep track of loading steps

def draw_loading_progress(surface, current_step, total_steps, message="Loading..."):
    """Draws the loading screen with progress bar and text."""
    screen_width = surface.get_width()
    screen_height = surface.get_height()

    # --- Clear Screen ---
    surface.fill((20, 20, 40)) # Dark blue background

    # --- Progress Bar ---
    bar_width = screen_width * 0.6
    bar_height = 30
    bar_x = (screen_width - bar_width) / 2
    bar_y = screen_height * 0.6
    bar_bg_color = (60, 60, 80)
    bar_fg_color = (100, 180, 255)

    # Calculate progress
    progress = 0.0
    if total_steps > 0:
        progress = min(1.0, max(0.0, current_step / total_steps))

    # Draw background bar
    pygame.draw.rect(surface, bar_bg_color, (bar_x, bar_y, bar_width, bar_height))
    # Draw foreground bar
    fg_width = bar_width * progress
    pygame.draw.rect(surface, bar_fg_color, (bar_x, bar_y, fg_width, bar_height))
    # Draw border
    pygame.draw.rect(surface, (200, 200, 220), (bar_x, bar_y, bar_width, bar_height), 2)

    # --- Text ---
    font = None
    try:
        # Use a slightly larger font for loading text
        font = pygame.font.SysFont(None, 36)
    except Exception as e:
        print(f"Could not load font for loading screen: {e}")
        # Font failed, can't draw text

    if font:
        # Loading Message
        text_surf = font.render(message, True, (220, 220, 240))
        text_rect = text_surf.get_rect(center=(screen_width / 2, screen_height * 0.5))
        surface.blit(text_surf, text_rect)

        # Percentage Text
        percent_text = f"{int(progress * 100)}%"
        percent_surf = font.render(percent_text, True, (220, 220, 240))
        percent_rect = percent_surf.get_rect(center=(screen_width / 2, bar_y + bar_height / 2))
        surface.blit(percent_surf, percent_rect)

    # --- Update Display ---
    pygame.display.flip()

    # --- Keep Window Responsive ---
    pygame.event.pump() # Process internal events


def run_loading_screen(surface, game_state, mixer_initialized):
    """
    Handles the loading process and updates the loading screen.
    Returns the loaded world_data, collision_quadtree, effective dimensions,
    loaded player animations, enemy animations, and initialized managers.
    """

    # Define variables to store loaded data
    world_data = None
    collision_quadtree = None
    effective_world_width = 0
    effective_world_height = 0
    player_idle_frames, player_walk_frames, player_attack_frames, player_hurt_frames, player_death_frames = [None]*5
    player_frame_dims = None
    all_enemy_animations = {}
    combat_manager = None
    npc_manager = None

    current_step = 0
    draw_loading_progress(surface, current_step, TOTAL_LOADING_STEPS, "Initializing...")
    pygame.time.wait(100) # Small pause to ensure first draw

    # --- Step 1 & 2: World Loading/Generation ---
    print("Loading Step: World Data...")
    # Note: collision_quadtree is created but not populated yet here

    world_data, collision_quadtree = world_struct_stable.load_or_generate_world()
    
    current_step += 2 # Count as 2 steps (load/gen + sprite loading inside)
    draw_loading_progress(surface, current_step, TOTAL_LOADING_STEPS, "World Generated...")
    pygame.time.wait(50)

    # --- Step 3-7: Player Animations ---
    print("Loading Step: Player Animations...")
    player_idle_frames, player_frame_dims = load_sprite_sheet(SPRITE_SHEET_PLAYER_IDLE_FILENAME, NUM_PLAYER_IDLE_FRAMES)
    current_step += 1; draw_loading_progress(surface, current_step, TOTAL_LOADING_STEPS, "Loading Player...")
    player_walk_frames, _ = load_sprite_sheet(SPRITE_SHEET_PLAYER_WALK_FILENAME, NUM_PLAYER_WALK_FRAMES)
    current_step += 1; draw_loading_progress(surface, current_step, TOTAL_LOADING_STEPS, "Loading Player...")
    player_attack_frames, _ = load_sprite_sheet(SPRITE_SHEET_PLAYER_ATTACK_FILENAME, NUM_PLAYER_ATTACK_FRAMES)
    current_step += 1; draw_loading_progress(surface, current_step, TOTAL_LOADING_STEPS, "Loading Player...")
    player_hurt_frames, _ = load_sprite_sheet(SPRITE_SHEET_PLAYER_HURT_FILENAME, NUM_PLAYER_HURT_FRAMES)
    current_step += 1; draw_loading_progress(surface, current_step, TOTAL_LOADING_STEPS, "Loading Player...")
    player_death_frames, _ = load_sprite_sheet(SPRITE_SHEET_PLAYER_DEATH_FILENAME, NUM_PLAYER_DEATH_FRAMES)
    current_step += 1; draw_loading_progress(surface, current_step, TOTAL_LOADING_STEPS, "Player Assets Loaded...")
    pygame.time.wait(50)

    # Check essential player frames
    if not player_idle_frames or not player_frame_dims:
        print("FATAL: Failed to load essential player idle frames during loading screen. Exiting.")
        pygame.quit(); sys.exit()
    # Store player frames in a dict for easier return
    player_animations = {
        'idle': player_idle_frames, 'walk': player_walk_frames, 'attack': player_attack_frames,
        'hurt': player_hurt_frames, 'death': player_death_frames, 'dims': player_frame_dims
    }

    # --- Step 8-12: Enemy Animations (Orc Example) ---
    print("Loading Step: Enemy Animations...")
    
    # Load Orc Animations
    orc_idle_frames, orc_frame_dims = load_sprite_sheet(SPRITE_SHEET_ORC_IDLE_FILENAME, NUM_ORC_IDLE_FRAMES)
    current_step += 1; draw_loading_progress(surface, current_step, TOTAL_LOADING_STEPS, "Loading Enemies...")
    orc_walk_frames, _ = load_sprite_sheet(SPRITE_SHEET_ORC_WALK_FILENAME, NUM_ORC_WALK_FRAMES)
    current_step += 1; draw_loading_progress(surface, current_step, TOTAL_LOADING_STEPS, "Loading Enemies...")
    orc_attack_frames, _ = load_sprite_sheet(SPRITE_SHEET_ORC_ATTACK_FILENAME, NUM_ORC_ATTACK_FRAMES)
    current_step += 1; draw_loading_progress(surface, current_step, TOTAL_LOADING_STEPS, "Loading Enemies...")
    orc_hurt_frames, _ = load_sprite_sheet(SPRITE_SHEET_ORC_HURT_FILENAME, NUM_ORC_HURT_FRAMES)
    current_step += 1; draw_loading_progress(surface, current_step, TOTAL_LOADING_STEPS, "Loading Enemies...")
    orc_death_frames, _ = load_sprite_sheet(SPRITE_SHEET_ORC_DEATH_FILENAME, NUM_ORC_DEATH_FRAMES)
    current_step += 1; draw_loading_progress(surface, current_step, TOTAL_LOADING_STEPS, "Enemy Assets Loaded...")
    pygame.time.wait(50)

    # Store Orc animations if loaded successfully
    if all([orc_idle_frames, orc_walk_frames, orc_attack_frames, orc_hurt_frames, orc_death_frames, orc_frame_dims]):
        all_enemy_animations["Sword_Orc"] = {
            'idle': orc_idle_frames, 'walk': orc_walk_frames, 'attack': orc_attack_frames,
            'hurt': orc_hurt_frames, 'death': orc_death_frames, 'dims': orc_frame_dims
        }
    else:
        print("WARNING: Failed to load one or more Orc animations.")
    # (Add loading for other enemies here, incrementing current_step for each)

    # --- Step 13: Load Music ---
    print("Loading Step: Music...")
    if mixer_initialized:
        try:
            pygame.mixer.music.load(MUSIC_FILE_PATH)
            pygame.mixer.music.set_volume(MUSIC_VOLUME)
            # Don't play yet, play after loading finishes
        except pygame.error as e:
            print(f"Error loading music file during loading screen: {e}")
    current_step += 1; draw_loading_progress(surface, current_step, TOTAL_LOADING_STEPS, "Audio Loaded...")
    pygame.time.wait(50)

    # --- Step 14: Determine World Size & Populate Quadtree ---
    print("Loading Step: Quadtree Population...")
    if game_state == "dungeon":
        dungeon_world_width = world_struct_stable.DUNGEON_GRID_WIDTH * world_struct_stable.DUNGEON_TILE_SIZE
        dungeon_world_height = world_struct_stable.DUNGEON_GRID_HEIGHT * world_struct_stable.DUNGEON_TILE_SIZE
        dungeon_boundary_rect = pygame.Rect(0, 0, dungeon_world_width, dungeon_world_height)
        collision_quadtree.boundary = dungeon_boundary_rect
        world_struct_stable.populate_quadtree_with_dungeon(collision_quadtree, world_data["dungeon_grid"])
        effective_world_width = dungeon_world_width
        effective_world_height = dungeon_world_height
    elif game_state == "overworld":
        overworld_boundary_rect = pygame.Rect(0, 0, world_struct_stable.WORLD_WIDTH, world_struct_stable.WORLD_HEIGHT)
        collision_quadtree.boundary = overworld_boundary_rect
        world_struct_stable.populate_quadtree_with_overworld(collision_quadtree, world_data["colliders"])
        effective_world_width = world_struct_stable.WORLD_WIDTH
        effective_world_height = world_struct_stable.WORLD_HEIGHT
    else: # Default case or error
        print(f"ERROR: Unknown game_state '{game_state}'. Defaulting to overworld bounds.")
        overworld_boundary_rect = pygame.Rect(0, 0, world_struct_stable.WORLD_WIDTH, world_struct_stable.WORLD_HEIGHT)
        collision_quadtree.boundary = overworld_boundary_rect
        world_struct_stable.populate_quadtree_with_overworld(collision_quadtree, world_data["colliders"])
        effective_world_width = world_struct_stable.WORLD_WIDTH
        effective_world_height = world_struct_stable.WORLD_HEIGHT
    current_step += 1; draw_loading_progress(surface, current_step, TOTAL_LOADING_STEPS, "Optimizing World...")
    pygame.time.wait(50)

    # --- Step 15 & 16: Initialize Managers ---
    # <<< NETWORK: Pass network_players dict to managers so they know about all players >>>
    print("Loading Step: Preparing Managers...")
    combat_manager = combat_mech_stable.CombatManager(world_data, collision_quadtree, world_struct_stable.is_point_in_polygon, all_enemy_animations, network.network_players)
    npc_manager = npc_system_stable.NPCManager(world_data, world_struct_stable.SCREEN_HEIGHT, world_struct_stable.SCREEN_WIDTH, network.network_players, network.is_host)

    # Don't spawn here, spawn happens in main after player is created
    current_step += 2; draw_loading_progress(surface, current_step, TOTAL_LOADING_STEPS, "Preparing Inhabitants...")
    pygame.time.wait(50)

    # --- Step 17: Finalization ---
    print("Loading Step: Finalizing...")
    current_step += 1; draw_loading_progress(surface, current_step, TOTAL_LOADING_STEPS, "Ready!")
    pygame.time.wait(500) # Show "Ready!" for a moment

    return (world_data, collision_quadtree,
            effective_world_width, effective_world_height,
            all_enemy_animations, player_animations,
            combat_manager, npc_manager)
    


# --- END OF FILE loading.py ---