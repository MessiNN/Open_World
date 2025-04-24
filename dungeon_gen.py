import random
import pygame

pygame.init()


# <<< ADD Dungeon Generator Constants HERE >>>
# Grid and Tile Settings for Dungeon
DUNGEON_TILE_SIZE = 16      # Pixel size of each dungeon tile (adjust for desired zoom)
DUNGEON_GRID_WIDTH = 100    # Number of tiles horizontally in dungeon
DUNGEON_GRID_HEIGHT = 80    # Number of tiles vertically in dungeon

# Dungeon Generation Parameters
DUNGEON_NUM_ROOM_ATTEMPTS = 150
DUNGEON_MIN_ROOM_SIZE = 6
DUNGEON_MAX_ROOM_SIZE = 12
DUNGEON_ROOM_BUFFER = 3
DUNGEON_PATH_WIDTH = 3

# Tile Types (represented as integers)
TILE_WALL = 0
TILE_FLOOR = 1

# Dungeon Colors
DUNGEON_COLOR_WALL = (40, 40, 60)
DUNGEON_COLOR_FLOOR = (90, 90, 110)
DUNGEON_COLOR_ROOM_DEBUG = (0, 255, 0, 100) # Optional debug
DUNGEON_COLOR_CORRIDOR_DEBUG = (0, 0, 255) # Optional debug

# --- Dungeon Generator Class ---
class DungeonGenerator:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = []
        self.rooms = [] # List to store pygame.Rect objects for rooms (in GRID coordinates)

    def _initialize_grid(self):
        """Creates a grid filled entirely with walls."""
        self.grid = [[TILE_WALL for _ in range(self.width)] for _ in range(self.height)]
        self.rooms = []

    def _create_room(self, room_rect):
        """Carves out a room in the grid, changing walls to floors."""
        for y in range(room_rect.top, room_rect.bottom):
            for x in range(room_rect.left, room_rect.right):
                if 0 <= x < self.width and 0 <= y < self.height:
                    self.grid[y][x] = TILE_FLOOR

    def _create_h_tunnel(self, x1, x2, y, path_width): # Add path_width parameter
        """Carves a horizontal tunnel of a given width."""
        start_x = min(x1, x2)
        end_x = max(x1, x2)
        # Calculate vertical extent of the tunnel based on center y and width
        y_start = y - path_width // 2
        y_end = y_start + path_width # Exclusive end for range

        for current_x in range(start_x, end_x + 1): # Iterate horizontally
            for current_y in range(y_start, y_end):   # Iterate vertically for thickness
                # Boundary check before writing to grid
                if 0 <= current_x < self.width and 0 <= current_y < self.height:
                    self.grid[current_y][current_x] = TILE_FLOOR

    def _create_v_tunnel(self, y1, y2, x, path_width): # Add path_width parameter
        """Carves a vertical tunnel of a given width."""
        start_y = min(y1, y2)
        end_y = max(y1, y2)
        # Calculate horizontal extent of the tunnel based on center x and width
        x_start = x - path_width // 2
        x_end = x_start + path_width # Exclusive end for range

        for current_y in range(start_y, end_y + 1): # Iterate vertically
            for current_x in range(x_start, x_end):   # Iterate horizontally for thickness
                 # Boundary check before writing to grid
                if 0 <= current_x < self.width and 0 <= current_y < self.height:
                    self.grid[current_y][current_x] = TILE_FLOOR

    def _place_rooms(self):
        """Randomly places non-overlapping rooms on the grid."""
        for _ in range(DUNGEON_NUM_ROOM_ATTEMPTS): # Use dungeon constant
            w = random.randint(DUNGEON_MIN_ROOM_SIZE, DUNGEON_MAX_ROOM_SIZE) # Use dungeon constant
            h = random.randint(DUNGEON_MIN_ROOM_SIZE, DUNGEON_MAX_ROOM_SIZE) # Use dungeon constant
            x = random.randint(1, self.width - w - 1)
            y = random.randint(1, self.height - h - 1)
            new_room = pygame.Rect(x, y, w, h)
            overlaps = False
            check_rect = new_room.inflate(DUNGEON_ROOM_BUFFER * 2, DUNGEON_ROOM_BUFFER * 2) # Use dungeon constant
            for other_room in self.rooms:
                if check_rect.colliderect(other_room):
                    overlaps = True
                    break
            if not overlaps:
                self._create_room(new_room)
                self.rooms.append(new_room) # Store rect in GRID coordinates

    def _connect_rooms(self):
        """Connects rooms sequentially with L-shaped corridors."""
        if not self.rooms: return

        # Ensure path width is at least 1
        path_width = max(1, DUNGEON_PATH_WIDTH) # Use the constant

        sorted_rooms = sorted(self.rooms, key=lambda r: (r.centery, r.centerx))
        for i in range(len(sorted_rooms) - 1):
            center1 = sorted_rooms[i].center
            center2 = sorted_rooms[i+1].center

            # Pass the path_width to the tunnel functions
            if random.randint(0, 1) == 0:
                self._create_h_tunnel(center1[0], center2[0], center1[1], path_width) # Pass width
                self._create_v_tunnel(center1[1], center2[1], center2[0], path_width) # Pass width
            else:
                self._create_v_tunnel(center1[1], center2[1], center1[0], path_width) # Pass width
                self._create_h_tunnel(center1[0], center2[0], center2[1], path_width) # Pass width

    def generate_dungeon(self):
        """Generates the full dungeon layout."""
        self._initialize_grid()
        self._place_rooms()
        if not self.rooms:
             print("Warning: No rooms placed in dungeon generation!")
             # Optionally force a small room if none generated
             # fallback_room = pygame.Rect(self.width // 2 - 2, self.height // 2 - 2, 4, 4)
             # self._create_room(fallback_room)
             # self.rooms.append(fallback_room)
        else:
            self._connect_rooms()
        return self.grid, self.rooms # Return grid data and list of room Rects (in grid coords)