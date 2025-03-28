# -*- coding: utf-8 -*-
"""
Simplified Mindustry-like Proof of Concept - Attempt 15 (Settings Update)
By: The Best Python Programmer (as per request)
Date: 2025-03-31
Version: 15.0 (Resolution & Network Interval Settings)

Controls (In-Game):
- WASD: Move Player Character
- Mouse Left Click: Place selected building (within player radius)
- Mouse Right Click: Delete building under cursor
- Keys 1-8: Select building (See UI)
- Key 0: Deselect building
- Key 'R': Rotate selected Conveyor preview (BEFORE placing)
- Key 'U': Upgrade building under cursor (requires resources, must have nothing selected [Key 0])
- ESC: Return to Main Menu (or Quit from Menu)

Objective: Survive waves. Manage Copper, Coal, and Power. Upgrade defenses & production. (Multiplayer: Cooperate!)
"""
import pygame
import sys
import math
import random
import time
import socket
import select
import json
import threading
import glob
import os
from collections import deque

# --- Constants ---
# Screen & UI
AVAILABLE_RESOLUTIONS = [
    (800, 600),
    (1024, 768),
    (1280, 768), # Default
    (1366, 768),
    (1600, 900),
    (1920, 1080),
]
DEFAULT_RESOLUTION_INDEX = 2

# Music Constants
MAIN_MENU_MUSIC_FILE = 'main_menu.mp3'
GAME_MUSIC_FILES_PATTERN = 'in_game*.mp3'
MUSIC_END_EVENT = pygame.USEREVENT + 1
MUSIC_FADE_MS = 500
DEFAULT_MUSIC_VOLUME = 0.6 # Volume from 0.0 to 1.0

#UI
CONFIG_FILENAME = "config.json"
SAVE_FILENAME_SP = "save_sp.json"
SAVE_FILENAME_HOST = "save_host.json"
UI_HEIGHT = 140
FPS = 60
GAME_TITLE = "Mindurka Reworked"

# Grid
TILE_SIZE = 32
# Grid/Map dimensions are now calculated in Game.__init__ based on screen size

# Colors
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_GRAY = (128, 128, 128)
COLOR_DARK_GRAY = (50, 50, 50)
COLOR_GREEN = (0, 255, 0)
COLOR_RED = (255, 0, 0)
COLOR_BLUE = (0, 0, 255)
COLOR_YELLOW = (255, 255, 0)
COLOR_BROWN = (139, 69, 19)
COLOR_COPPER = (184, 115, 51)
COLOR_COAL = (60, 60, 60)
COLOR_TURRET = [(100, 100, 150), (120, 120, 180), (150, 150, 220)] # T1, T2, T3
COLOR_WALL = (150, 150, 150)
COLOR_ENEMY = (200, 50, 50)
COLOR_PROJECTILE = (255, 165, 0)
COLOR_UI_BG = (30, 30, 30)
COLOR_UI_TEXT = (200, 200, 200)
COLOR_UI_HEADER = (150, 150, 255)
COLOR_PLAYER = COLOR_YELLOW
COLOR_INVALID_RADIUS = (100, 100, 255, 120)
COLOR_GENERATOR = (80, 180, 80)
COLOR_POLE = (200, 200, 100)
COLOR_POWER_LINE = COLOR_YELLOW
COLOR_BATTERY = (90, 90, 200)
COLOR_BATTERY_CHARGE = COLOR_YELLOW
COLOR_RECONSTRUCTOR = (200, 100, 200)
COLOR_REPAIR_AURA = (*COLOR_GREEN[:3], 50)
COLOR_DRILL = [(139, 69, 19), (160, 90, 40), (180, 110, 60)] # T1, T2, T3
COLOR_CONVEYOR = [(128, 128, 128), (150, 150, 150), (180, 180, 180)] # T1, T2, T3
COLOR_MENU_BUTTON = (80, 80, 150)
COLOR_MENU_BUTTON_HOVER = (120, 120, 200)
COLOR_MENU_BUTTON_DISABLED = (70, 70, 70)
COLOR_MENU_TITLE = COLOR_UI_HEADER
COLOR_PLAYER_OPTIONS = [
    COLOR_YELLOW, (0, 200, 255), (255, 100, 100), (100, 255, 100), (255, 0, 255),
    (255, 165, 0), (128, 0, 128), (0, 128, 128), (255, 255, 255), (100, 100, 100),
    (0, 0, 0)
]
COLOR_INPUT_BOX_ACTIVE = COLOR_WHITE
COLOR_INPUT_BOX_INACTIVE = COLOR_GRAY
COLOR_SETTINGS_BG = COLOR_DARK_GRAY
COLOR_SELECTED_SWATCH_BORDER = COLOR_WHITE
COLOR_NETWORK_STATUS = COLOR_YELLOW
COLOR_CHAT_BG = (*COLOR_DARK_GRAY, 180)
COLOR_CHAT_TEXT = COLOR_WHITE
COLOR_CHAT_INPUT_BG = (*COLOR_UI_BG, 220)
COLOR_SLIDER_TRACK = COLOR_GRAY
COLOR_SLIDER_HANDLE = COLOR_WHITE
COLOR_SLIDER_HANDLE_DRAG = COLOR_YELLOW

# Resource Types Enum
RES_COPPER = 'copper'
RES_COAL = 'coal'

# Game Settings
STARTING_COPPER = 200
STARTING_COAL = 100
CORE_HP = 1500
DELETE_REFUND_RATIO = 0.5
PLAYER_SPEED = 5.0 * TILE_SIZE
PLAYER_BUILD_RADIUS = 8 * TILE_SIZE

# Enemy/Wave Settings
ENEMY_SPAWN_RATE = 3.0
ENEMY_START_HP = 50
ENEMY_HP_INCREASE_PER_WAVE = 20
ENEMY_SPEED = 1.7 * TILE_SIZE
ENEMY_DAMAGE = 20
ENEMY_ATTACK_COOLDOWN = 0.9
WAVE_DURATION = 40
WAVE_COOLDOWN = 30
MAX_WAVES = 20

# Building Stats & Upgrades
MAX_TIER = 3
DRILL_COST = {RES_COPPER: 15}
DRILL_STATS = [(1.8, 100), (1.4, 140), (1.0, 180)]
DRILL_UPGRADE_COST = { 2: {RES_COPPER: 40}, 3: {RES_COPPER: 75, RES_COAL: 20} }
DRILL_OUTPUT_COOLDOWN = 0.1
CONVEYOR_COST = {RES_COPPER: 5}
CONVEYOR_STATS = [(0.8, 50, 1), (0.55, 70, 2), (0.35, 90, 3)]
CONVEYOR_UPGRADE_COST = { 2: {RES_COPPER: 15}, 3: {RES_COPPER: 30, RES_COAL: 5} }
CONVEYOR_ITEM_SPACING = 0.3
TURRET_COST = {RES_COPPER: 30}
TURRET_STATS = [ (5.0 * TILE_SIZE, 30, 0.45, 150), (5.5 * TILE_SIZE, 40, 0.40, 220), (6.0 * TILE_SIZE, 55, 0.30, 300) ]
TURRET_UPGRADE_COST = { 2: {RES_COPPER: 50, RES_COAL: 20}, 3: {RES_COPPER: 80, RES_COAL: 50} }
TURRET_AMMO_CAPACITY = 12
TURRET_AMMO_CONSUMPTION = 1
PROJECTILE_SPEED = 7.5 * TILE_SIZE
TURRET_T3_POWER_CONSUMPTION = 15.0
WALL_COST = {RES_COPPER: 10}
WALL_HP = 400
COALGENERATOR_COST = {RES_COPPER: 40, RES_COAL: 25}
COALGENERATOR_HP = 200
COALGENERATOR_INPUT_CAP = 10
COALGENERATOR_CONSUMPTION_RATE = 3.0
COALGENERATOR_POWER_OUTPUT = 30.0
POWERPOLE_COST = {RES_COPPER: 15}
POWERPOLE_HP = 80
POWER_RADIUS = 5 * TILE_SIZE
POWER_SEARCH_DEPTH_LIMIT = 15
POWER_NETWORK_STATS_UPDATE_INTERVAL = 0.3
BATTERY_COST = {RES_COPPER: 50, RES_COAL: 15}
BATTERY_HP = 250
BATTERY_CAPACITY = 3000
BATTERY_CHARGE_RATE = 40.0
BATTERY_DISCHARGE_RATE = 40.0
RECONSTRUCTOR_COST = {RES_COPPER: 70, RES_COAL: 40}
RECONSTRUCTOR_HP = 300
RECONSTRUCTOR_POWER_CONSUMPTION = 10.0
RECONSTRUCTOR_REPAIR_RATE = 8.0
RECONSTRUCTOR_REPAIR_RADIUS = 2.5 * TILE_SIZE

# Building Types Enum & Orientations
BUILDING_NONE, BUILDING_DRILL, BUILDING_CONVEYOR, BUILDING_TURRET, BUILDING_WALL, BUILDING_COALGENERATOR, BUILDING_POWERPOLE, BUILDING_CORE, BUILDING_RESOURCE, BUILDING_BATTERY, BUILDING_RECONSTRUCTOR = range(11)
ORIENTATIONS = [(0, -1), (1, 0), (0, 1), (-1, 0)]
NORTH, EAST, SOUTH, WEST = 0, 1, 2, 3

# Application States
STATE_MAIN_MENU = 0
STATE_PLAYING_SP = 1
STATE_SETTINGS = 2
STATE_HOSTING = 3
STATE_JOINING = 4
STATE_PLAYING_MP_CLIENT = 5
STATE_SHOW_IP = 6

# Network Settings
DEFAULT_PORT = 5555
MAX_PLAYERS = 10
DEFAULT_NETWORK_UPDATE_INTERVAL = 0.05 # Default value (20 Hz)
MIN_NETWORK_UPDATE_INTERVAL = 0.01   # Limit (100 Hz)
MAX_NETWORK_UPDATE_INTERVAL = 0.2    # Limit (5 Hz)
BUFFER_SIZE = 4096
HEADER_LENGTH = 10

# --- Global Fonts (initialized later) ---
font_tiny = None
font_small = None
font_medium = None
font_large = None
font_title = None

# --- Helper Functions ---
def init_fonts():
    """Initializes global font objects."""
    global font_tiny, font_small, font_medium, font_large, font_title
    try:
        font_tiny = pygame.font.Font(None, 16)
        font_small = pygame.font.Font(None, 18)
        font_medium = pygame.font.Font(None, 24)
        font_large = pygame.font.Font(None, 72)
        font_title = pygame.font.Font(None, 80)
    except Exception as e:
        print(f"FATAL: Font loading error: {e}")
        # Provide basic fallbacks
        if not font_small: font_small = pygame.font.Font(None, 18)
        if not font_medium: font_medium = pygame.font.Font(None, 24)
        if not font_tiny: font_tiny = pygame.font.Font(None, 16)
        if not font_large: font_large = pygame.font.Font(None, 72)
        if not font_title: font_title = pygame.font.Font(None, 80)

def draw_text(surface, text, size, x, y, color=COLOR_WHITE, align="topleft"):
    """Draws text on a surface using globally loaded fonts."""
    font = None
    try:
        if size <= 16:
            font = font_tiny
        elif size <= 20:
            font = font_small
        elif size <= 30:
            font = font_medium
        elif size <= 72:
            font = font_large
        else:
            font = font_title

        if not font:
            font = pygame.font.Font(None, int(size))
            print(f"WARN: Using fallback font for size {size}.")
    except Exception as e:
        print(f"FONT ERR: {e}. Size:{size}, Text:{text}")
        font = pygame.font.Font(None, int(size))

    try:
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()
        setattr(text_rect, align, (x, y))
        surface.blit(text_surface, text_rect)
    except Exception as e:
         print(f"TEXT RENDER ERR: {e}. Size:{size}, Text:{text}, Color:{color}")

def world_to_grid(x, y):
    return int(x // TILE_SIZE), int(y // TILE_SIZE)

def grid_to_world(gx, gy):
    return gx * TILE_SIZE, gy * TILE_SIZE

def grid_to_world_center(gx, gy):
    return (gx + 0.5) * TILE_SIZE, (gy + 0.5) * TILE_SIZE

def distance_sq(x1, y1, x2, y2):
    dx = x1 - x2
    dy = y1 - y2
    return dx * dx + dy * dy

def distance(x1, y1, x2, y2):
    return math.sqrt(distance_sq(x1, y1, x2, y2)) + 1e-9

# --- Network Helper Functions ---
def encode_message(data):
    """Encodes a dictionary to JSON bytes with a header."""
    try:
        message = json.dumps(data).encode('utf-8')
        header = f"{len(message):<{HEADER_LENGTH}}".encode('utf-8')
        return header + message
    except TypeError as e:
        print(f"Error encoding message: {e}, Data causing error: {data}")
        if isinstance(data, dict):
            for k in data.keys():
                if not isinstance(k, (str, int, float, bool)) and k is not None:
                    print(f" -> Problematic key type: {type(k)} for key: {k}")
                    if isinstance(k, tuple) and 'base_terrain' in data and data.get('base_terrain') is not None and k in data['base_terrain']:
                         print(" -> Likely caused by tuple key in 'base_terrain'. Fix applied in get_full_snapshot.")
                    break
        return None
    except Exception as e:
        print(f"Unexpected error encoding message: {e}, Data: {data}")
        return None

def receive_message(sock):
    """Receives a complete message based on the header length."""
    try:
        header_data = sock.recv(HEADER_LENGTH)
        if not header_data:
            return None # Connection closed
        message_length = int(header_data.decode('utf-8').strip())

        chunks = []
        bytes_recd = 0
        while bytes_recd < message_length:
            chunk = sock.recv(min(message_length - bytes_recd, BUFFER_SIZE))
            if not chunk:
                raise ConnectionError("Socket connection broken while receiving message body")
            chunks.append(chunk)
            bytes_recd += len(chunk)

        message_data = b''.join(chunks)
        return json.loads(message_data.decode('utf-8'))
    except (ValueError, json.JSONDecodeError) as e:
        print(f"Error decoding received data: {e}")
        return None
    except ConnectionResetError:
        print("Receive Error: Connection reset by peer.")
        return None
    except ConnectionAbortedError:
        print("Receive Error: Connection aborted.")
        return None
    except socket.error as e:
        # Ignore non-blocking errors
        if e.errno != 10035 and e.errno != 11: # WSAEWOULDBLOCK / EAGAIN
            print(f"Socket Receive Error: {e}")
        return None # Return None for blocking errors too, as data is not fully received
    except Exception as e:
        print(f"Unexpected Receive Error: {e}")
        return None

def get_local_ip():
    """Tries to get the local IP address for display."""
    s = None
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        if s:
            s.close()
    return ip

# --- Player Class ---
class Player:
    def __init__(self, start_x, start_y, player_id, name="Player", color_index=0):
        self.player_id = player_id
        self.world_x = float(start_x)
        self.world_y = float(start_y)
        self.radius = TILE_SIZE * 0.4
        self.speed = PLAYER_SPEED
        self.move_x = 0
        self.move_y = 0
        self.name = name
        self.color_index = color_index
        self.color = COLOR_PLAYER_OPTIONS[color_index % len(COLOR_PLAYER_OPTIONS)]
        self.last_input_processed = 0

    def update(self, dt, game_instance=None):
        """Updates player position based on movement state and delta time."""
        dx = self.move_x
        dy = self.move_y
        mag_sq = dx * dx + dy * dy

        if mag_sq > 1e-9:
            mag = math.sqrt(mag_sq)
            norm_dx = dx / mag
            norm_dy = dy / mag
        else:
            norm_dx = 0
            norm_dy = 0

        potential_x = self.world_x + norm_dx * self.speed * dt
        potential_y = self.world_y + norm_dy * self.speed * dt

        # Use map dimensions from game instance if available for clamping
        map_width = game_instance.map_width_px if game_instance else 10000
        map_height = game_instance.map_height_px if game_instance else 10000

        self.world_x = max(self.radius, min(potential_x, map_width - self.radius))
        self.world_y = max(self.radius, min(potential_y, map_height - self.radius))

    def draw(self, surface):
        """Draws the player character and name."""
        pos_x = int(self.world_x)
        pos_y = int(self.world_y)
        rad = int(self.radius)
        pygame.draw.circle(surface, self.color, (pos_x, pos_y), rad)
        pygame.draw.circle(surface, COLOR_BLACK, (pos_x, pos_y), rad, 1)

        if self.name and font_small:
            name_y_offset = rad + 4
            draw_text(surface, self.name, 18, pos_x, pos_y - name_y_offset, COLOR_WHITE, align="midbottom")

    def get_state(self):
        """Returns a serializable dictionary representing the player's state."""
        return {
            'id': self.player_id,
            'x': self.world_x,
            'y': self.world_y,
            'name': self.name,
            'color_idx': self.color_index,
        }

    def apply_state(self, state_data):
        """Updates the player's state from a received dictionary (Client-side)."""
        self.world_x = state_data.get('x', self.world_x)
        self.world_y = state_data.get('y', self.world_y)
        self.name = state_data.get('name', self.name)
        new_color_index = state_data.get('color_idx', self.color_index)
        if new_color_index != self.color_index:
            self.color_index = new_color_index
            self.color = COLOR_PLAYER_OPTIONS[self.color_index % len(COLOR_PLAYER_OPTIONS)]

# --- Structure Classes (Serialization Added) ---
class Structure:
    def __init__(self, gx, gy, hp, cost_dict, color, b_type):
        self.grid_x = gx
        self.grid_y = gy
        self.world_x, self.world_y = grid_to_world(gx, gy)
        self.center_x, self.center_y = grid_to_world_center(gx, gy)
        self.max_hp = hp
        self.hp = hp
        self.cost = cost_dict
        self.color = color
        self.building_type = b_type
        self.destroyed = False
        self.is_power_node = False
        self.is_power_source = False
        self.is_power_storage = False
        self.is_power_consumer = False
        self.power_consumption = 0
        self.is_on_grid = False
        self.is_powered = False
        self.power_source_node = None
        self.connected_nodes_coords = []
        self.tier = 1
        self.max_tier = 1
        self.upgrade_cost = {}
        self.network_id = f"{gx}_{gy}_{b_type}"

    def update(self, game):
        pass

    def client_update(self, dt):
        pass

    def draw(self, surface):
        rect = pygame.Rect(self.world_x, self.world_y, TILE_SIZE, TILE_SIZE)
        display_color = self.color
        if isinstance(self.color, list):
             try:
                 display_color = self.color[self.tier - 1]
             except IndexError:
                 display_color = self.color[-1]
        pygame.draw.rect(surface, display_color, rect)
        pygame.draw.rect(surface, COLOR_BLACK, rect, 1)
        self.draw_hp_bar(surface)
        if self.is_power_consumer and self.is_powered:
            px = self.world_x + TILE_SIZE - 5
            py = self.world_y + 5
            pygame.draw.circle(surface, COLOR_YELLOW, (int(px), int(py)), 3)

    def draw_hp_bar(self, surface):
        if self.hp < self.max_hp and self.max_hp > 0:
            ratio = max(0.0, min(1.0, self.hp / self.max_hp))
            bar_w = TILE_SIZE * 0.8
            bar_h = 4
            bar_x = self.world_x + (TILE_SIZE - bar_w) / 2
            bar_y = self.world_y + TILE_SIZE - bar_h - 2
            bg_rect = (bar_x, bar_y, bar_w, bar_h)
            pygame.draw.rect(surface, COLOR_RED, bg_rect)
            if ratio > 0:
                hp_rect = (bar_x, bar_y, bar_w * ratio, bar_h)
                pygame.draw.rect(surface, COLOR_GREEN, hp_rect)

    def take_damage(self, amount, game):
        if self.building_type == BUILDING_CORE and game.game_over:
            return False
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.destroyed = True
            return True
        return False

    def get_neighbor(self, game, direction_index):
        dx, dy = ORIENTATIONS[direction_index]
        nx = self.grid_x + dx
        ny = self.grid_y + dy
        return game.get_structure_at(nx, ny)

    def get_all_neighbors(self, game):
        neighbors = []
        for i in range(4):
            neighbor = self.get_neighbor(game, i)
            if neighbor is not None:
                neighbors.append(neighbor)
        return neighbors

    def try_accept_item(self, source_structure, game, item_type):
        return False

    def can_upgrade(self):
        has_costs = hasattr(self, 'upgrade_cost')
        more_tiers = (self.tier < self.max_tier)
        next_cost_exists = False
        if has_costs and more_tiers:
            next_cost_exists = (self.tier + 1) in self.upgrade_cost
        return has_costs and more_tiers and next_cost_exists

    def get_next_upgrade_cost(self):
        if self.can_upgrade():
            return self.upgrade_cost.get(self.tier + 1)
        return None

    def apply_upgrade(self, game):
        if not self.can_upgrade():
            return False
        hp_ratio = self.hp / self.max_hp if self.max_hp > 0 else 1.0
        self.tier += 1
        print(f"SERVER: {type(self).__name__} @ ({self.grid_x},{self.grid_y}) upgraded to Tier {self.tier}!")
        if hasattr(self, 'update_stats'):
            self.update_stats()
        else:
             print(f"WARN: {type(self).__name__} upgraded but has no update_stats method!")
        # Ensure max_hp is updated before setting hp
        if hasattr(self, 'max_hp'):
            self.hp = min(self.max_hp, self.max_hp * hp_ratio)
        else: # Fallback if max_hp wasn't updated by update_stats
            self.hp = self.hp * hp_ratio # May exceed new max_hp temporarily

        if self.max_hp > 0 and self.hp < 1:
            self.hp = 1
        return True

    def get_state(self):
        """Returns a serializable dictionary for network transfer."""
        state = {
            'net_id': self.network_id,
            'type': self.building_type,
            'gx': self.grid_x, 'gy': self.grid_y,
            'hp': self.hp, 'max_hp': self.max_hp, 'tier': self.tier,
            'is_powered': self.is_powered, 'is_on_grid': self.is_on_grid,
            'connected_nodes_coords': self.connected_nodes_coords,
            'power_source_coords': getattr(self, 'power_source_coords', None)
        }
        # Add type-specific state (remains the same)
        if self.building_type == BUILDING_CONVEYOR:
            state.update({'orientation': self.orientation, 'item_type': self.item_type, 'item_count': self.item_count,
                          'item_progress': self.item_progress})
        elif self.building_type == BUILDING_TURRET:
            state.update({'ammo': self.ammo, 'angle': self.angle})
        elif self.building_type == BUILDING_DRILL:
            state.update({'res_held': self.resource_held_count, 'res_type': self.resource_type_held})
        elif self.building_type == BUILDING_COALGENERATOR:
            state.update({'coal_buffer': self.coal_buffer, 'is_generating': self.is_power_source})
        elif self.building_type == BUILDING_BATTERY:
            state.update(
                {'charge': self.charge, 'is_charging': self.is_charging, 'is_discharging': self.is_discharging})

        return state

    def apply_state(self, state_data):
        """Updates the structure's state from received data (Client-side)."""
        new_tier = state_data.get('tier', self.tier)
        tier_changed = (new_tier != self.tier)
        self.tier = new_tier
        self.hp = state_data.get('hp', self.hp)
        self.is_powered = state_data.get('is_powered', self.is_powered)
        self.is_on_grid = state_data.get('is_on_grid', self.is_on_grid)
        self.connected_nodes_coords = state_data.get('connected_nodes_coords', [])
        self.power_source_coords = state_data.get('power_source_coords', None)

        if tier_changed and hasattr(self, 'update_stats'):
             self.update_stats()
        self.max_hp = state_data.get('max_hp', self.max_hp)

        if self.building_type == BUILDING_CONVEYOR:
            self.orientation = state_data.get('orientation', self.orientation)
            self.item_type = state_data.get('item_type', self.item_type)
            self.item_count = state_data.get('item_count', self.item_count)
            self.item_progress = state_data.get('item_progress', self.item_progress)
        elif self.building_type == BUILDING_TURRET:
            self.ammo = state_data.get('ammo', self.ammo)
            self.angle = state_data.get('angle', self.angle)
        elif self.building_type == BUILDING_DRILL:
            self.resource_held_count = state_data.get('res_held', self.resource_held_count)
            self.resource_type_held = state_data.get('res_type', self.resource_type_held)
        elif self.building_type == BUILDING_COALGENERATOR:
            self.coal_buffer = state_data.get('coal_buffer', self.coal_buffer)
            self.is_power_source = state_data.get('is_generating', self.is_power_source)
        elif self.building_type == BUILDING_BATTERY:
            self.charge = state_data.get('charge', self.charge)
            self.is_charging = state_data.get('is_charging', self.is_charging)
            self.is_discharging = state_data.get('is_discharging', self.is_discharging)

# --- Subclasses (Core, ResourcePatch, Drill, Conveyor, Turret, Wall, CoalGenerator, PowerPole, Battery, Reconstructor) ---
# (Keep these subclasses exactly as they were in the previous version, including their draw, update, try_accept, etc. methods)
# Example:
class Core(Structure):
    def __init__(self, gx, gy):
        super().__init__(gx, gy, CORE_HP, {}, COLOR_BLUE, BUILDING_CORE)
    def draw(self, surface):
        super().draw(surface)
        inner_rect = (self.world_x + 4, self.world_y + 4, TILE_SIZE - 8, TILE_SIZE - 8)
        pygame.draw.rect(surface, COLOR_WHITE, inner_rect, 2)
    def try_accept_item(self, source_structure, game, item_type):
        if item_type in game.resources:
            game.resources[item_type] += 1
            return True
        else:
            print(f"WARN: Core received unknown item type: {item_type}")
            return False

class ResourcePatch(Structure):
    def __init__(self, gx, gy, resource_type):
        self.resource_type = resource_type
        color = COLOR_COPPER if resource_type == RES_COPPER else COLOR_COAL
        super().__init__(gx, gy, 99999, {}, color, BUILDING_RESOURCE)
        self.network_id = f"res_{gx}_{gy}"
    def draw(self, surface):
        super().draw(surface)
        indicator_color = COLOR_BLACK if self.resource_type == RES_COAL else COLOR_DARK_GRAY
        cx, cy = int(self.center_x), int(self.center_y)
        pygame.draw.circle(surface, indicator_color, (cx, cy), TILE_SIZE // 5, 2)
    def get_state(self): return None
    def apply_state(self, state_data): pass

class Drill(Structure):
    def __init__(self, gx, gy):
        super().__init__(gx, gy, DRILL_STATS[0][1], DRILL_COST, COLOR_DRILL, BUILDING_DRILL)
        self.mining_timer = 0.0; self.output_timer = 0.0
        self.resource_held_count = 0; self.resource_type_held = None
        self.is_on_patch = False; self.max_tier = MAX_TIER
        self.upgrade_cost = DRILL_UPGRADE_COST; self.speed = DRILL_STATS[0][0]
        self.update_stats()
    def update_stats(self):
        if 0 <= self.tier - 1 < len(DRILL_STATS):
             stats = DRILL_STATS[self.tier - 1]
             self.speed, self.max_hp = stats[0], stats[1]
        else: print(f"WARN: Invalid tier {self.tier} for Drill stats.")
    def setup_on_patch(self, game):
        patch_type = game.base_terrain.get((self.grid_x, self.grid_y))
        if patch_type in [RES_COPPER, RES_COAL]:
            self.resource_type_held = patch_type; self.is_on_patch = True
        else: self.is_on_patch = False
    def update(self, game):
        if not self.is_on_patch or self.resource_type_held is None: return
        self.mining_timer += game.dt
        if self.mining_timer >= self.speed:
            self.mining_timer -= self.speed; self.resource_held_count += 1
        self.output_timer += game.dt
        if self.resource_held_count > 0 and self.output_timer >= DRILL_OUTPUT_COOLDOWN:
            self.output_timer = 0
            if self.try_output_resource(game): self.resource_held_count -= 1
    def try_output_resource(self, game):
        neighbors = self.get_all_neighbors(game); random.shuffle(neighbors)
        for neighbor in neighbors:
            if neighbor.try_accept_item(self, game, self.resource_type_held): return True
        return False
    def draw(self, surface):
        super().draw(surface)
        pygame.draw.circle(surface, COLOR_GRAY, (int(self.center_x), int(self.center_y)), TILE_SIZE // 5)
        if self.resource_held_count > 0 and self.resource_type_held is not None:
            item_color = COLOR_COPPER if self.resource_type_held == RES_COPPER else COLOR_COAL
            pygame.draw.rect(surface, item_color, (self.world_x + 2, self.world_y + 2, 6, 6))
        if self.max_tier > 1:
            draw_text(surface, f"T{self.tier}", 14, self.world_x + TILE_SIZE - 2, self.world_y + TILE_SIZE - 12, COLOR_WHITE, align="bottomright")

class Conveyor(Structure):
    def __init__(self, gx, gy, orientation=EAST):
        super().__init__(gx, gy, CONVEYOR_STATS[0][1], CONVEYOR_COST, COLOR_CONVEYOR, BUILDING_CONVEYOR)
        self.orientation = orientation; self.item_progress = 0.0
        self.item_type = None; self.item_count = 0; self.max_tier = MAX_TIER
        self.upgrade_cost = CONVEYOR_UPGRADE_COST
        self.transfer_time = CONVEYOR_STATS[0][0]; self.capacity = CONVEYOR_STATS[0][2]
        self.update_stats()
    def update_stats(self):
        if 0 <= self.tier - 1 < len(CONVEYOR_STATS):
            stats = CONVEYOR_STATS[self.tier - 1]
            self.transfer_time, self.max_hp, self.capacity = stats[0], stats[1], stats[2]
        else: print(f"WARN: Invalid tier {self.tier} for Conveyor stats.")
        self.item_count = min(self.item_count, self.capacity)
        if self.item_count == 0: self.item_type = None
    def update(self, game):
        if self.item_count > 0 and self.transfer_time > 0:
            delta_progress = game.dt / self.transfer_time
            self.item_progress += delta_progress
            if self.item_progress >= 1.0:
                if self.try_push_item(game):
                    self.item_count -= 1
                    if self.item_count > 0: self.item_progress = max(0.0, self.item_progress - 1.0)
                    else: self.item_progress = 0.0; self.item_type = None
                else: self.item_progress = 1.0
    def client_update(self, dt):
         if self.item_count > 0 and self.transfer_time > 0:
             delta_progress = dt / self.transfer_time
             potential_progress = self.item_progress + delta_progress
             if self.item_progress > 0.99 and potential_progress > 1.0: self.item_progress = 1.0
             else: self.item_progress = potential_progress % (1.0 + 1e-6)
    def try_accept_item(self, source_structure, game, item_type_to_accept):
        if self.item_count < self.capacity:
            if self.item_count == 0:
                self.item_type = item_type_to_accept; self.item_progress = 0.0; self.item_count += 1; return True
            elif item_type_to_accept == self.item_type:
                self.item_count += 1; return True
        return False
    def try_push_item(self, game):
        if self.item_count <= 0 or self.item_type is None: return False
        target = self.get_neighbor(game, self.orientation)
        if target is not None and target.try_accept_item(self, game, self.item_type): return True
        return False
    def draw(self, surface):
        super().draw(surface); self._draw_arrow(surface)
        if self.item_count > 0: self._draw_items(surface)
        if self.max_tier > 1: draw_text(surface, f"T{self.tier}", 14, self.world_x + TILE_SIZE - 2, self.world_y + TILE_SIZE - 12, COLOR_BLACK, align="bottomright")
    def _draw_arrow(self, surface):
        cx, cy = self.center_x, self.center_y; dx, dy = ORIENTATIONS[self.orientation]
        base_len, head_len = TILE_SIZE * 0.3, TILE_SIZE * 0.15; pdx, pdy = -dy, dx
        lsx, lsy = cx - dx * base_len * 0.6, cy - dy * base_len * 0.6
        lex, ley = cx + dx * base_len * 0.6, cy + dy * base_len * 0.6
        pygame.draw.line(surface, COLOR_BLACK, (lsx, lsy), (lex, ley), 2)
        w1x, w1y = lex - dx * head_len + pdx * head_len, ley - dy * head_len + pdy * head_len
        w2x, w2y = lex - dx * head_len - pdx * head_len, ley - dy * head_len - pdy * head_len
        pygame.draw.line(surface, COLOR_BLACK, (lex, ley), (w1x, w1y), 2)
        pygame.draw.line(surface, COLOR_BLACK, (lex, ley), (w2x, w2y), 2)
    def _draw_items(self, surface):
        if self.item_type is None or self.item_count <= 0: return
        item_color = COLOR_COPPER if self.item_type == RES_COPPER else COLOR_COAL
        item_size = TILE_SIZE * 0.35; half_size = item_size / 2.0
        dx, dy = ORIENTATIONS[self.orientation]
        travel_dist = TILE_SIZE * 0.8; half_travel = travel_dist / 2.0
        sx, sy = self.center_x - dx * half_travel, self.center_y - dy * half_travel
        ex, ey = self.center_x + dx * half_travel, self.center_y + dy * half_travel
        clamped_progress = max(0.0, min(1.0, self.item_progress))
        lead_x = sx + (ex - sx) * clamped_progress; lead_y = sy + (ey - sy) * clamped_progress
        spacing_dist = TILE_SIZE * CONVEYOR_ITEM_SPACING
        sp_dx, sp_dy = -dx * spacing_dist, -dy * spacing_dist
        for i in range(self.item_count):
            cur_x, cur_y = lead_x + i * sp_dx, lead_y + i * sp_dy
            if abs(cur_x - self.center_x) < TILE_SIZE * 0.6 and abs(cur_y - self.center_y) < TILE_SIZE * 0.6:
                item_rect = pygame.Rect(cur_x - half_size, cur_y - half_size, item_size, item_size)
                pygame.draw.rect(surface, item_color, item_rect)
                pygame.draw.rect(surface, COLOR_BLACK, item_rect, 1)

class Turret(Structure):
    def __init__(self, gx, gy):
        super().__init__(gx, gy, TURRET_STATS[0][3], TURRET_COST, COLOR_TURRET, BUILDING_TURRET)
        self.fire_timer = random.uniform(0, TURRET_STATS[0][2]); self.ammo = 0
        self.capacity = TURRET_AMMO_CAPACITY; self.target_id = None; self.angle = 0.0
        self.max_tier = MAX_TIER; self.upgrade_cost = TURRET_UPGRADE_COST
        self.range = TURRET_STATS[0][0]; self.range_sq = self.range * self.range
        self.damage = TURRET_STATS[0][1]; self.fire_rate = TURRET_STATS[0][2]
        self.update_stats()
    def update_stats(self):
        if 0 <= self.tier - 1 < len(TURRET_STATS):
            stats = TURRET_STATS[self.tier - 1]
            self.range, self.damage, self.fire_rate, self.max_hp = stats[0], stats[1], stats[2], stats[3]
            self.range_sq = self.range * self.range; self.ammo = 0
        else: print(f"WARN: Invalid tier {self.tier} for Turret stats.")
        if self.tier == 3: self.is_power_consumer = True; self.power_consumption = TURRET_T3_POWER_CONSUMPTION
        else: self.is_power_consumer = False; self.power_consumption = 0; self.is_powered = False
    def try_accept_ammo(self):
        if self.tier < 3 and self.ammo < self.capacity: self.ammo += 1; return True
        return False
    def try_accept_item(self, source_structure, game, item_type):
        if item_type == RES_COPPER and self.tier < 3: return self.try_accept_ammo()
        return False
    def update(self, game):
        self.fire_timer += game.dt
        target_enemy = game.get_enemy_by_id(self.target_id) if self.target_id else None
        target_lost = (target_enemy is None or target_enemy.destroyed or
                       distance_sq(self.center_x, self.center_y, target_enemy.world_x, target_enemy.world_y) > self.range_sq)
        if target_lost:
            new_target = self.find_target(game.enemies)
            self.target_id = new_target.network_id if new_target else None
            target_enemy = new_target
        if target_enemy is not None:
            dx, dy = target_enemy.world_x - self.center_x, target_enemy.world_y - self.center_y
            self.angle = math.atan2(dy, dx)
            ready = (self.fire_timer >= self.fire_rate)
            has_res = (self.ammo >= TURRET_AMMO_CONSUMPTION) if self.tier < 3 else self.is_powered
            if ready and has_res:
                self.fire_timer = 0
                if self.tier < 3: self.ammo -= TURRET_AMMO_CONSUMPTION
                proj = Projectile(self.center_x, self.center_y, target_enemy, PROJECTILE_SPEED, self.damage, game.get_next_projectile_id())
                game.projectiles[proj.network_id] = proj
    def find_target(self, enemies_dict):
        closest = None; min_d_sq = self.range_sq
        for enemy in enemies_dict.values():
            if enemy.destroyed: continue
            d_sq = distance_sq(self.center_x, self.center_y, enemy.world_x, enemy.world_y)
            if d_sq <= self.range_sq and (closest is None or d_sq < min_d_sq):
                min_d_sq = d_sq; closest = enemy
        return closest
    def draw(self, surface):
        super().draw(surface)
        barrel_len = TILE_SIZE * 0.6; barrel_thick = 4 + self.tier
        ex = self.center_x + barrel_len * math.cos(self.angle)
        ey = self.center_y + barrel_len * math.sin(self.angle)
        pygame.draw.line(surface, COLOR_BLACK, (self.center_x, self.center_y), (ex, ey), barrel_thick)
        if self.tier < 3:
            ix, iy = self.world_x + TILE_SIZE - 8, self.world_y + 8
            draw_text(surface, str(self.ammo), 16, ix, iy - 6, COLOR_YELLOW, align="center")
        if self.max_tier > 1:
             draw_text(surface, f"T{self.tier}", 14, self.world_x + TILE_SIZE - 2, self.world_y + TILE_SIZE - 12, COLOR_WHITE, align="bottomright")

class Wall(Structure):
    def __init__(self, gx, gy):
        super().__init__(gx, gy, WALL_HP, WALL_COST, COLOR_WALL, BUILDING_WALL)
    def draw(self, surface):
        super().draw(surface); s = TILE_SIZE - 1
        pygame.draw.line(surface, COLOR_WHITE, (self.world_x, self.world_y), (self.world_x + s, self.world_y), 2)
        pygame.draw.line(surface, COLOR_WHITE, (self.world_x, self.world_y), (self.world_x, self.world_y + s), 2)
        pygame.draw.line(surface, COLOR_DARK_GRAY, (self.world_x + s, self.world_y + 1), (self.world_x + s, self.world_y + s), 2)
        pygame.draw.line(surface, COLOR_DARK_GRAY, (self.world_x + 1, self.world_y + s), (self.world_x + s, self.world_y + s), 2)

class CoalGenerator(Structure):
    def __init__(self, gx, gy):
        super().__init__(gx, gy, COALGENERATOR_HP, COALGENERATOR_COST, COLOR_GENERATOR, BUILDING_COALGENERATOR)
        self.coal_buffer = 0; self.consume_timer = 0.0; self.is_power_node = True
    def try_accept_coal(self):
        if self.coal_buffer < COALGENERATOR_INPUT_CAP: self.coal_buffer += 1; return True
        return False
    def try_accept_item(self, source_structure, game, item_type):
        if item_type == RES_COAL: return self.try_accept_coal()
        return False
    def update(self, game):
        self.is_power_source = (self.coal_buffer > 0)
        if self.is_power_source:
            self.consume_timer += game.dt
            if self.consume_timer >= COALGENERATOR_CONSUMPTION_RATE:
                self.consume_timer -= COALGENERATOR_CONSUMPTION_RATE; self.coal_buffer -= 1
        else: self.consume_timer = 0.0
    def draw(self, surface):
        super().draw(surface)
        if self.coal_buffer > 0:
            ratio = min(1.0, self.coal_buffer / COALGENERATOR_INPUT_CAP)
            bar_h = TILE_SIZE * 0.8 * ratio; bar_w = 4
            bar_x, bar_y = self.world_x + 2, self.world_y + TILE_SIZE - 2 - bar_h
            pygame.draw.rect(surface, COLOR_COAL, (bar_x, bar_y, bar_w, bar_h))
        if self.is_power_source and int(time.time() * 4) % 2 == 0:
            pygame.draw.circle(surface, COLOR_YELLOW, (int(self.center_x), int(self.center_y)), 5)

class PowerPole(Structure):
    def __init__(self, gx, gy):
        super().__init__(gx, gy, POWERPOLE_HP, POWERPOLE_COST, COLOR_POLE, BUILDING_POWERPOLE)
        self.is_power_node = True
    def draw(self, surface):
        super().draw(surface)
        if self.is_on_grid: pygame.draw.circle(surface, COLOR_POWER_LINE, (int(self.center_x), int(self.center_y)), 4)

class Battery(Structure):
    def __init__(self, gx, gy):
        super().__init__(gx, gy, BATTERY_HP, BATTERY_COST, COLOR_BATTERY, BUILDING_BATTERY)
        self.is_power_node = True; self.is_power_storage = True; self.charge = 0.0
        self.capacity = BATTERY_CAPACITY; self.charge_rate = BATTERY_CHARGE_RATE
        self.discharge_rate = BATTERY_DISCHARGE_RATE
        self.is_charging = False; self.is_discharging = False
    def update(self, game):
        self.charge = max(0.0, min(self.charge, self.capacity))
    def draw(self, surface):
        super().draw(surface)
        ratio = max(0.0, min(1.0, self.charge / self.capacity if self.capacity > 0 else 0))
        bar_w = TILE_SIZE * 0.9; bar_h = 6
        bar_x = self.world_x + (TILE_SIZE - bar_w) / 2; bar_y = self.world_y + TILE_SIZE - bar_h - 3
        pygame.draw.rect(surface, COLOR_DARK_GRAY, (bar_x, bar_y, bar_w, bar_h))
        if ratio > 0: pygame.draw.rect(surface, COLOR_BATTERY_CHARGE, (bar_x, bar_y, bar_w * ratio, bar_h))
        status_color = None
        if self.is_charging: status_color = COLOR_GREEN
        elif self.is_discharging: status_color = COLOR_RED
        if status_color: pygame.draw.circle(surface, status_color, (int(self.center_x), int(self.center_y)), 4)

class Reconstructor(Structure):
    def __init__(self, gx, gy):
        super().__init__(gx, gy, RECONSTRUCTOR_HP, RECONSTRUCTOR_COST, COLOR_RECONSTRUCTOR, BUILDING_RECONSTRUCTOR)
        self.is_power_consumer = True; self.power_consumption = RECONSTRUCTOR_POWER_CONSUMPTION
        self.repair_timer = 0.0; self.repair_radius_sq = RECONSTRUCTOR_REPAIR_RADIUS * RECONSTRUCTOR_REPAIR_RADIUS
    def update(self, game):
        if not self.is_powered: self.repair_timer = 0.0; return
        self.repair_timer += game.dt
        heal_per_sec = RECONSTRUCTOR_REPAIR_RATE; check_interval = 0.1
        if self.repair_timer >= check_interval:
            heal_amount = heal_per_sec * self.repair_timer; self.repair_timer = 0.0
            targets = []
            radius_grid = int(RECONSTRUCTOR_REPAIR_RADIUS / TILE_SIZE) + 2
            for dx in range(-radius_grid, radius_grid + 1):
                 for dy in range(-radius_grid, radius_grid + 1):
                      struct = game.get_structure_at(self.grid_x + dx, self.grid_y + dy)
                      if (struct and struct != self and struct.building_type != BUILDING_RESOURCE and
                          struct.hp < struct.max_hp and
                          distance_sq(self.center_x, self.center_y, struct.center_x, struct.center_y) <= self.repair_radius_sq):
                          targets.append(struct)
            if targets:
                 target = random.choice(targets)
                 target.hp = min(target.max_hp, target.hp + heal_amount)
    def draw(self, surface):
        super().draw(surface)
        if self.is_powered:
            radius = int(RECONSTRUCTOR_REPAIR_RADIUS)
            aura_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(aura_surf, COLOR_REPAIR_AURA, (radius, radius), radius)
            surface.blit(aura_surf, (self.center_x - radius, self.center_y - radius))

# --- Enemy & Projectile Classes ---
# (Keep Enemy and Projectile classes exactly as they were in the previous corrected version)
class Enemy:
    def __init__(self, sx, sy, target_core_coords, hp, speed, dmg, atk_cd, network_id):
        self.network_id = network_id; self.world_x = float(sx); self.world_y = float(sy)
        self.target_core_coords = target_core_coords; self.current_attack_target_id = None
        self.max_hp = hp; self.hp = hp; self.speed = speed; self.damage = dmg
        self.attack_cooldown = atk_cd; self.attack_timer = 0.0; self.destroyed = False
    def update(self, game):
        if self.destroyed: return
        speed_this_frame = self.speed * game.dt
        target_struct = game.get_structure_by_id(self.current_attack_target_id) if self.current_attack_target_id else None
        target_invalid = (target_struct is None or target_struct.destroyed)
        if target_invalid:
            target_struct = self.find_attack_target(game)
            self.current_attack_target_id = target_struct.network_id if target_struct else None
            self.attack_timer = 0
        if target_struct:
            attack_range_sq = (TILE_SIZE * 0.8)**2
            dist_sq = distance_sq(self.world_x, self.world_y, target_struct.center_x, target_struct.center_y)
            if dist_sq <= attack_range_sq:
                self.attack_timer += game.dt
                if self.attack_timer >= self.attack_cooldown:
                    self.attack_timer = 0
                    if target_struct.take_damage(self.damage, game):
                        self.current_attack_target_id = None
            else: self.current_attack_target_id = None; target_struct = None
        if target_struct is None:
            tx, ty = self.target_core_coords
            dx, dy = tx - self.world_x, ty - self.world_y
            dist = math.sqrt(dx*dx + dy*dy) + 1e-9
            move_x, move_y = (dx / dist) * speed_this_frame, (dy / dist) * speed_this_frame
            next_x, next_y = self.world_x + move_x, self.world_y + move_y
            check_x, check_y = self.world_x + move_x * 1.5, self.world_y + move_y * 1.5
            check_gx, check_gy = world_to_grid(check_x, check_y)
            curr_gx, curr_gy = world_to_grid(self.world_x, self.world_y)
            can_move = True
            if check_gx != curr_gx or check_gy != curr_gy:
                blocking = game.get_structure_at(check_gx, check_gy)
                if blocking and blocking.building_type != BUILDING_RESOURCE:
                    can_move = False
                    if self.current_attack_target_id is None:
                        self.current_attack_target_id = blocking.network_id
                        self.attack_timer = self.attack_cooldown
            if can_move:
                 # Use map dimensions from game instance
                 map_width = game.map_width_px if game else 10000
                 map_height = game.map_height_px if game else 10000
                 self.world_x = max(0, min(next_x, map_width)) # Allow getting close to edge
                 self.world_y = max(0, min(next_y, map_height))
    def find_attack_target(self, game):
        possible = []; attack_range_sq = (TILE_SIZE * 0.8)**2
        gx, gy = world_to_grid(self.world_x, self.world_y)
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                struct = game.get_structure_at(gx + dx, gy + dy)
                if struct and struct.building_type != BUILDING_RESOURCE:
                    if distance_sq(self.world_x, self.world_y, struct.center_x, struct.center_y) < attack_range_sq:
                        prio = 0; b_type = struct.building_type
                        if b_type == BUILDING_CORE: prio = 10
                        elif b_type == BUILDING_TURRET: prio = 8
                        elif b_type == BUILDING_RECONSTRUCTOR: prio = 7
                        elif b_type in [BUILDING_COALGENERATOR, BUILDING_BATTERY, BUILDING_DRILL]: prio = 5
                        elif b_type == BUILDING_WALL: prio = 4
                        elif b_type == BUILDING_POWERPOLE: prio = 2
                        elif b_type == BUILDING_CONVEYOR: prio = 1
                        if prio > 0: possible.append((prio, struct))
        if not possible: return None
        possible.sort(key=lambda item: item[0], reverse=True)
        return possible[0][1]
    def take_damage(self, amount, game):
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0; self.destroyed = True
            if game.network_mode != "client": game.resources[RES_COPPER] += 10
    def draw(self, surface):
        if not self.destroyed:
            rad = TILE_SIZE // 3; px, py = int(self.world_x), int(self.world_y)
            pygame.draw.circle(surface, COLOR_ENEMY, (px, py), rad)
            pygame.draw.circle(surface, COLOR_BLACK, (px, py), rad, 1)
            if self.hp < self.max_hp:
                ratio = max(0.0, min(1.0, self.hp / self.max_hp))
                bar_w = rad * 2; bar_h = 4
                bar_x = self.world_x - rad; bar_y = self.world_y - rad - bar_h - 2
                pygame.draw.rect(surface, COLOR_RED, (bar_x, bar_y, bar_w, bar_h))
                if ratio > 0: pygame.draw.rect(surface, COLOR_GREEN, (bar_x, bar_y, bar_w * ratio, bar_h))
    def get_state(self):
        return {'net_id': self.network_id, 'x': self.world_x, 'y': self.world_y, 'hp': self.hp, 'max_hp': self.max_hp}
    def apply_state(self, state_data):
        self.world_x = state_data.get('x', self.world_x); self.world_y = state_data.get('y', self.world_y)
        self.hp = state_data.get('hp', self.hp); self.max_hp = state_data.get('max_hp', self.max_hp)

class Projectile:
    def __init__(self, sx, sy, target_enemy_obj, speed, dmg, network_id, vx=None, vy=None):
        self.network_id = network_id; self.world_x = float(sx); self.world_y = float(sy)
        self.target_enemy_id = target_enemy_obj.network_id if target_enemy_obj else None
        self.speed = speed; self.damage = dmg; self.destroyed = False; self.lifetime = 2.0
        if vx is not None and vy is not None: self.vx, self.vy = vx, vy
        elif target_enemy_obj:
            dx, dy = target_enemy_obj.world_x - self.world_x, target_enemy_obj.world_y - self.world_y
            dist = math.sqrt(dx*dx + dy*dy) + 1e-9
            self.vx, self.vy = (dx / dist) * self.speed, (dy / dist) * self.speed
        else: self.vx, self.vy = 0, 0; print(f"WARN: Proj {self.network_id} created with no target/velocity.")
    def update(self, game):
        if self.destroyed: return
        self.world_x += self.vx * game.dt; self.world_y += self.vy * game.dt
        self.lifetime -= game.dt
        target = game.get_enemy_by_id(self.target_enemy_id) if self.target_enemy_id else None
        hit_rad_sq = (TILE_SIZE / 3 + 4)**2
        if target and not target.destroyed:
            if distance_sq(self.world_x, self.world_y, target.world_x, target.world_y) < hit_rad_sq:
                target.take_damage(self.damage, game); self.destroyed = True; return
        if self.lifetime <= 0 or not (0 <= self.world_x < game.map_width_px and 0 <= self.world_y < game.map_height_px):
             self.destroyed = True
    def client_update(self, dt):
        if not self.destroyed: self.world_x += self.vx * dt; self.world_y += self.vy * dt
    def draw(self, surface):
        if not self.destroyed: pygame.draw.circle(surface, COLOR_PROJECTILE, (int(self.world_x), int(self.world_y)), 4)
    def get_state(self): return {'net_id': self.network_id, 'x': self.world_x, 'y': self.world_y, 'vx': self.vx, 'vy': self.vy}
    def apply_state(self, state_data):
        self.world_x = state_data.get('x', self.world_x); self.world_y = state_data.get('y', self.world_y)
        self.vx = state_data.get('vx', self.vx); self.vy = state_data.get('vy', self.vy)


# --- Settings Menu Class ---
class SettingsMenu:
    def __init__(self, screen, clock, initial_name, initial_color_index, initial_res_index, initial_net_interval):
        self.screen_width = screen.get_width()
        self.screen_height = screen.get_height()
        self.screen = screen
        self.clock = clock
        self.title = "Settings"
        self.current_name = initial_name
        self.selected_color_index = initial_color_index
        self.current_ip = "127.0.0.1" # Default IP, maybe load/save later
        self.available_resolutions = AVAILABLE_RESOLUTIONS
        self.current_resolution_index = initial_res_index
        self.min_net_interval = MIN_NETWORK_UPDATE_INTERVAL
        self.max_net_interval = MAX_NETWORK_UPDATE_INTERVAL
        try: # Validate initial interval string
             init_interval_val = float(initial_net_interval)
             init_interval_val = max(self.min_net_interval, min(init_interval_val, self.max_net_interval))
             self.current_network_interval_str = f"{init_interval_val:.4f}" # Store with more precision
        except ValueError:
             self.current_network_interval_str = f"{DEFAULT_NETWORK_UPDATE_INTERVAL:.4f}"
        self.input_active = False
        self.ip_input_active = False
        self.interval_input_active = False
        self.max_name_length = 16
        self.cursor_timer = 0.0
        self.show_cursor = True
        self.back_button_rect = None
        self.color_swatch_rects = []
        self.name_input_rect = None
        self.ip_input_rect = None
        self.res_left_arrow_rect = None
        self.res_right_arrow_rect = None
        self.res_display_rect = None
        self.interval_input_rect = None
        self._setup_ui()

    def _setup_ui(self):
        center_x = self.screen_width // 2
        base_y = 80
        input_box_width = 300; input_box_height = 40
        input_y_spacing = 75; label_offset_y = -30
        name_y = base_y + 50
        self.name_input_rect = pygame.Rect(center_x - input_box_width // 2, name_y, input_box_width, input_box_height)
        color_y = name_y + input_y_spacing
        swatch_size = 30; swatch_padding = 10
        total_swatch_width = len(COLOR_PLAYER_OPTIONS) * swatch_size + (len(COLOR_PLAYER_OPTIONS) - 1) * swatch_padding
        start_swatch_x = center_x - total_swatch_width // 2
        self.color_swatch_rects = []
        for i, color in enumerate(COLOR_PLAYER_OPTIONS):
            r = pygame.Rect(start_swatch_x + i * (swatch_size + swatch_padding), color_y, swatch_size, swatch_size)
            self.color_swatch_rects.append(r)
        res_y = color_y + input_y_spacing - 15
        arrow_w, arrow_h = 30, 40; res_disp_w = 180
        res_total_w = arrow_w + res_disp_w + arrow_w + 20
        res_start_x = center_x - res_total_w // 2
        self.res_left_arrow_rect = pygame.Rect(res_start_x, res_y, arrow_w, arrow_h)
        self.res_display_rect = pygame.Rect(res_start_x + arrow_w + 10, res_y, res_disp_w, arrow_h)
        self.res_right_arrow_rect = pygame.Rect(res_start_x + arrow_w + res_disp_w + 20, res_y, arrow_w, arrow_h)
        interval_y = res_y + input_y_spacing
        self.interval_input_rect = pygame.Rect(center_x - input_box_width // 2, interval_y, input_box_width, input_box_height)
        ip_y = interval_y + input_y_spacing
        self.ip_input_rect = pygame.Rect(center_x - input_box_width // 2, ip_y, input_box_width, input_box_height)
        button_width, button_height = 150, 50
        back_y = ip_y + input_y_spacing
        back_y = min(back_y, self.screen_height - button_height - 20)
        self.back_button_rect = pygame.Rect(center_x - button_width // 2, back_y, button_width, button_height)

    def handle_event(self, event):
        action = None
        resolution_changed = False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            was_active = self.input_active or self.ip_input_active or self.interval_input_active
            self.input_active = self.ip_input_active = self.interval_input_active = False # Deactivate all
            if self.back_button_rect.collidepoint(mouse_pos):
                self._validate_and_clamp_interval(); action = 'back'
            elif self.name_input_rect.collidepoint(mouse_pos):
                self.input_active = True;
                if was_active and not self.input_active: self._validate_and_clamp_interval()
            elif self.ip_input_rect.collidepoint(mouse_pos):
                self.ip_input_active = True;
                if was_active and not self.ip_input_active: self._validate_and_clamp_interval()
            elif self.interval_input_rect.collidepoint(mouse_pos):
                self.interval_input_active = True # No validation on activate
            elif self.res_left_arrow_rect.collidepoint(mouse_pos):
                self.current_resolution_index = (self.current_resolution_index - 1) % len(self.available_resolutions)
                resolution_changed = True;
                if was_active: self._validate_and_clamp_interval()
            elif self.res_right_arrow_rect.collidepoint(mouse_pos):
                self.current_resolution_index = (self.current_resolution_index + 1) % len(self.available_resolutions)
                resolution_changed = True;
                if was_active: self._validate_and_clamp_interval()
            else:
                swatch_clicked = False
                for i, rect in enumerate(self.color_swatch_rects):
                    if rect.collidepoint(mouse_pos): self.selected_color_index = i; swatch_clicked = True; break
                if not swatch_clicked and was_active: self._validate_and_clamp_interval()
            # Note: resolution change is applied on 'back' in main loop

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._validate_and_clamp_interval(); action = 'back'
                self.input_active = self.ip_input_active = self.interval_input_active = False
            if self.input_active or self.ip_input_active or self.interval_input_active:
                self.cursor_timer = 0.0; self.show_cursor = True
            if self.input_active:
                if event.key == pygame.K_BACKSPACE: self.current_name = self.current_name[:-1]
                elif event.key in [pygame.K_RETURN, pygame.K_KP_ENTER]: self.input_active = False
                elif len(self.current_name) < self.max_name_length and (event.unicode.isalnum() or event.unicode == ' '):
                    self.current_name += event.unicode
            elif self.ip_input_active:
                if event.key == pygame.K_BACKSPACE: self.current_ip = self.current_ip[:-1]
                elif event.key in [pygame.K_RETURN, pygame.K_KP_ENTER]: self.ip_input_active = False
                elif len(self.current_ip) < 30 and (event.unicode.isdigit() or event.unicode == '.'):
                    self.current_ip += event.unicode
            elif self.interval_input_active:
                 if event.key == pygame.K_BACKSPACE: self.current_network_interval_str = self.current_network_interval_str[:-1]
                 elif event.key in [pygame.K_RETURN, pygame.K_KP_ENTER]:
                      self.interval_input_active = False; self._validate_and_clamp_interval()
                 elif len(self.current_network_interval_str) < 7:
                     if event.unicode.isdigit() or (event.unicode == '.' and '.' not in self.current_network_interval_str):
                         if not(event.unicode == '0' and len(self.current_network_interval_str) == 1 and self.current_network_interval_str[0] == '0'):
                             self.current_network_interval_str += event.unicode
        return action

    def _validate_and_clamp_interval(self):
        try:
            val = float(self.current_network_interval_str if self.current_network_interval_str else "0") # Handle empty string
            clamped_val = max(self.min_net_interval, min(val, self.max_net_interval))
            if clamped_val <= 0: clamped_val = self.min_net_interval
            self.current_network_interval_str = f"{clamped_val:.4f}"
        except ValueError:
            print(f"WARN: Invalid interval '{self.current_network_interval_str}', resetting.")
            self.current_network_interval_str = f"{DEFAULT_NETWORK_UPDATE_INTERVAL:.4f}"

    def update(self, dt):
        if self.screen.get_width() != self.screen_width or self.screen.get_height() != self.screen_height:
             # print("SettingsMenu: Screen resize detected, recalculating layout.") # Can be noisy
             self.screen_width = self.screen.get_width()
             self.screen_height = self.screen.get_height()
             self._setup_ui()
        active_input = self.input_active or self.ip_input_active or self.interval_input_active
        if active_input:
            self.cursor_timer += dt
            if self.cursor_timer >= 0.5:
                self.cursor_timer -= 0.5; self.show_cursor = not self.show_cursor
        else: self.show_cursor = False

    def draw(self):
        self.screen.fill(COLOR_SETTINGS_BG)
        center_x = self.screen_width // 2; label_offset_y = -30
        draw_text(self.screen, self.title, 70, center_x, 60, COLOR_MENU_TITLE, align="center")
        # Name
        draw_text(self.screen, "Player Name:", 24, self.name_input_rect.left, self.name_input_rect.top + label_offset_y, COLOR_UI_TEXT)
        pygame.draw.rect(self.screen, COLOR_UI_BG, self.name_input_rect)
        b_col = COLOR_INPUT_BOX_ACTIVE if self.input_active else COLOR_INPUT_BOX_INACTIVE
        pygame.draw.rect(self.screen, b_col, self.name_input_rect, 2)
        if font_medium:
            surf = font_medium.render(self.current_name, True, COLOR_WHITE)
            rect = surf.get_rect(midleft=(self.name_input_rect.left + 10, self.name_input_rect.centery))
            self.screen.blit(surf, rect)
            if self.input_active and self.show_cursor:
                cx = rect.right + 2; cy1, cy2 = self.name_input_rect.top + 5, self.name_input_rect.bottom - 5
                pygame.draw.line(self.screen, COLOR_WHITE, (cx, cy1), (cx, cy2), 2)
        # Colors
        draw_text(self.screen, "Player Color:", 24, self.color_swatch_rects[0].left, self.color_swatch_rects[0].top + label_offset_y, COLOR_UI_TEXT)
        for i, rect in enumerate(self.color_swatch_rects):
            pygame.draw.rect(self.screen, COLOR_PLAYER_OPTIONS[i], rect)
            b_col = COLOR_SELECTED_SWATCH_BORDER if i == self.selected_color_index else COLOR_BLACK
            b_width = 3 if i == self.selected_color_index else 1
            pygame.draw.rect(self.screen, b_col, rect, b_width)
        # Resolution
        draw_text(self.screen, "Resolution:", 24, self.res_display_rect.left, self.res_display_rect.top + label_offset_y, COLOR_UI_TEXT)
        mouse_pos = pygame.mouse.get_pos()
        a_col = COLOR_MENU_BUTTON_HOVER if self.res_left_arrow_rect.collidepoint(mouse_pos) else COLOR_MENU_BUTTON
        pygame.draw.rect(self.screen, a_col, self.res_left_arrow_rect)
        pygame.draw.polygon(self.screen, COLOR_WHITE, [(self.res_left_arrow_rect.right - 10, self.res_left_arrow_rect.top + 5), (self.res_left_arrow_rect.left + 10, self.res_left_arrow_rect.centery), (self.res_left_arrow_rect.right - 10, self.res_left_arrow_rect.bottom - 5)])
        a_col = COLOR_MENU_BUTTON_HOVER if self.res_right_arrow_rect.collidepoint(mouse_pos) else COLOR_MENU_BUTTON
        pygame.draw.rect(self.screen, a_col, self.res_right_arrow_rect)
        pygame.draw.polygon(self.screen, COLOR_WHITE, [(self.res_right_arrow_rect.left + 10, self.res_right_arrow_rect.top + 5), (self.res_right_arrow_rect.right - 10, self.res_right_arrow_rect.centery), (self.res_right_arrow_rect.left + 10, self.res_right_arrow_rect.bottom - 5)])
        pygame.draw.rect(self.screen, COLOR_UI_BG, self.res_display_rect)
        pygame.draw.rect(self.screen, COLOR_INPUT_BOX_INACTIVE, self.res_display_rect, 2)
        res_w, res_h = self.available_resolutions[self.current_resolution_index]
        res_text = f"{res_w} x {res_h}"
        if font_medium: draw_text(self.screen, res_text, 30, self.res_display_rect.centerx, self.res_display_rect.centery, COLOR_WHITE, align="center")
        # Interval
        int_label = f"Net Update Interval (s) [{self.min_net_interval:.2f}-{self.max_net_interval:.2f}]:" # Shorter label
        draw_text(self.screen, int_label, 24, self.interval_input_rect.left, self.interval_input_rect.top + label_offset_y, COLOR_UI_TEXT)
        pygame.draw.rect(self.screen, COLOR_UI_BG, self.interval_input_rect)
        b_col = COLOR_INPUT_BOX_ACTIVE if self.interval_input_active else COLOR_INPUT_BOX_INACTIVE
        pygame.draw.rect(self.screen, b_col, self.interval_input_rect, 2)
        if font_medium:
            surf = font_medium.render(self.current_network_interval_str, True, COLOR_WHITE)
            rect = surf.get_rect(midleft=(self.interval_input_rect.left + 10, self.interval_input_rect.centery))
            self.screen.blit(surf, rect)
            if self.interval_input_active and self.show_cursor:
                cx = rect.right + 2; cy1, cy2 = self.interval_input_rect.top + 5, self.interval_input_rect.bottom - 5
                pygame.draw.line(self.screen, COLOR_WHITE, (cx, cy1), (cx, cy2), 2)
        # IP
        draw_text(self.screen, "Host IP Address:", 24, self.ip_input_rect.left, self.ip_input_rect.top + label_offset_y, COLOR_UI_TEXT)
        pygame.draw.rect(self.screen, COLOR_UI_BG, self.ip_input_rect)
        b_col = COLOR_INPUT_BOX_ACTIVE if self.ip_input_active else COLOR_INPUT_BOX_INACTIVE
        pygame.draw.rect(self.screen, b_col, self.ip_input_rect, 2)
        if font_medium:
            surf = font_medium.render(self.current_ip, True, COLOR_WHITE)
            rect = surf.get_rect(midleft=(self.ip_input_rect.left + 10, self.ip_input_rect.centery))
            self.screen.blit(surf, rect)
            if self.ip_input_active and self.show_cursor:
                cx = rect.right + 2; cy1, cy2 = self.ip_input_rect.top + 5, self.ip_input_rect.bottom - 5
                pygame.draw.line(self.screen, COLOR_WHITE, (cx, cy1), (cx, cy2), 2)
        # Back Button
        back_color = COLOR_MENU_BUTTON_HOVER if self.back_button_rect.collidepoint(mouse_pos) else COLOR_MENU_BUTTON
        pygame.draw.rect(self.screen, back_color, self.back_button_rect)
        pygame.draw.rect(self.screen, COLOR_BLACK, self.back_button_rect, 2)
        draw_text(self.screen, "Back", 30, self.back_button_rect.centerx, self.back_button_rect.centery, COLOR_WHITE, align="center")

    def get_settings(self):
        self._validate_and_clamp_interval() # Final validation
        try: net_interval = float(self.current_network_interval_str)
        except ValueError: net_interval = DEFAULT_NETWORK_UPDATE_INTERVAL
        return {
            'name': self.current_name.strip() if self.current_name else "Player",
            'color_index': self.selected_color_index,
            'host_ip': self.current_ip.strip(),
            'resolution_index': self.current_resolution_index,
            'network_interval': net_interval,
        }

# --- Game Class ---
class Game:
    def __init__(self, screen, clock, player_settings, network_mode="sp", server=None, client=None, load_data=None): # Added load_data
        self.screen = screen
        current_screen_width = screen.get_width()
        current_screen_height = screen.get_height()
        # Calculate grid/map dimensions based on current screen size
        self.grid_width = current_screen_width // TILE_SIZE
        self.grid_height = (current_screen_height - UI_HEIGHT) // TILE_SIZE
        self.map_width_px = current_screen_width # Use screen width directly for map width
        self.map_height_px = self.grid_height * TILE_SIZE # Map height depends on grid
        print(f"Game Init: Screen={current_screen_width}x{current_screen_height}, Grid={self.grid_width}x{self.grid_height}, Map={self.map_width_px}x{self.map_height_px}")

        self.clock = clock
        self.player_settings = player_settings # This now holds the full app_config dict
        self.network_mode = network_mode
        self.server = server
        self.client = client
        self.running = True # Controls if the game state itself should continue (e.g., for ESC)

        # --- Initialize based on load_data or defaults ---
        if load_data:
            print("Initializing game from loaded save data...")
            # Initialize core attributes from loaded data first
            self.resources = load_data.get('resources', {RES_COPPER: STARTING_COPPER, RES_COAL: STARTING_COAL})
            self.wave_number = load_data.get('wave_number', 0)
            self.wave_timer = load_data.get('wave_timer', WAVE_COOLDOWN)
            self.in_wave = load_data.get('in_wave', False)
            self.game_over = load_data.get('game_over', False) # Load end game status
            self.game_won = load_data.get('game_won', False)
            # Other state (structures, players) initialized later via apply_full_snapshot
        else:
            print("Initializing new game...")
            # Default initialization for a new game
            self.resources = {RES_COPPER: STARTING_COPPER, RES_COAL: STARTING_COAL}
            self.wave_number = 0
            self.wave_timer = WAVE_COOLDOWN
            self.in_wave = False
            self.game_over = False
            self.game_won = False
        # --- END MODIFIED ---

        # --- Initialize containers (always needed) ---
        self.grid = [[None for _ in range(self.grid_height)] for _ in range(self.grid_width)]
        self.structures = {} # network_id -> Structure object
        self.enemies = {}    # network_id -> Enemy object
        self.projectiles = {}# network_id -> Projectile object
        self.core = None
        self.base_terrain = {} # (gx, gy) -> RES_TYPE (only stores resource patches)
        self.players = {}      # player_id -> Player object
        # ------------------------------------------

        self.local_player_id = None # Will be set based on mode/load/network assignment
        self.dt = 0.0               # Delta time for current frame

        # --- UI/Input State ---
        self.selected_building_type = BUILDING_NONE
        self.selected_orientation = EAST
        self.building_info = {
            BUILDING_DRILL: {'cost': DRILL_COST, 'class': Drill, 'name': 'Drill', 'section': 'Production'},
            BUILDING_CONVEYOR: {'cost': CONVEYOR_COST, 'class': Conveyor, 'name': 'Conveyor', 'section': 'Logistics'},
            BUILDING_TURRET: {'cost': TURRET_COST, 'class': Turret, 'name': 'Turret', 'section': 'Defense'},
            BUILDING_WALL: {'cost': WALL_COST, 'class': Wall, 'name': 'Wall', 'section': 'Defense'},
            BUILDING_COALGENERATOR: {'cost': COALGENERATOR_COST, 'class': CoalGenerator, 'name': 'Generator', 'section': 'Power'},
            BUILDING_POWERPOLE: {'cost': POWERPOLE_COST, 'class': PowerPole, 'name': 'Pole', 'section': 'Power'},
            BUILDING_BATTERY: {'cost': BATTERY_COST, 'class': Battery, 'name': 'Battery', 'section': 'Power'},
            BUILDING_RECONSTRUCTOR: {'cost': RECONSTRUCTOR_COST, 'class': Reconstructor, 'name': 'Reconstructor', 'section': 'Support'},
        }
        self.key_to_building_type = {pygame.K_0 + i: bt for i, bt in enumerate(self.building_info.keys(), 1)}
        self.preview_instances = self._create_preview_instances()
        # --- End UI/Input ---

        # --- Power Grid State ---
        self.power_nodes = []
        self.power_consumers = []
        self.power_grid_update_timer = 0.0
        self.power_grid_update_interval = POWER_NETWORK_STATS_UPDATE_INTERVAL
        self.hovered_power_node_id = None
        self.network_stats = None
        self.network_stats_timer = 0.0
        # --- End Power Grid ---

        # --- Wave/Enemy State ---
        # wave_number, wave_timer, in_wave initialized earlier based on load_data
        self.enemies_to_spawn_this_wave = 0
        self.enemies_spawned_this_wave = 0
        self.enemy_spawn_timer = 0.0
        self.current_enemy_hp = ENEMY_START_HP # Will be updated based on wave number
        self.max_waves = MAX_WAVES
        # Load next IDs from save data if available, else start at 0
        self.next_enemy_id = load_data.get('next_enemy_id', 0) if load_data else 0
        self.next_projectile_id = load_data.get('next_projectile_id', 0) if load_data else 0
        # --- End Wave/Enemy ---

        # --- Music Attributes ---
        self.game_music_files = sorted(glob.glob(GAME_MUSIC_FILES_PATTERN))
        self.current_song_index = -1 # No song selected initially
        self.music_playing = False # Tracks if we intend it to play (vs mixer's state)
        self.prev_button_rect = None
        self.play_pause_button_rect = None
        self.next_button_rect = None
        # Volume Slider Attributes
        # Use volume from player_settings (app_config) passed during creation
        self.current_volume = player_settings.get('volume', DEFAULT_MUSIC_VOLUME)
        self.volume_slider_track_rect = None
        self.volume_slider_handle_rect = None
        self.dragging_volume = False # Is the user currently dragging the handle?
        # Calculate initial UI positions (includes slider now)
        self._setup_music_controls_ui()
        if self.game_music_files:
            print(f"Found game music: {', '.join([os.path.basename(f) for f in self.game_music_files])}")
        else:
            print("WARN: No game music files found matching pattern.")
        # Set initial mixer volume for the game instance
        try:
            pygame.mixer.music.set_volume(self.current_volume)
        except pygame.error as e:
            print(f"WARN: Error setting initial game music volume: {e}")
        # --- END Music Attributes ---


        # --- Setup based on mode and load_data ---
        if self.network_mode == "client":
            # Client always waits for server state, no local setup needed here
            print("CLIENT: Waiting for initial game state from server...")
            # local_player_id will be assigned by server message
        elif load_data:
            # Apply the rest of the loaded state (structures, players, etc.)
            # We use apply_full_snapshot as it handles creating objects
            print("Applying snapshot from loaded save data...")
            try:
                # apply_full_snapshot will populate self.structures, self.players, etc.
                # It also handles self.base_terrain and self.core
                self.apply_full_snapshot(load_data)

                # --- Post-Load Validation ---
                # Ensure local player ID is set correctly for loaded SP/Host game
                self.local_player_id = 0 # Host/SP is always player 0
                if self.local_player_id not in self.players:
                     print("WARN: Player 0 not found in loaded save data for SP/Host. Creating default.")
                     # Create a default player 0 if missing, perhaps near core
                     px, py = (self.core.center_x, self.core.center_y - TILE_SIZE * 2) if self.core else (self.map_width_px/2, self.map_height_px/2)
                     pname = self.player_settings.get('name', "Player0") # Use current config name
                     cidx = self.player_settings.get('color_index', 0)  # Use current config color
                     self.players[self.local_player_id] = Player(px, py, self.local_player_id, name=pname, color_index=cidx)
                else:
                     # Optional: Update loaded player 0's name/color from current config?
                     # player0 = self.players[self.local_player_id]
                     # player0.name = self.player_settings.get('name', player0.name)
                     # player0.color_index = self.player_settings.get('color_index', player0.color_index)
                     # player0.color = COLOR_PLAYER_OPTIONS[player0.color_index % len(COLOR_PLAYER_OPTIONS)]
                     pass # Decide if player appearance should update on load

                # Recalculate derived state after loading
                if self.network_mode != "client": # SP or Host
                     self._rebuild_power_lists() # Populate power lists from loaded structures
                # Update current_enemy_hp based on loaded wave number
                self.current_enemy_hp = ENEMY_START_HP + max(0, self.wave_number - 1) * ENEMY_HP_INCREASE_PER_WAVE
                print(f"Applied loaded save data snapshot. NextEnemyID: {self.next_enemy_id}, Wave: {self.wave_number}")
                # --- End Post-Load Validation ---

            except Exception as e:
                print(f"ERROR applying loaded save data snapshot: {e}. Starting new game instead.")
                import traceback; traceback.print_exc() # More detailed error
                # Fallback to new game setup if loading fails badly
                self.resources = {RES_COPPER: STARTING_COPPER, RES_COAL: STARTING_COAL} # Reset basic state
                self.wave_number = 0; self.wave_timer = WAVE_COOLDOWN; self.in_wave = False
                self.game_over = False; self.game_won = False
                self.enemies = {}; self.projectiles = {}; self.structures = {} # Clear containers
                self.grid = [[None for _ in range(self.grid_height)] for _ in range(self.grid_width)] # Reset grid
                self.next_enemy_id = 0; self.next_projectile_id = 0
                self.local_player_id = 0 # Ensure local ID is set for new game
                self.setup_world() # Run new game setup

        else: # New Game Setup (SP or Host)
            self.local_player_id = 0 # Host/SP starts as player 0
            self.setup_world() # Creates core, initial player 0, resources
            if self.network_mode == "host" and self.server:
                 if self.server.initial_snapshot is None:
                     # Ensure snapshot reflects the newly created world
                     # Needs lock? Server might access this immediately.
                     with self.server.game_lock:
                         self.server.initial_snapshot = self.get_full_snapshot()
                     print("HOST: Initial snapshot created for new game.")
        # --- End Setup ---


    def _create_preview_instances(self):
        """Creates dummy instances of buildings for UI preview."""
        previews = {}
        for bt, info in self.building_info.items():
             # Provide necessary args for constructor, default orientation if needed
             args = (0, 0, self.selected_orientation) if bt == BUILDING_CONVEYOR else (0, 0)
             try:
                 # Use info['class'] which holds the actual class type
                 instance = info['class'](*args)
                 instance.tier = 1 # Set default tier for preview
                 # Call update_stats if the preview instance has it (for correct HP/visuals)
                 if hasattr(instance, 'update_stats'):
                     instance.update_stats()
                 previews[bt] = instance
             except Exception as e:
                 print(f"Error creating preview instance for {info['name']}: {e}")
        return previews

    def get_next_enemy_id(self):
        """Generates a unique network ID for a new enemy (Server/SP)."""
        self.next_enemy_id += 1
        return f"e_{self.next_enemy_id}"

    def get_next_projectile_id(self):
        """Generates a unique network ID for a new projectile (Server/SP)."""
        self.next_projectile_id += 1
        return f"p_{self.next_projectile_id}"

    def setup_world(self):
        """Initializes a new game world (Server/SP only)."""
        if self.network_mode == "client": return # Clients receive world state

        print(f"SERVER/SP: Setting up NEW world for grid {self.grid_width}x{self.grid_height}...")
        self.base_terrain.clear()
        self.structures.clear()
        self.enemies.clear()
        self.projectiles.clear()
        self.players.clear()
        self.grid = [[None for _ in range(self.grid_height)] for _ in range(self.grid_width)] # Clear grid

        # --- Place Core ---
        core_gx = self.grid_width // 2
        core_gy = self.grid_height - 4 # Place near bottom middle
        # Clamp core position to be valid
        core_gx = max(0, min(core_gx, self.grid_width - 1))
        core_gy = max(0, min(core_gy, self.grid_height - 1))
        self.core = Core(core_gx, core_gy)
        self._add_structure_to_game(self.core) # Add core to grid and structures dict

        # --- Place Initial Player (Player 0) ---
        player_start_x, player_start_y = grid_to_world_center(core_gx, core_gy - 2) # Start near core
        # Clamp player start position
        player_start_x = max(TILE_SIZE, min(player_start_x, self.map_width_px - TILE_SIZE))
        player_start_y = max(TILE_SIZE, min(player_start_y, self.map_height_px - TILE_SIZE))
        # Use current config for player name/color
        player_name = self.player_settings.get('name', "Player0")
        color_index = self.player_settings.get('color_index', 0)
        host_player = Player(player_start_x, player_start_y, self.local_player_id, name=player_name, color_index=color_index)
        self.players[self.local_player_id] = host_player

        # --- Generate Resource Patches ---
        # Scale number of patches roughly with map area
        num_patches = int(65 * (self.grid_width * self.grid_height) / (40*19))
        min_dist_from_core_sq = (6 * TILE_SIZE)**2 # Min distance from core center
        coal_ratio = 4 # Roughly 1 coal for every 3 copper
        placed_patches = 0
        max_attempts_total = num_patches * 150 # Limit attempts to prevent infinite loop
        current_attempts = 0

        core_center_x, core_center_y = self.core.center_x, self.core.center_y

        while placed_patches < num_patches and current_attempts < max_attempts_total:
            current_attempts += 1
            res_type = RES_COAL if (placed_patches + 1) % coal_ratio == 0 else RES_COPPER
            # Choose random grid location, avoiding edges slightly
            gx = random.randint(1, self.grid_width - 2)
            gy = random.randint(1, self.grid_height - 2)

            # Check if tile is empty (no structure or existing base terrain)
            is_tile_free = (self.grid[gx][gy] is None and (gx, gy) not in self.base_terrain)
            # Check distance from core
            patch_center_x, patch_center_y = grid_to_world_center(gx, gy)
            dist_sq = distance_sq(patch_center_x, patch_center_y, core_center_x, core_center_y)
            dist_ok = (dist_sq > min_dist_from_core_sq)

            if is_tile_free and dist_ok:
                # Check immediate neighbors (including diagonals) for other resources to prevent clumping
                is_clear_around = True
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        if dx == 0 and dy == 0: continue
                        nx, ny = gx + dx, gy + dy
                        # Check bounds and if neighbor is already a resource patch
                        if 0 <= nx < self.grid_width and 0 <= ny < self.grid_height:
                            if (nx, ny) in self.base_terrain:
                                is_clear_around = False; break
                    if not is_clear_around: continue # Skip if neighbor is resource

                if is_clear_around:
                    # Place the patch
                    self.base_terrain[(gx, gy)] = res_type
                    # Create a ResourcePatch object for drawing, but don't store in self.structures
                    patch_obj = ResourcePatch(gx, gy, res_type)
                    if 0 <= gx < self.grid_width and 0 <= gy < self.grid_height:
                        self.grid[gx][gy] = patch_obj # Place visual representation on grid
                    placed_patches += 1

        print(f"SERVER/SP: New world setup complete. {placed_patches}/{num_patches} resource patches placed.")
        # --- End Resource Generation ---

        self._rebuild_power_lists() # Ensure power lists are correct after setup

    # --- Structure Management Methods ---
    def get_structure_at(self, gx, gy):
        """Gets the structure object at the given grid coordinates, if any."""
        if 0 <= gx < self.grid_width and 0 <= gy < self.grid_height:
            return self.grid[gx][gy]
        return None

    def get_structure_by_id(self, network_id):
        """Gets a structure object by its unique network ID."""
        return self.structures.get(network_id)

    def _add_structure_to_game(self, structure_obj):
        """Adds a structure to the grid and internal dictionary. Handles overwriting/drills on patches."""
        gx, gy = structure_obj.grid_x, structure_obj.grid_y
        if not (0 <= gx < self.grid_width and 0 <= gy < self.grid_height):
            print(f"WARN: Attempted to add structure outside grid bounds ({gx},{gy})")
            return False

        existing_on_grid = self.grid[gx][gy]
        is_drill_on_patch = isinstance(structure_obj, Drill) and isinstance(existing_on_grid, ResourcePatch)

        # If placing something other than a drill, or placing a drill on non-patch, remove existing structure first
        if not is_drill_on_patch and existing_on_grid is not None and existing_on_grid.building_type != BUILDING_RESOURCE:
            print(f"INFO: Overwriting existing structure {type(existing_on_grid).__name__} at ({gx},{gy})")
            self._remove_structure_from_game(existing_on_grid) # Remove from dicts and power lists

        # Place new structure on grid
        self.grid[gx][gy] = structure_obj
        # Add to structures dictionary using its network ID
        self.structures[structure_obj.network_id] = structure_obj

        # Update power network tracking (Server/SP only)
        if self.network_mode != "client":
            self._update_power_lists_add(structure_obj)

        # Special setup for drills (Server/SP only)
        if isinstance(structure_obj, Drill) and self.network_mode != "client":
            structure_obj.setup_on_patch(self) # Checks if it's on a valid patch type

        # print(f"DEBUG: Added {type(structure_obj).__name__} ({structure_obj.network_id}) at ({gx},{gy})")
        return True

    def _remove_structure_from_game(self, structure_obj):
        """Removes a structure from the grid and internal dictionary."""
        if structure_obj is None: return
        gx, gy = structure_obj.grid_x, structure_obj.grid_y
        removed_id = structure_obj.network_id

        # Remove from structures dictionary
        if removed_id in self.structures:
            del self.structures[removed_id]
            # print(f"DEBUG: Removed {type(structure_obj).__name__} ({removed_id}) from dict.")
        else:
            # This might happen if removing a ResourcePatch visual, which isn't in self.structures
            # print(f"DEBUG: Structure {removed_id} not found in dict during removal.")
            pass

        # Update power network tracking (Server/SP only)
        if self.network_mode != "client":
            self._update_power_lists_remove(structure_obj)

        # Update grid display: Replace with ResourcePatch if base terrain exists, else None
        if 0 <= gx < self.grid_width and 0 <= gy < self.grid_height and self.grid[gx][gy] == structure_obj:
             base_type = self.base_terrain.get((gx, gy)) # Check if it was originally a resource patch
             if base_type:
                 self.grid[gx][gy] = ResourcePatch(gx, gy, base_type) # Restore visual patch
             else:
                 self.grid[gx][gy] = None # Clear the grid cell

    def _rebuild_power_lists(self):
        """Re-populates the power_nodes and power_consumers lists from self.structures. (Server/SP only)"""
        if self.network_mode == "client": return
        self.power_nodes.clear()
        self.power_consumers.clear()
        for struct in self.structures.values():
            if struct.is_power_node:
                self.power_nodes.append(struct)
            if struct.is_power_consumer:
                self.power_consumers.append(struct)
        print(f"DEBUG: Rebuilt power lists: {len(self.power_nodes)} nodes, {len(self.power_consumers)} consumers.")

    def _update_power_lists_add(self, obj):
        """Adds a structure to power lists if applicable (Server/SP only)."""
        if self.network_mode == "client": return
        if obj.is_power_node and obj not in self.power_nodes:
            self.power_nodes.append(obj)
        if obj.is_power_consumer and obj not in self.power_consumers:
            self.power_consumers.append(obj)

    def _update_power_lists_remove(self, obj):
        """Removes a structure from power lists if applicable (Server/SP only)."""
        if self.network_mode == "client": return
        if obj.is_power_node and obj in self.power_nodes:
            try: self.power_nodes.remove(obj)
            except ValueError: pass # Ignore if already removed somehow
        if obj.is_power_consumer and obj in self.power_consumers:
            try: self.power_consumers.remove(obj)
            except ValueError: pass

    # --- Player Actions (Server/SP Authoritative Logic) ---
    def action_place_structure(self, player_id, building_type, gx, gy, orientation):
        """Attempts to place a structure, called by server/SP based on input."""
        if self.network_mode == "client": return False # Clients don't execute actions directly
        player = self.players.get(player_id)
        info = self.building_info.get(building_type)
        if not player or not info or building_type == BUILDING_NONE: return False

        # 1. Check Validity: Bounds, Cost, Radius, Tile Occupation
        if not (0 <= gx < self.grid_width and 0 <= gy < self.grid_height): return False
        cost = info['cost']
        if not all(self.resources.get(res, 0) >= amount for res, amount in cost.items()): return False
        target_center_x, target_center_y = grid_to_world_center(gx, gy)
        radius_sq = PLAYER_BUILD_RADIUS * PLAYER_BUILD_RADIUS
        if distance_sq(player.world_x, player.world_y, target_center_x, target_center_y) > radius_sq: return False

        existing = self.get_structure_at(gx, gy)
        BuildingClass = info['class']
        is_drill_on_patch = (BuildingClass == Drill and isinstance(existing, ResourcePatch))
        is_empty = (existing is None)

        # Allow placing drills only on resource patches, other buildings only on empty tiles
        if not (is_drill_on_patch or (is_empty and BuildingClass != Drill)):
            # print(f"DEBUG: Placement failed - Invalid tile target for {BuildingClass.__name__} at ({gx},{gy}). Existing: {type(existing).__name__ if existing else 'None'}")
            return False

        # 2. Deduct Cost & Create Structure
        print(f"SERVER/SP: Player {player_id} placing {info['name']} at ({gx},{gy})")
        for res, amount in cost.items(): self.resources[res] -= amount

        # Instantiate the new building
        new_structure = None
        try:
             if building_type == BUILDING_CONVEYOR:
                 new_structure = BuildingClass(gx, gy, orientation)
             else:
                 new_structure = BuildingClass(gx, gy)
        except Exception as e:
             print(f"ERROR: Failed to instantiate {BuildingClass.__name__}: {e}")
             # Refund cost if instantiation failed
             for res, amount in cost.items(): self.resources[res] += amount
             return False

        # 3. Add to Game State
        if not self._add_structure_to_game(new_structure):
            print(f"ERROR: Server/SP failed _add_structure_to_game for {info['name']}!")
            # Refund cost if adding failed
            for res, amount in cost.items(): self.resources[res] += amount
            return False

        # 4. Broadcast (Host only)
        if self.network_mode == "host" and self.server:
            state = new_structure.get_state();
            if state:
                self.server.broadcast_message({'type': 'structure_add', 'data': state})
            else:
                 print(f"WARN: Failed to get state for new structure {new_structure.network_id}")

        return True

    def action_remove_structure(self, player_id, gx, gy):
        """Attempts to remove a structure, called by server/SP based on input."""
        if self.network_mode == "client": return False
        player = self.players.get(player_id)
        struct_to_remove = self.get_structure_at(gx, gy)
        if not player or not struct_to_remove: return False

        # 1. Check Validity: Cannot remove Core or Resource Patches, Check Radius
        if struct_to_remove.building_type in [BUILDING_CORE, BUILDING_RESOURCE]: return False
        target_center_x, target_center_y = grid_to_world_center(gx, gy)
        radius_sq = PLAYER_BUILD_RADIUS * PLAYER_BUILD_RADIUS
        if distance_sq(player.world_x, player.world_y, target_center_x, target_center_y) > radius_sq: return False

        # 2. Refund Resources & Remove Structure
        print(f"SERVER/SP: Player {player_id} removing {type(struct_to_remove).__name__} at ({gx},{gy})")
        for res, amount in struct_to_remove.cost.items():
            self.resources[res] = self.resources.get(res, 0) + int(amount * DELETE_REFUND_RATIO)

        removed_id = struct_to_remove.network_id # Get ID before removing
        self._remove_structure_from_game(struct_to_remove)

        # 3. Broadcast (Host only)
        if self.network_mode == "host" and self.server:
            self.server.broadcast_message({'type': 'structure_remove', 'net_id': removed_id})

        return True

    def action_upgrade_structure(self, player_id, gx, gy):
        """Attempts to upgrade a structure, called by server/SP based on input."""
        if self.network_mode == "client": return False
        player = self.players.get(player_id)
        target = self.get_structure_at(gx, gy)
        if not player or not target: return False

        # 1. Check Validity: Radius, Can Upgrade?, Afford Cost
        target_center_x, target_center_y = grid_to_world_center(gx, gy)
        radius_sq = PLAYER_BUILD_RADIUS * PLAYER_BUILD_RADIUS
        if distance_sq(player.world_x, player.world_y, target_center_x, target_center_y) > radius_sq: return False
        if not target.can_upgrade(): return False

        cost = target.get_next_upgrade_cost();
        if cost is None: return False # Should be caught by can_upgrade, but safety check
        if not all(self.resources.get(res, 0) >= amount for res, amount in cost.items()): return False

        # 2. Deduct Cost & Apply Upgrade
        for res, amount in cost.items(): self.resources[res] -= amount

        # Store power status before upgrade
        was_consumer = target.is_power_consumer
        was_node = target.is_power_node

        success = target.apply_upgrade(self) # This increments tier and updates stats

        # 3. Handle State Changes & Broadcast
        if success:
            # Update power lists if role changed (Server/SP only)
            if self.network_mode != "client":
                if (target.is_power_consumer != was_consumer or target.is_power_node != was_node):
                    print(f"DEBUG: Power role changed for {target.network_id} on upgrade.")
                    self._update_power_lists_remove(target) # Remove with old role
                    self._update_power_lists_add(target)    # Add with new role

            # Broadcast updated state (Host only)
            if self.network_mode == "host" and self.server:
                 state = target.get_state()
                 if state:
                     self.server.broadcast_message({'type': 'structure_update', 'data': state})
                 else:
                      print(f"WARN: Failed to get state for upgraded structure {target.network_id}")
        else:
            # If upgrade failed internally (shouldn't happen if checks pass), refund cost
            print(f"ERROR: Server/SP apply_upgrade method failed unexpectedly for {target.network_id}!")
            for res, amount in cost.items(): self.resources[res] += amount

        return success
    # --- End Player Actions ---


    # --- Enemy & Projectile Management ---
    def get_enemy_by_id(self, network_id):
        """Gets an enemy object by its unique network ID."""
        return self.enemies.get(network_id)

    def get_projectile_by_id(self, network_id):
        """Gets a projectile object by its unique network ID."""
        return self.projectiles.get(network_id)

    def spawn_enemy(self):
        """Creates a new enemy at the edge of the map (Server/SP only)."""
        if self.network_mode == "client": return
        if not self.core:
             print("WARN: Cannot spawn enemy, core does not exist.")
             return # Don't spawn if core is gone

        # Choose spawn edge and position
        edge = random.choice(['top', 'left', 'right'])
        margin = TILE_SIZE * 1.5 # Spawn slightly off-screen
        sx, sy = 0.0, 0.0

        if edge == 'top':
            sx = random.uniform(margin, self.map_width_px - margin)
            sy = -margin
        elif edge == 'left':
            sx = -margin
            sy = random.uniform(margin, self.map_height_px - margin)
        else: # Right edge
            sx = self.map_width_px + margin
            sy = random.uniform(margin, self.map_height_px - margin)

        enemy_id = self.get_next_enemy_id()
        core_coords = (self.core.center_x, self.core.center_y)

        # Use current_enemy_hp which is updated based on wave number
        new_enemy = Enemy(sx, sy, core_coords, self.current_enemy_hp, ENEMY_SPEED, ENEMY_DAMAGE, ENEMY_ATTACK_COOLDOWN, enemy_id)
        self.enemies[enemy_id] = new_enemy

        # Broadcast new enemy (Host only)
        if self.network_mode == "host" and self.server:
             state = new_enemy.get_state()
             if state:
                 self.server.broadcast_message({'type': 'enemy_add', 'data': state})

    # --- Power Grid (Server/SP Only Calculation) ---
    def update_power_grid(self):
            """Server/SP: Recalculates power distribution across all networks."""
            if self.network_mode == "client": return

            # 1. Reset Status on all potential nodes and consumers
            for node in self.power_nodes:
                node.is_on_grid = False
                node.connected_nodes_coords.clear() # Clear visual connection data
                if node.is_power_storage:
                     node.is_charging = False
                     node.is_discharging = False
            for consumer in self.power_consumers:
                consumer.is_powered = False
                consumer.power_source_coords = None # Reset visual connection data

            # 2. Network Discovery using BFS from potential sources
            potential_seeds = [n for n in self.power_nodes if n.is_power_source or (n.is_power_storage and n.charge > 1e-9)]
            processed_nodes = set()
            all_networks = [] # List to store sets of nodes, each set is one independent network

            for seed_node in potential_seeds:
                if seed_node in processed_nodes:
                    continue # Already processed as part of another network

                current_network_nodes = set()
                queue = deque([(seed_node, 0)]) # Store (node, depth)
                visited_in_bfs = {seed_node}

                while queue:
                    current_node, depth = queue.popleft()

                    # Add to this network's node set and mark as processed globally
                    current_network_nodes.add(current_node)
                    processed_nodes.add(current_node)
                    current_node.is_on_grid = True # Mark node as connected

                    if depth >= POWER_SEARCH_DEPTH_LIMIT:
                        continue # Stop searching deeper from this branch

                    # Find neighbors within range
                    radius_grid_search = int(POWER_RADIUS / TILE_SIZE) + 1
                    for dx in range(-radius_grid_search, radius_grid_search + 1):
                        for dy in range(-radius_grid_search, radius_grid_search + 1):
                            if dx == 0 and dy == 0: continue

                            check_gx, check_gy = current_node.grid_x + dx, current_node.grid_y + dy
                            neighbor = self.get_structure_at(check_gx, check_gy)

                            # Check if valid neighbor: exists, is a power node, not visited yet, and within actual distance
                            if (neighbor and neighbor.is_power_node and
                                    neighbor not in visited_in_bfs and
                                    distance_sq(current_node.center_x, current_node.center_y, neighbor.center_x, neighbor.center_y) <= POWER_RADIUS ** 2):

                                visited_in_bfs.add(neighbor)
                                queue.append((neighbor, depth + 1))

                                # Store visual connection coordinates (avoid duplicates)
                                curr_coords = (current_node.center_x, current_node.center_y)
                                neighbor_coords = (neighbor.center_x, neighbor.center_y)
                                if neighbor_coords not in current_node.connected_nodes_coords:
                                    current_node.connected_nodes_coords.append(neighbor_coords)
                                if curr_coords not in neighbor.connected_nodes_coords:
                                    neighbor.connected_nodes_coords.append(curr_coords)

                if current_network_nodes: # If BFS found any nodes
                    all_networks.append(current_network_nodes)

            # 3. Calculate Balance & Set Status Per Network
            delta_time = self.dt # Use frame delta time for calculations

            for network_nodes_set in all_networks:
                # Calculate total generation in this network
                total_generation_rate = sum(COALGENERATOR_POWER_OUTPUT for n in network_nodes_set if n.building_type == BUILDING_COALGENERATOR and n.is_power_source) # is_power_source set in CoalGenerator.update

                # Find consumers connected to THIS network and sum their consumption
                consumers_in_this_network = [] # Store tuples (consumer, closest_node_in_network)
                total_consumption_rate = 0.0
                for consumer in self.power_consumers:
                    closest_node = self.find_closest_node_in_set(consumer, network_nodes_set)
                    if closest_node: # If consumer is close enough to a node in this network
                        consumers_in_this_network.append((consumer, closest_node))
                        total_consumption_rate += consumer.power_consumption

                # Calculate battery potential for this network
                batteries_in_network = [n for n in network_nodes_set if n.is_power_storage]
                max_possible_discharge_rate = sum(b.discharge_rate for b in batteries_in_network if b.charge > 1e-9)
                total_available_discharge_amount = sum(min(b.charge, b.discharge_rate * delta_time) for b in batteries_in_network) # Max energy batteries can provide this frame
                total_available_charge_room = sum(min(b.capacity - b.charge, b.charge_rate * delta_time) for b in batteries_in_network) # Max energy batteries can absorb this frame

                # 4. Determine Sufficiency
                is_power_sufficient = (total_generation_rate + max_possible_discharge_rate >= total_consumption_rate - 1e-9)

                # 5/6. Set Status & Apply Charge/Discharge Amounts
                actual_charge_amount = 0.0
                actual_discharge_amount = 0.0

                if is_power_sufficient:
                    # Power all consumers connected to this network
                    for consumer, source_node in consumers_in_this_network:
                        consumer.is_powered = True
                        consumer.power_source_coords = (source_node.center_x, source_node.center_y) # For visual line

                    # Calculate net balance (positive = surplus, negative = deficit needing battery discharge)
                    power_balance = total_generation_rate - total_consumption_rate

                    if power_balance < -1e-9: # Deficit - need to discharge batteries
                        needed_discharge_amount = abs(power_balance) * delta_time
                        # Discharge only up to what's available
                        actual_discharge_amount = min(needed_discharge_amount, total_available_discharge_amount)
                    elif power_balance > 1e-9: # Surplus - can charge batteries
                        potential_charge_amount = power_balance * delta_time
                        # Charge only up to available room
                        actual_charge_amount = min(potential_charge_amount, total_available_charge_room)

                else: # Insufficient Power (Generation + Max Discharge < Consumption)
                    # No consumers are powered in this scenario in this simplified model
                    for consumer, source_node in consumers_in_this_network:
                        consumer.is_powered = False
                        consumer.power_source_coords = None # No power source visual

                    # Batteries might still charge slightly from generation if there's room
                    potential_charge_amount = total_generation_rate * delta_time
                    actual_charge_amount = min(potential_charge_amount, total_available_charge_room)
                    # No discharge happens if power is insufficient overall


                # Apply calculated charge/discharge to batteries proportionally
                if actual_discharge_amount > 1e-9 and total_available_discharge_amount > 1e-9:
                    discharge_fraction = actual_discharge_amount / total_available_discharge_amount
                    for battery in batteries_in_network:
                        provide = min(battery.charge, battery.discharge_rate * delta_time) * discharge_fraction
                        if provide > 1e-9:
                            battery.charge -= provide
                            battery.is_discharging = True # Set status for visual feedback
                if actual_charge_amount > 1e-9 and total_available_charge_room > 1e-9:
                     charge_fraction = actual_charge_amount / total_available_charge_room
                     for battery in batteries_in_network:
                         absorb = min(battery.capacity - battery.charge, battery.charge_rate * delta_time) * charge_fraction
                         if absorb > 1e-9:
                             battery.charge += absorb
                             battery.is_charging = True # Set status for visual feedback

    def find_closest_node_in_set(self, consumer, node_set):
        """Finds the closest power node in a given set to a consumer, within POWER_RADIUS."""
        closest_node = None
        min_dist_sq = POWER_RADIUS * POWER_RADIUS + 1 # Start slightly outside max radius

        for node in node_set:
            d_sq = distance_sq(consumer.center_x, consumer.center_y, node.center_x, node.center_y)
            if d_sq <= POWER_RADIUS * POWER_RADIUS and d_sq < min_dist_sq:
                min_dist_sq = d_sq
                closest_node = node
        return closest_node

    # --- Tooltip Calculation ---
    def calculate_network_stats(self, start_node_id):
        """Calculates display stats for the network connected to start_node_id.
           Uses the current (potentially client-side) game state."""
        start_node = self.get_structure_by_id(start_node_id)
        # Check if the node exists and is marked as being on a grid (state sync'd from server)
        if start_node is None or not start_node.is_power_node or not start_node.is_on_grid:
            self.network_stats = None # No stats if node isn't valid or isn't powered
            return

        stats = {'generation': 0.0, 'consumption': 0.0, 'capacity': 0.0, 'charge': 0.0, 'nodes': 0}
        network_node_ids = set() # Store IDs of nodes found in this network
        queue = deque([start_node_id])
        visited_ids = {start_node_id}

        # BFS using synced connection data (connected_nodes_coords)
        while queue:
            current_node_id = queue.popleft()
            current_node = self.get_structure_by_id(current_node_id)

            # Node must exist and be on the grid according to its state
            if current_node is None or not current_node.is_power_node or not current_node.is_on_grid:
                continue

            network_node_ids.add(current_node_id)
            stats['nodes'] += 1

            # Sum stats based on node type and state
            # Note: is_power_source for generator and charge for battery are synced from server state
            if current_node.building_type == BUILDING_COALGENERATOR and getattr(current_node, 'is_power_source', False):
                stats['generation'] += COALGENERATOR_POWER_OUTPUT
            if current_node.is_power_storage:
                stats['capacity'] += getattr(current_node, 'capacity', 0)
                stats['charge'] += getattr(current_node, 'charge', 0)

            # Explore neighbors using connected_nodes_coords
            # This requires finding node IDs corresponding to the coordinates
            for neighbor_coords in getattr(current_node, 'connected_nodes_coords', []):
                found_neighbor_id = None
                # Inefficient search for neighbor matching coords - OK for tooltip?
                for potential_id, potential_node in self.structures.items():
                    if (potential_node.is_power_node and potential_id not in visited_ids and
                            abs(potential_node.center_x - neighbor_coords[0]) < 1.0 and
                            abs(potential_node.center_y - neighbor_coords[1]) < 1.0):
                        found_neighbor_id = potential_id
                        break # Found the neighbor

                if found_neighbor_id:
                    visited_ids.add(found_neighbor_id)
                    queue.append(found_neighbor_id)

        # Now, find consumers potentially powered by this network
        # Check all consumers whose state indicates they are powered AND their source coords match a node in our found network
        for consumer in self.structures.values():
             # Check consumer status based on its synced state
             if consumer.is_power_consumer and getattr(consumer, 'is_powered', False):
                 source_coords = getattr(consumer, 'power_source_coords', None)
                 if source_coords:
                     # Check if the source coords match any node in the network we just BFS'd
                     for node_id in network_node_ids:
                         node = self.structures.get(node_id)
                         if node and abs(node.center_x - source_coords[0]) < 1.0 and abs(node.center_y - source_coords[1]) < 1.0:
                             # Found the source node within this network, count the consumption
                             stats['consumption'] += consumer.power_consumption
                             break # Count consumption only once per consumer

        self.network_stats = stats # Store calculated stats

    # --- Input Handling ---
    def handle_events(self, events):
        """Handles player input, UI interaction, and music controls."""
        local_player = self.players.get(self.local_player_id)

        # --- Update Local Player Movement Intent (Sent Separately if Client) ---
        keys = pygame.key.get_pressed()
        my, mx = (keys[pygame.K_s] - keys[pygame.K_w]), (keys[pygame.K_d] - keys[pygame.K_a])
        move_payload = None # Renamed to avoid clash
        direction_changed = False
        if local_player:
            if local_player.move_x != mx or local_player.move_y != my:
                direction_changed = True
                local_player.move_x, local_player.move_y = mx, my
                move_payload = {'action': 'move', 'data': {'x': mx, 'y': my}}
        if self.network_mode == "client" and self.client and move_payload and direction_changed:
            self.client.send_message({'type': 'input', 'payload': move_payload})
        # --- End Movement ---

        mouse_pos = pygame.mouse.get_pos()
        mouse_over_ui = mouse_pos[1] >= self.map_height_px
        mouse_gx, mouse_gy = world_to_grid(*mouse_pos)

        # --- Tooltip Hover Update ---
        new_hover_id = None
        if not mouse_over_ui:
            struct = self.get_structure_at(mouse_gx, mouse_gy)
            if struct and struct.is_power_node:
                new_hover_id = struct.network_id
        if new_hover_id != self.hovered_power_node_id:
            self.hovered_power_node_id = new_hover_id
            self.network_stats = None # Reset stats when hover changes
            self.network_stats_timer = 0
        # --- End Tooltip ---

        # --- Process Event Queue ---
        for event in events:
            # --- Per-Event Flags to check if UI handled this event ---
            slider_interacted = False
            button_interacted = False
            # -------------------------------------------------------

            if event.type == pygame.QUIT:
                self.running = False # Signal main loop to exit app
                continue # Skip rest of processing for this event

            # --- Handle Mouse Button Down ---
            if event.type == pygame.MOUSEBUTTONDOWN:
                # --- Volume Slider Drag Start / Track Click ---
                if event.button == 1:
                    if self.volume_slider_handle_rect and self.volume_slider_handle_rect.collidepoint(mouse_pos):
                        self.dragging_volume = True
                        slider_interacted = True
                    elif self.volume_slider_track_rect and self.volume_slider_track_rect.collidepoint(mouse_pos):
                        relative_x = mouse_pos[0] - self.volume_slider_track_rect.left
                        new_volume = max(0.0, min(1.0, relative_x / self.volume_slider_track_rect.width))
                        if abs(new_volume - self.current_volume) > 1e-3: # Update only if changed significantly
                             self.current_volume = new_volume
                             try: pygame.mixer.music.set_volume(self.current_volume)
                             except pygame.error as e: print(f"WARN: Set volume error: {e}")
                        self.volume_slider_handle_rect.centerx = self.volume_slider_track_rect.left + int(self.current_volume * self.volume_slider_track_rect.width)
                        slider_interacted = True
                # --------------------------------------------

                # --- Music Buttons Click ---
                if event.button == 1 and not slider_interacted and self.game_music_files:
                     if self.prev_button_rect and self.prev_button_rect.collidepoint(mouse_pos):
                         self.play_prev_song(); button_interacted = True
                     elif self.play_pause_button_rect and self.play_pause_button_rect.collidepoint(mouse_pos):
                         self.toggle_pause(); button_interacted = True
                     elif self.next_button_rect and self.next_button_rect.collidepoint(mouse_pos):
                         self.play_next_song(); button_interacted = True
                # -------------------------

                # --- Game Action Click (Build/Delete) ---
                if not slider_interacted and not button_interacted:
                    # Only process game actions if UI wasn't clicked and game not over/won
                    if not self.game_over and not self.game_won and not mouse_over_ui:
                        game_action_payload = None
                        if event.button == 1 and self.selected_building_type != BUILDING_NONE:
                            game_action_payload = {'action': 'place', 'data': {'type': self.selected_building_type, 'gx': mouse_gx, 'gy': mouse_gy, 'orient': self.selected_orientation}}
                        elif event.button == 3: # Right Click for Delete
                            game_action_payload = {'action': 'remove', 'data': {'gx': mouse_gx, 'gy': mouse_gy}}

                        # Process the game action payload
                        if game_action_payload:
                            if self.network_mode == "client" and self.client:
                                self.client.send_message({'type': 'input', 'payload': game_action_payload})
                            elif self.network_mode != "client": # Server or SP executes directly
                                action_type, data = game_action_payload['action'], game_action_payload['data']
                                if action_type == 'place': self.action_place_structure(self.local_player_id, data['type'], data['gx'], data['gy'], data['orient'])
                                elif action_type == 'remove': self.action_remove_structure(self.local_player_id, data['gx'], data['gy'])
                # ---------------------------------------

            # --- Handle Mouse Button Up ---
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 and self.dragging_volume:
                    self.dragging_volume = False
                    # slider_interacted = True # Mouse up after drag isn't really an interaction needing to block others
            # ---------------------------

            # --- Handle Mouse Motion ---
            elif event.type == pygame.MOUSEMOTION:
                if self.dragging_volume:
                    clamped_x = max(self.volume_slider_track_rect.left, min(mouse_pos[0], self.volume_slider_track_rect.right))
                    relative_x = clamped_x - self.volume_slider_track_rect.left
                    new_volume = relative_x / self.volume_slider_track_rect.width
                    # Update volume only if dragging and value changed
                    if abs(new_volume - self.current_volume) > 1e-3:
                         self.current_volume = new_volume
                         try: pygame.mixer.music.set_volume(self.current_volume)
                         except pygame.error as e: print(f"WARN: Set volume error: {e}")
                    self.volume_slider_handle_rect.centerx = clamped_x
                    # slider_interacted = True # Dragging doesn't need to block other events like key presses
            # --------------------------

            # --- Handle Key Down ---
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False # Signal to main loop to exit game state/menu
                    continue # Don't process other keys if ESC pressed

                # Ignore game keys if game ended
                if self.game_over or self.game_won: continue

                key = event.key
                key_action_payload = None

                # Building Selection / Deselection / Rotation
                if key == pygame.K_0: self.selected_building_type = BUILDING_NONE
                elif key == pygame.K_r and self.selected_building_type == BUILDING_CONVEYOR:
                    self.selected_orientation = (self.selected_orientation + 1) % 4
                    preview = self.preview_instances.get(BUILDING_CONVEYOR)
                    if preview: preview.orientation = self.selected_orientation
                elif key in self.key_to_building_type:
                    selected = self.key_to_building_type[key]
                    if self.selected_building_type != selected:
                        self.selected_building_type = selected; self.selected_orientation = EAST

                # Upgrade Action
                elif key == pygame.K_u and self.selected_building_type == BUILDING_NONE and not mouse_over_ui:
                    struct_to_upgrade = self.get_structure_at(mouse_gx, mouse_gy)
                    if struct_to_upgrade and struct_to_upgrade.building_type != BUILDING_RESOURCE:
                         key_action_payload = {'action': 'upgrade', 'data': {'gx': mouse_gx, 'gy': mouse_gy}}

                # Send key-based game actions
                if key_action_payload:
                    if self.network_mode == "client" and self.client:
                        self.client.send_message({'type': 'input', 'payload': key_action_payload})
                    elif self.network_mode != "client": # Server or SP executes directly
                         if key_action_payload['action'] == 'upgrade':
                             self.action_upgrade_structure(self.local_player_id, **key_action_payload['data'])
            # ----------------------

            # --- End of event processing for this specific event ---
        # --- End of Event Queue Processing for this frame ---

    # --- Update Logic ---
    def update(self):
        """Updates the game state for one frame."""
        if not self.running: return # Should not be called if not running, but safety check

        # --- Server / Single Player Update Logic ---
        if self.network_mode in ["host", "sp"]:
            # Update Players
            for player in self.players.values():
                player.update(self.dt, self) # Pass self for map bounds

            # Update Structures
            # Iterate over list copy in case structures are added/removed during update
            for struct in list(self.structures.values()):
                struct.update(self) # Includes drills, generators, turrets finding targets, etc.

            # Update Enemies
            for enemy in list(self.enemies.values()):
                enemy.update(self) # Movement, targeting, attacking

            # Update Projectiles
            for proj in list(self.projectiles.values()):
                proj.update(self) # Movement, collision check

            # Update Power Grid periodically
            self.power_grid_update_timer += self.dt
            if self.power_grid_update_timer >= self.power_grid_update_interval:
                self.power_grid_update_timer = 0.0 # Reset timer
                self.update_power_grid()

            # --- Cleanup Destroyed Entities ---
            destroyed_structure_ids = [sid for sid, s in self.structures.items() if s.destroyed]
            core_destroyed_this_frame = False
            for sid in destroyed_structure_ids:
                 if sid in self.structures: # Check if not already removed
                     if self.structures[sid].building_type == BUILDING_CORE:
                         core_destroyed_this_frame = True
                     self._remove_structure_from_game(self.structures[sid])

            destroyed_enemy_ids = [eid for eid, e in self.enemies.items() if e.destroyed]
            for eid in destroyed_enemy_ids:
                 if eid in self.enemies: del self.enemies[eid] # Remove from dict

            destroyed_projectile_ids = [pid for pid, p in self.projectiles.items() if p.destroyed]
            for pid in destroyed_projectile_ids:
                 if pid in self.projectiles: del self.projectiles[pid] # Remove from dict

            # Broadcast removals if host
            if self.network_mode == "host" and self.server:
                 if destroyed_structure_ids: self.server.broadcast_message({'type': 'structures_remove', 'ids': destroyed_structure_ids})
                 if destroyed_enemy_ids: self.server.broadcast_message({'type': 'enemies_remove', 'ids': destroyed_enemy_ids})
                 if destroyed_projectile_ids: self.server.broadcast_message({'type': 'projectiles_remove', 'ids': destroyed_projectile_ids})
            # --- End Cleanup ---


            # --- Wave Management ---
            if not self.game_over and not self.game_won: # Only manage waves if game is active
                self.wave_timer -= self.dt

                # Start new wave if cooldown finished
                if not self.in_wave and self.wave_timer <= 0 and self.wave_number < self.max_waves:
                    self.in_wave = True
                    self.wave_number += 1
                    self.enemies_to_spawn_this_wave = 10 + self.wave_number * 5 # Example scaling
                    self.enemies_spawned_this_wave = 0
                    self.current_enemy_hp = ENEMY_START_HP + (self.wave_number - 1) * ENEMY_HP_INCREASE_PER_WAVE
                    self.wave_timer = WAVE_DURATION # Set timer for wave duration
                    self.enemy_spawn_timer = 0 # Reset spawn timer for the new wave
                    print(f"SERVER/SP: --- Wave {self.wave_number}/{self.max_waves} Started (HP: {self.current_enemy_hp}) ---")
                    # Broadcast wave update if host
                    if self.network_mode == "host" and self.server:
                         self.server.broadcast_message({'type': 'wave_update', 'data': {'number': self.wave_number, 'timer': self.wave_timer, 'in_wave': self.in_wave}})


                # Spawn enemies during a wave
                if self.in_wave and self.enemies_spawned_this_wave < self.enemies_to_spawn_this_wave:
                    self.enemy_spawn_timer -= self.dt
                    if self.enemy_spawn_timer <= 0:
                        self.spawn_enemy()
                        self.enemies_spawned_this_wave += 1
                        # Calculate next spawn time (distribute over wave duration with some randomness)
                        base_interval = WAVE_DURATION / self.enemies_to_spawn_this_wave if self.enemies_to_spawn_this_wave > 0 else ENEMY_SPAWN_RATE
                        self.enemy_spawn_timer = max(0.1, base_interval * random.uniform(0.7, 1.3)) # Add jitter, ensure minimum delay

                # End wave conditions
                wave_ended_naturally = self.in_wave and self.wave_timer <= 0
                wave_cleared = self.in_wave and self.enemies_spawned_this_wave >= self.enemies_to_spawn_this_wave and not self.enemies

                if wave_ended_naturally or wave_cleared:
                    result = 'Cleared' if not self.enemies else 'Ended'
                    print(f"SERVER/SP: --- Wave {self.wave_number} {result} ---")
                    self.in_wave = False
                    self.wave_timer = WAVE_COOLDOWN # Start cooldown for next wave
                     # Broadcast wave update if host
                    if self.network_mode == "host" and self.server:
                         self.server.broadcast_message({'type': 'wave_update', 'data': {'number': self.wave_number, 'timer': self.wave_timer, 'in_wave': self.in_wave}})

            # --- Game End Conditions ---
            if core_destroyed_this_frame and not self.game_over:
                self.game_over = True
                print("SERVER/SP: --- GAME OVER --- Core Destroyed!")
                # Broadcast game status if host
                if self.network_mode == "host" and self.server:
                    self.server.broadcast_message({'type': 'game_status', 'status': 'over'})

            # Check win condition (only if not already won/lost)
            if not self.game_over and not self.game_won:
                if self.wave_number >= self.max_waves and not self.in_wave and not self.enemies:
                     self.game_won = True
                     print("SERVER/SP: --- YOU WIN! --- All waves survived!")
                     # Broadcast game status if host
                     if self.network_mode == "host" and self.server:
                          self.server.broadcast_message({'type': 'game_status', 'status': 'won'})
            # --- End Game End ---

        # --- Client Update Logic ---
        elif self.network_mode == "client":
            # Clients mainly rely on server state updates (apply_full_snapshot / apply_incremental_update)
            # Client-side updates are mostly for visual smoothing / prediction / local effects

            # Update structure animations (e.g., conveyor item movement) based on last known state
            for struct in self.structures.values():
                struct.client_update(self.dt) # Handles item progress on conveyors visually

            # Update projectile positions visually based on last known velocity
            for proj in self.projectiles.values():
                proj.client_update(self.dt) # Simple linear movement

            # Update local player visual position (can add prediction/interpolation later)
            local_player = self.players.get(self.local_player_id)
            if local_player:
                local_player.update(self.dt, self) # Update visual pos using self for bounds

            # Update network stats tooltip calculation timer
            if self.hovered_power_node_id:
                self.network_stats_timer += self.dt
                if self.network_stats is None or self.network_stats_timer >= POWER_NETWORK_STATS_UPDATE_INTERVAL:
                    self.network_stats_timer = 0
                    self.calculate_network_stats(self.hovered_power_node_id)
            else:
                 self.network_stats = None # Clear stats if not hovering

        # --- End Client Update ---

    # --- Drawing Logic ---
    def draw_grid(self):
        """Draws the background grid lines."""
        map_end_y = self.map_height_px
        grid_line_color = (60, 60, 60)
        current_w = self.screen.get_width()
        # Vertical lines
        for x in range(0, current_w, TILE_SIZE):
            pygame.draw.line(self.screen, grid_line_color, (x, 0), (x, map_end_y), 1)
        # Horizontal lines
        for y in range(0, int(map_end_y) + 1, TILE_SIZE):
            pygame.draw.line(self.screen, grid_line_color, (0, y), (current_w, y), 1)

    def draw_base_terrain(self):
        """Draws the resource patches on the ground."""
        for (gx, gy), res_type in self.base_terrain.items():
             # Draw background color of the patch
             color = COLOR_COPPER if res_type == RES_COPPER else COLOR_COAL
             world_x, world_y = grid_to_world(gx, gy)
             rect = pygame.Rect(world_x, world_y, TILE_SIZE, TILE_SIZE)
             pygame.draw.rect(self.screen, color, rect)
             pygame.draw.rect(self.screen, COLOR_BLACK, rect, 1) # Border

             # Draw small indicator circle in the center
             indicator_color = COLOR_BLACK if res_type == RES_COAL else COLOR_DARK_GRAY
             cx, cy = grid_to_world_center(gx, gy)
             pygame.draw.circle(self.screen, indicator_color, (int(cx), int(cy)), TILE_SIZE // 5, 2)

    def draw_power_grid_connections(self):
        """Draws power lines between connected nodes and from sources to consumers."""
        drawn_connections = set() # Prevents drawing lines twice between nodes
        line_color = COLOR_POWER_LINE

        # 1. Draw connections between connected power NODES based on their synced state
        for struct in self.structures.values():
            # Node must exist, be a node, and be marked as on_grid in its state
            if struct.is_power_node and getattr(struct, 'is_on_grid', False):
                node_center_int = (int(struct.center_x), int(struct.center_y))
                # Use the synced coordinates list to draw lines
                for neighbor_coords in getattr(struct, 'connected_nodes_coords', []):
                    neighbor_center_int = (int(neighbor_coords[0]), int(neighbor_coords[1]))
                    # Create sorted tuple key to avoid duplicates (A->B vs B->A)
                    connection_key = tuple(sorted((node_center_int, neighbor_center_int)))
                    if connection_key not in drawn_connections:
                        pygame.draw.line(self.screen, line_color, node_center_int, neighbor_center_int, 1)
                        drawn_connections.add(connection_key)

        # 2. Draw connections from source nodes to *OPERATIONAL* consumers based on state
        for struct in self.structures.values():
             # Consumer must exist, be a consumer, be powered, AND have source coords synced
             if (struct.is_power_consumer and
                     getattr(struct, 'is_powered', False) and
                     hasattr(struct, 'power_source_coords') and
                     struct.power_source_coords): # Ensure coords are not None

                 source_coords = struct.power_source_coords
                 source_center_int = (int(source_coords[0]), int(source_coords[1]))
                 consumer_center_int = (int(struct.center_x), int(struct.center_y))
                 # Draw the line from the synced source coords to the consumer center
                 pygame.draw.line(self.screen, line_color, source_center_int, consumer_center_int, 1)

    def draw_build_preview(self):
        """Draws the ghost image of the selected building under the cursor."""
        if self.selected_building_type == BUILDING_NONE: return
        local_player = self.players.get(self.local_player_id)
        if not local_player: return # Need player for radius check

        info = self.building_info.get(self.selected_building_type)
        preview_instance = self.preview_instances.get(self.selected_building_type)
        if info is None or preview_instance is None: return

        mx, my = pygame.mouse.get_pos()
        # Don't draw preview if mouse is over the UI area
        if my >= self.map_height_px: return

        gx, gy = world_to_grid(mx, my)
        # Ensure preview stays within grid bounds visually
        if not (0 <= gx < self.grid_width and 0 <= gy < self.grid_height): return

        world_x, world_y = grid_to_world(gx, gy)

        # --- Check Placement Validity ---
        cost = info['cost']
        can_afford = all(self.resources.get(res, 0) >= amount for res, amount in cost.items())

        existing = self.get_structure_at(gx, gy)
        BuildingClass = info['class']
        is_drill_on_patch = (BuildingClass == Drill and isinstance(existing, ResourcePatch))
        is_empty = (existing is None)
        valid_tile = (is_drill_on_patch or (is_empty and BuildingClass != Drill))

        target_center_x, target_center_y = grid_to_world_center(gx, gy)
        radius_sq = PLAYER_BUILD_RADIUS * PLAYER_BUILD_RADIUS
        in_radius = distance_sq(local_player.world_x, local_player.world_y, target_center_x, target_center_y) <= radius_sq

        is_placement_valid = can_afford and valid_tile and in_radius
        # --- End Validity Check ---


        # --- Determine Tint and Alpha ---
        tint_color = None
        preview_alpha = 180 # Semi-transparent default

        if not is_placement_valid:
            preview_alpha = 150 # More transparent if invalid
            if not in_radius: tint_color = COLOR_INVALID_RADIUS # Blue tint for out of range
            elif not valid_tile: tint_color = (*COLOR_RED[:3], 120) # Red tint for blocked tile
            else: tint_color = (*COLOR_YELLOW[:3], 120) # Yellow tint for cannot afford
        # --- End Tint/Alpha ---

        # --- Draw Preview ---
        try:
            # Create a surface for the preview instance
            preview_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            # Set world position to 0,0 for drawing on the surface
            preview_instance.world_x, preview_instance.world_y = 0, 0
            preview_instance.center_x, preview_instance.center_y = TILE_SIZE / 2.0, TILE_SIZE / 2.0
            # Update orientation if it's a conveyor
            if isinstance(preview_instance, Conveyor):
                 preview_instance.orientation = self.selected_orientation
            # Draw the building onto the temporary surface
            preview_instance.draw(preview_surf)
            preview_surf.set_alpha(preview_alpha)

            # Apply tint if needed
            if tint_color:
                tint_surface = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                tint_surface.fill(tint_color)
                # Blend the tint color multiplicatively onto the preview surface
                preview_surf.blit(tint_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

            # Blit the final preview surface onto the main screen
            self.screen.blit(preview_surf, (world_x, world_y))
        except Exception as e:
             print(f"ERROR drawing build preview for {info['name']}: {e}")
        # --- End Draw Preview ---

    def draw_ui(self):
        """Draws the main user interface at the bottom."""
        current_w, current_h = self.screen.get_width(), self.screen.get_height()
        ui_rect = pygame.Rect(0, self.map_height_px, current_w, UI_HEIGHT) # Position below game area

        # Background and Top Border
        pygame.draw.rect(self.screen, COLOR_UI_BG, ui_rect)
        pygame.draw.line(self.screen, COLOR_GRAY, (0, ui_rect.y), (current_w, ui_rect.y), 1)

        # Check if fonts are loaded
        if not all([font_tiny, font_small, font_medium]):
            print("WARN: UI Fonts not loaded, skipping UI draw.")
            return

        # --- UI Elements ---
        res_fs, core_fs, wave_fs = 24, 24, 24
        build_h_fs, build_i_fs, tt_fs = 16, 16, 14
        padding = 15
        y_row1 = ui_rect.y + 8

        # Resources
        draw_text(self.screen, f"Cu: {self.resources.get(RES_COPPER, 0)}", res_fs, padding, y_row1, COLOR_COPPER)
        draw_text(self.screen, f"Coal: {self.resources.get(RES_COAL, 0)}", res_fs, padding + 120, y_row1, COLOR_COAL)

        # Core HP
        core_hp_text, core_hp_color = "Core: N/A", COLOR_GRAY
        if self.core:
             hp = int(self.core.hp); max_hp = self.core.max_hp
             if hp <= 0: core_hp_text, core_hp_color = "Core: DESTROYED", COLOR_RED
             else:
                 core_hp_text = f"Core: {hp}/{max_hp}"
                 core_hp_color = COLOR_GREEN if hp > max_hp * 0.3 else COLOR_YELLOW
        draw_text(self.screen, core_hp_text, core_fs, padding + 260, y_row1, core_hp_color)

        # Wave Status
        wave_text, wave_color = "", COLOR_YELLOW
        if self.game_won: wave_text, wave_color = "YOU WIN!", COLOR_GREEN
        elif self.game_over: wave_text, wave_color = "GAME OVER", COLOR_RED
        elif self.in_wave:
             num_enemies = len(self.enemies) # Number of active enemies
             wave_text = f"Wave: {self.wave_number}/{self.max_waves} ({num_enemies} Enemies)"
             wave_color = COLOR_RED
        elif self.wave_number >= self.max_waves:
             wave_text = "Clear remaining enemies!" # After last wave starts cooldown
        else: # Cooldown between waves
             wave_text = f"Next Wave ({self.wave_number + 1}) in: {int(self.wave_timer)}s"
        # Position wave text further right
        draw_text(self.screen, wave_text, wave_fs, padding + 480, y_row1, wave_color, align="topleft")


        # Network Mode / Player Count (Top Right of UI)
        mode_text = f"Mode: {self.network_mode.upper()}"
        if self.network_mode == "host":
             mode_text += f" ({len(self.players)}/{MAX_PLAYERS})"
        elif self.network_mode == "client":
             status = "Connected" if self.client and self.client.connected else "Connecting..."
             mode_text += f" ({status})"
        draw_text(self.screen, mode_text, 16, current_w - padding, y_row1 + 25, COLOR_NETWORK_STATUS, align="topright")

        # Basic Controls Hint (Top Right of UI)
        controls_text = "[WASD]Move [RMB]Del [U]Upgr [ESC]Menu"
        draw_text(self.screen, controls_text, tt_fs, current_w - padding, y_row1 + 5, COLOR_GRAY, align="topright")


        # --- Build Menu ---
        y_build_start = ui_rect.y + 45 # Start lower down
        sections = {'Production': [], 'Logistics': [], 'Defense': [], 'Power': [], 'Support': []}
        # Group buildings by section
        for bt, info in self.building_info.items():
            sections.setdefault(info.get('section', 'Other'), []).append(bt)

        current_build_x = padding
        section_spacing = 15
        item_spacing = 10
        item_y_offset = 20 # Space below section header

        # Inverse map for getting key number
        key_num_map = {v: k for k, v in self.key_to_building_type.items()}

        for section_name, building_types in sections.items():
            if not building_types: continue # Skip empty sections

            header_y = y_build_start
            draw_text(self.screen, section_name, build_h_fs, current_build_x, header_y, COLOR_UI_HEADER)
            header_width_approx = len(section_name) * 8 # Estimate width

            item_y = header_y + item_y_offset
            section_start_x = current_build_x

            for bt in building_types:
                info = self.building_info[bt]
                # Format cost string (e.g., "15C+5Co")
                cost_str = "+".join([f"{a}{'C' if r == RES_COPPER else 'Co'}" for r, a in info['cost'].items()])
                # Get key number (1-8)
                key_code = key_num_map.get(bt, 0)
                key_display = str(key_code - pygame.K_0) if key_code >= pygame.K_1 else '?'

                button_text = f"[{key_display}] {info['name']} ({cost_str})"

                is_selected = (self.selected_building_type == bt)
                can_afford = all(self.resources.get(res, 0) >= amount for res, amount in info['cost'].items())

                # Determine text color based on selection and affordability
                text_color = COLOR_GREEN if is_selected else COLOR_UI_TEXT
                if not can_afford:
                    # Dim color if cannot afford
                    text_color = tuple(c // 2 for c in text_color)

                # Render and draw text, get width for positioning next item
                text_surface = font_small.render(button_text, True, text_color)
                self.screen.blit(text_surface, (current_build_x, item_y))
                current_build_x += text_surface.get_width() + item_spacing

            # Move to next section position, ensure enough space
            current_build_x = max(current_build_x, section_start_x + header_width_approx) + section_spacing

        # Draw "[0] None" button
        none_color = COLOR_GREEN if self.selected_building_type == BUILDING_NONE else COLOR_UI_TEXT
        draw_text(self.screen, "[0] None", build_i_fs, current_build_x, y_build_start + item_y_offset, none_color)
        # --- End Build Menu ---


        # --- Power Network Tooltip ---
        # Check if hovering a node AND network stats have been calculated
        if self.hovered_power_node_id and self.network_stats:
            hovered_node = self.get_structure_by_id(self.hovered_power_node_id)
            # Double check the hovered node still exists and is valid (based on current state)
            if hovered_node and hovered_node.is_power_node and getattr(hovered_node, 'is_on_grid', False):
                stats = self.network_stats
                mouse_x, mouse_y = pygame.mouse.get_pos()
                box_x, box_y = mouse_x + 15, mouse_y + 10
                line_height = 18
                num_lines = 4 # Reduced number of lines
                box_width = 180 # Adjusted width
                box_height = num_lines * line_height + 10

                # Adjust position to stay fully on screen
                if box_x + box_width > current_w: box_x = mouse_x - box_width - 15 # Flip left
                if box_y + box_height > self.map_height_px: box_y = mouse_y - box_height - 10 # Flip above cursor if near UI
                box_y = max(5, box_y) # Prevent going off top

                # Draw tooltip box
                tooltip_bg_color = (*COLOR_UI_BG[:3], 230) # Semi-transparent background
                pygame.draw.rect(self.screen, tooltip_bg_color, (box_x, box_y, box_width, box_height))
                pygame.draw.rect(self.screen, COLOR_GRAY, (box_x, box_y, box_width, box_height), 1) # Border

                # Draw tooltip text
                y_offset = box_y + 5
                net_power = stats['generation'] - stats['consumption']
                net_power_color = COLOR_GREEN if net_power >= -1e-6 else COLOR_RED

                draw_text(self.screen, f"Network ({stats['nodes']} nodes):", tt_fs, box_x + 5, y_offset, COLOR_WHITE); y_offset += line_height
                draw_text(self.screen, f"+ {stats['generation']:.1f}/s", tt_fs, box_x + 5, y_offset, COLOR_GREEN); y_offset += line_height
                draw_text(self.screen, f"- {stats['consumption']:.1f}/s", tt_fs, box_x + 5, y_offset, COLOR_RED); y_offset += line_height
                storage_text = f"Bat: {stats['charge']:.0f} / {stats['capacity']:.0f}"
                draw_text(self.screen, storage_text, tt_fs, box_x + 5, y_offset, COLOR_BATTERY_CHARGE); y_offset += line_height
                # draw_text(self.screen, f"Net: {net_power:+.1f}/s", tt_fs, box_x + 5, y_offset, net_power_color); y_offset += line_height # Optionally show net

    def draw_overlay_screen(self, title, title_color, subtitle, subtitle_color, waves_survived=None):
        """Draws a semi-transparent overlay for game over/win screens."""
        overlay_color = (*COLOR_DARK_GRAY[:3], 220) # Dark semi-transparent
        current_w, current_h = self.screen.get_width(), self.screen.get_height()

        # Create a surface for the overlay
        overlay_surface = pygame.Surface((current_w, current_h), pygame.SRCALPHA)
        overlay_surface.fill(overlay_color)
        # Blit the overlay surface onto the main screen
        self.screen.blit(overlay_surface, (0, 0))

        # Draw text on top of the overlay
        if font_large and font_medium and font_small:
            center_x, center_y = current_w // 2, current_h // 2
            # Main Title (Game Over / You Win)
            draw_text(self.screen, title, 72, center_x, center_y - 60, title_color, align="center")
            # Subtitle (Reason / Wave count)
            draw_text(self.screen, subtitle, 24, center_x, center_y + 10, subtitle_color, align="center")
            # Optional wave survival count
            if waves_survived is not None:
                wave_report = f"Survived {max(0, waves_survived)} waves."
                draw_text(self.screen, wave_report, 18, center_x, center_y + 45, COLOR_GRAY, align="center")
            # Prompt to return to menu
            draw_text(self.screen, "Press ESC to return to Menu", 18, center_x, center_y + 80, COLOR_GRAY, align="center")

    def draw_music_controls(self):
        """Draws the music control buttons and volume slider in the top-right corner."""
        # Don't draw if no music files were found
        if not self.game_music_files: return

        mouse_pos = pygame.mouse.get_pos()
        btn_color = (*COLOR_UI_BG[:3], 180) # Semi-transparent background
        hover_color = (*COLOR_MENU_BUTTON_HOVER[:3], 220)
        border_color = COLOR_GRAY
        text_color = COLOR_WHITE

        # --- Draw Slider ---
        if self.volume_slider_track_rect and self.volume_slider_handle_rect:
            # Draw Track
            pygame.draw.rect(self.screen, COLOR_SLIDER_TRACK, self.volume_slider_track_rect, border_radius=4)
            # Draw Handle
            handle_color = COLOR_SLIDER_HANDLE_DRAG if self.dragging_volume else COLOR_SLIDER_HANDLE
            pygame.draw.rect(self.screen, handle_color, self.volume_slider_handle_rect, border_radius=3)
            pygame.draw.rect(self.screen, border_color, self.volume_slider_handle_rect, 1, border_radius=3) # Border

            # Optional: Draw volume percentage text next to slider
            if font_tiny:
                 vol_percent = int(self.current_volume * 100)
                 text_margin = 5
                 text_x = self.volume_slider_track_rect.right + text_margin
                 text_y = self.volume_slider_track_rect.centery
                 draw_text(self.screen, f"{vol_percent}%", 14, text_x, text_y, COLOR_GRAY, align="midleft")
        # ------------------

        # --- Draw Buttons ---
        buttons_to_draw = [
            (self.prev_button_rect, "<<"),
            # Dynamic label for play/pause button
            (self.play_pause_button_rect, "||" if self.music_playing else ">"),
            (self.next_button_rect, ">>")
        ]

        for rect, text in buttons_to_draw:
            if rect: # Ensure rect is not None
                current_color = hover_color if rect.collidepoint(mouse_pos) else btn_color
                pygame.draw.rect(self.screen, current_color, rect)
                pygame.draw.rect(self.screen, border_color, rect, 1) # Border
                draw_text(self.screen, text, 20, rect.centerx, rect.centery, text_color, align="center")
        # -------------------

        # --- Draw Current Song Name (Optional) ---
        # Position below the buttons
        if font_tiny and self.current_song_index != -1 and self.prev_button_rect:
             try:
                 song_name = os.path.basename(self.game_music_files[self.current_song_index])
                 name_x = self.prev_button_rect.left # Align with first button
                 name_y = self.prev_button_rect.bottom + 5 # Position below buttons
                 draw_text(self.screen, song_name, 14, name_x, name_y, COLOR_GRAY, align="topleft")
             except IndexError:
                 pass # Ignore if index is temporarily out of bounds
        # --------------------

    def draw(self):
        """Draws the entire game screen for one frame."""
        # 1. Background / Grid
        self.screen.fill(COLOR_DARK_GRAY)
        self.draw_grid()

        # 2. Base Terrain (Resource Patches)
        self.draw_base_terrain()

        # 3. Structures (Draws buildings from self.structures)
        # Use list() to create a copy in case structures are modified during draw (less likely but safer)
        for struct in list(self.structures.values()):
            struct.draw(self.screen)

        # 4. Power Grid Lines (Draw on top of structures)
        self.draw_power_grid_connections()

        # 5. Players
        for player in self.players.values():
            player.draw(self.screen)

        # 6. Enemies
        for enemy in self.enemies.values():
            enemy.draw(self.screen)

        # 7. Projectiles
        for proj in self.projectiles.values():
            proj.draw(self.screen)

        # 8. Build Preview (Ghost image under cursor)
        self.draw_build_preview()

        # 9. Main UI (Bottom panel)
        self.draw_ui()

        # 10. Music Controls (Top right, drawn over UI/Game)
        self.draw_music_controls()

        # 11. Game Over / Win Overlay (Draw last if active)
        waves_survived_count = self.wave_number - 1 if (self.in_wave or self.game_over) else self.wave_number
        if self.game_over:
            self.draw_overlay_screen("GAME OVER", COLOR_RED, "The core has been destroyed!", COLOR_WHITE, waves_survived_count)
        elif self.game_won:
            self.draw_overlay_screen("YOU WIN!", COLOR_GREEN, f"Survived all {self.max_waves} waves!", COLOR_WHITE)
        # --- End Drawing ---

    # --- State Synchronization ---
    def get_full_snapshot(self):
        """Gets the complete game state, suitable for saving or networking."""
        if self.network_mode == "client": return None # Clients don't generate snapshots

        # Convert terrain keys to strings for JSON compatibility
        string_key_terrain = {}
        for (gx, gy), r in self.base_terrain.items():
            string_key_terrain[f"{gx},{gy}"] = r

        snapshot = {
            'resources': self.resources.copy(),
            'wave_number': self.wave_number,
            'wave_timer': self.wave_timer,
            'in_wave': self.in_wave,
            'game_over': self.game_over,
            'game_won': self.game_won,
            'players': {pid: p.get_state() for pid, p in self.players.items()},
            # Ensure ResourcePatch objects are NOT included in structures snapshot
            'structures': {sid: s.get_state() for sid, s in self.structures.items() if s.building_type != BUILDING_RESOURCE},
            'enemies': {eid: e.get_state() for eid, e in self.enemies.items()},
            'projectiles': {pid: p.get_state() for pid, p in self.projectiles.items()},
            'base_terrain': string_key_terrain,
            'core_hp': self.core.hp if self.core else 0,
            'core_max_hp': self.core.max_hp if self.core else CORE_HP,
            # --- ADDED FOR SAVING ---
            'next_enemy_id': self.next_enemy_id,
            'next_projectile_id': self.next_projectile_id,
            'game_mode_for_save': self.network_mode # Store mode ('sp' or 'host')
            # ------------------------
        }
        return snapshot

    def apply_full_snapshot(self, snapshot):
        """Applies a complete game state snapshot (from network or save file)."""
        # Avoid applying state on server/SP mode from external source typically
        # But allow for save game loading which calls this internally
        # if self.network_mode == "sp" or self.network_mode == "host": return

        print("DEBUG: Applying full snapshot...") # Add more detailed logging if needed

        # --- Apply Basic State ---
        self.resources = snapshot.get('resources', self.resources)
        self.wave_number = snapshot.get('wave_number', self.wave_number)
        self.wave_timer = snapshot.get('wave_timer', self.wave_timer)
        self.in_wave = snapshot.get('in_wave', self.in_wave)
        self.game_over = snapshot.get('game_over', self.game_over)
        self.game_won = snapshot.get('game_won', self.game_won)
        # Apply next IDs if loading from save
        self.next_enemy_id = snapshot.get('next_enemy_id', self.next_enemy_id)
        self.next_projectile_id = snapshot.get('next_projectile_id', self.next_projectile_id)
        # --- End Basic State ---

        # --- Apply Base Terrain (Only if not already populated) ---
        # Check if base_terrain dict is empty OR if loading from a save file explicitly
        is_loading_from_save = 'game_mode_for_save' in snapshot # Check if it's a save file snapshot
        if not self.base_terrain or is_loading_from_save:
            received_terrain_str = snapshot.get('base_terrain')
            if received_terrain_str:
                new_base_terrain = {}
                new_grid = [[None for _ in range(self.grid_height)] for _ in range(self.grid_width)] # Start with fresh grid
                try:
                    for str_key, res_type in received_terrain_str.items():
                        parts = str_key.split(',')
                        gx, gy = int(parts[0]), int(parts[1])
                        new_base_terrain[(gx, gy)] = res_type
                        # Place visual patch on the new grid
                        if 0 <= gx < self.grid_width and 0 <= gy < self.grid_height:
                            new_grid[gx][gy] = ResourcePatch(gx, gy, res_type)
                    self.base_terrain = new_base_terrain
                    self.grid = new_grid # Replace old grid
                    print(f"Applied base terrain ({len(self.base_terrain)} patches).")
                except Exception as e:
                    print(f"ERROR parsing base_terrain from snapshot: {e}")
                    # Keep existing terrain/grid if parsing failed severely? Or clear them?
                    self.base_terrain = {}
                    self.grid = [[None for _ in range(self.grid_height)] for _ in range(self.grid_width)]
            else:
                 # If no terrain in snapshot, ensure local state is clear
                 self.base_terrain = {}
                 self.grid = [[None for _ in range(self.grid_height)] for _ in range(self.grid_width)]
        # --- End Base Terrain ---


        # --- Sync Players ---
        received_players = snapshot.get('players', {})
        current_player_ids = set(self.players.keys())
        received_player_ids = set()
        new_player_dict = {} # Build the new dictionary incrementally

        for pid_str, player_data in received_players.items():
             try:
                 pid = int(pid_str)
                 received_player_ids.add(pid)
                 if pid in self.players:
                     # Update existing player
                     self.players[pid].apply_state(player_data)
                     new_player_dict[pid] = self.players[pid] # Keep updated player
                 else:
                     # Create new player
                     # Use data from snapshot, provide defaults if keys missing
                     start_x = player_data.get('x', self.map_width_px / 2)
                     start_y = player_data.get('y', self.map_height_px / 2)
                     name = player_data.get('name', f"Player{pid}")
                     color_idx = player_data.get('color_idx', pid % len(COLOR_PLAYER_OPTIONS))
                     new_player = Player(start_x, start_y, pid, name=name, color_index=color_idx)
                     new_player_dict[pid] = new_player
                     print(f"Created player {pid} ('{new_player.name}') from snapshot.")
             except (ValueError, TypeError) as e:
                 print(f"Error processing player data for key '{pid_str}': {e}")
                 continue # Skip this player

        # Identify players to remove (present locally but not in snapshot)
        ids_to_remove = current_player_ids - received_player_ids
        if ids_to_remove:
             print(f"Players removed (not in snapshot): {ids_to_remove}")

        self.players = new_player_dict # Replace player dictionary
        # --- End Sync Players ---


        # --- Sync Structures ---
        received_structures = snapshot.get('structures', {})
        current_structure_ids = set(self.structures.keys())
        received_structure_ids = set(received_structures.keys())
        new_structure_dict = {} # Build the new dictionary

        core_data_from_snapshot = None
        core_id_from_snapshot = None

        for sid, struct_data in received_structures.items():
            building_type = struct_data.get('type')
            if building_type == BUILDING_CORE:
                # Handle core separately after main loop
                core_data_from_snapshot = struct_data
                core_id_from_snapshot = sid
                continue # Skip adding core to new_structure_dict here

            if sid in self.structures:
                # Update existing structure
                try:
                    self.structures[sid].apply_state(struct_data)
                    new_structure_dict[sid] = self.structures[sid] # Keep updated structure
                    # Update grid reference as well
                    gx, gy = self.structures[sid].grid_x, self.structures[sid].grid_y
                    if 0 <= gx < self.grid_width and 0 <= gy < self.grid_height:
                         self.grid[gx][gy] = self.structures[sid]
                except Exception as e:
                     print(f"Error applying state to structure {sid}: {e}")
            else:
                # Create new structure
                gx, gy = struct_data.get('gx'), struct_data.get('gy')
                info = self.building_info.get(building_type)
                if info and gx is not None and gy is not None:
                    BuildingClass = info['class']
                    orientation = struct_data.get('orientation', EAST) if building_type == BUILDING_CONVEYOR else None
                    try:
                        new_struct = BuildingClass(gx, gy, orientation) if orientation is not None else BuildingClass(gx, gy)
                        new_struct.network_id = sid # Assign the ID from the snapshot
                        new_struct.apply_state(struct_data) # Apply the rest of the state
                        new_structure_dict[sid] = new_struct
                        # Place on grid, potentially overwriting ResourcePatch visual
                        if 0 <= gx < self.grid_width and 0 <= gy < self.grid_height:
                            self.grid[gx][gy] = new_struct
                        # print(f"DEBUG: Created structure {sid} ({BuildingClass.__name__}) from snapshot.")
                    except Exception as e:
                        print(f"ERROR creating structure {sid} (type {building_type}) from snapshot: {e}")
                else:
                    print(f"WARN: Invalid data or missing info for new structure {sid} (type {building_type}). Skipping.")

        # --- Core Handling ---
        if core_data_from_snapshot:
            if self.core and self.core.network_id == core_id_from_snapshot:
                 # Update existing core
                 self.core.apply_state(core_data_from_snapshot)
                 new_structure_dict[core_id_from_snapshot] = self.core # Add to new dict
                 gx, gy = self.core.grid_x, self.core.grid_y
                 if 0 <= gx < self.grid_width and 0 <= gy < self.grid_height: self.grid[gx][gy] = self.core # Ensure grid ref
                 # print("DEBUG: Updated existing core from snapshot.")
            else:
                 # Create new core if missing or ID doesn't match
                 gx, gy = core_data_from_snapshot.get('gx'), core_data_from_snapshot.get('gy')
                 if gx is not None and gy is not None:
                      if self.core: print("WARN: Replacing existing core object.") # Should ideally not happen if IDs match
                      self.core = Core(gx, gy)
                      self.core.network_id = core_id_from_snapshot
                      self.core.apply_state(core_data_from_snapshot)
                      new_structure_dict[core_id_from_snapshot] = self.core # Add to new dict
                      if 0 <= gx < self.grid_width and 0 <= gy < self.grid_height: self.grid[gx][gy] = self.core # Place on grid
                      print("Created Core from snapshot.")
                 else: print("ERROR: Core data in snapshot missing coordinates.")
        elif self.core:
             # Core exists locally but not in snapshot - remove local core
             print("WARN: Core missing from snapshot, removing local core.")
             gx, gy = self.core.grid_x, self.core.grid_y
             if 0 <= gx < self.grid_width and 0 <= gy < self.grid_height and self.grid[gx][gy] == self.core:
                  base_type = self.base_terrain.get((gx, gy))
                  self.grid[gx][gy] = ResourcePatch(gx, gy, base_type) if base_type else None
             self.core = None

        # Identify structures to remove
        struct_ids_to_remove = current_structure_ids - received_structure_ids
        # Make sure not to remove the current core if it wasn't in the received dict but still exists
        if self.core and self.core.network_id in struct_ids_to_remove:
             struct_ids_to_remove.remove(self.core.network_id)

        if struct_ids_to_remove:
            # print(f"DEBUG: Structures removed (not in snapshot): {struct_ids_to_remove}")
            for sid in struct_ids_to_remove:
                 # Ensure grid is cleared where structure was removed
                 if sid in self.structures: # Get coords from old dict before replacing
                      old_struct = self.structures[sid]
                      gx, gy = old_struct.grid_x, old_struct.grid_y
                      if 0 <= gx < self.grid_width and 0 <= gy < self.grid_height and self.grid[gx][gy] == old_struct:
                           base_type = self.base_terrain.get((gx, gy))
                           self.grid[gx][gy] = ResourcePatch(gx, gy, base_type) if base_type else None

        self.structures = new_structure_dict # Replace structure dictionary

        # Ensure core HP matches snapshot explicitly (apply_state might be overridden)
        if self.core:
             self.core.hp = snapshot.get('core_hp', self.core.hp)
             self.core.max_hp = snapshot.get('core_max_hp', self.core.max_hp)
        # --- End Sync Structures ---


        # --- Sync Enemies ---
        received_enemies = snapshot.get('enemies', {})
        current_enemy_ids = set(self.enemies.keys())
        received_enemy_ids = set(received_enemies.keys())
        new_enemy_dict = {}

        for eid, enemy_data in received_enemies.items():
            if eid in self.enemies:
                 # Update existing enemy
                 try:
                      self.enemies[eid].apply_state(enemy_data)
                      new_enemy_dict[eid] = self.enemies[eid]
                 except Exception as e: print(f"Error applying state to enemy {eid}: {e}")
            else:
                 # Create new enemy
                 try:
                      # Provide defaults for constructor if data is minimal
                      pos_x = enemy_data.get('x', 0)
                      pos_y = enemy_data.get('y', 0)
                      hp = enemy_data.get('hp', ENEMY_START_HP)
                      # Target coords don't strictly matter for client/load, use placeholder
                      target_coords = (self.map_width_px/2, self.map_height_px/2)
                      new_enemy = Enemy(pos_x, pos_y, target_coords, hp, ENEMY_SPEED, ENEMY_DAMAGE, ENEMY_ATTACK_COOLDOWN, eid)
                      new_enemy.apply_state(enemy_data) # Apply full state after creation
                      new_enemy_dict[eid] = new_enemy
                 except Exception as e: print(f"ERROR creating enemy {eid} from snapshot: {e}")

        self.enemies = new_enemy_dict # Replace enemy dictionary
        # --- End Sync Enemies ---


        # --- Sync Projectiles ---
        received_projectiles = snapshot.get('projectiles', {})
        current_projectile_ids = set(self.projectiles.keys())
        received_projectile_ids = set(received_projectiles.keys())
        new_projectile_dict = {}

        for pid, proj_data in received_projectiles.items():
             if pid in self.projectiles:
                  # Update existing projectile
                  try:
                       self.projectiles[pid].apply_state(proj_data)
                       new_projectile_dict[pid] = self.projectiles[pid]
                  except Exception as e: print(f"Error applying state to projectile {pid}: {e}")
             else:
                  # Create new projectile
                  px, py = proj_data.get('x'), proj_data.get('y')
                  vx, vy = proj_data.get('vx'), proj_data.get('vy')
                  if px is not None and py is not None and vx is not None and vy is not None:
                       try:
                            # Target obj is None when creating from state, provide velocity directly
                            new_proj = Projectile(px, py, None, PROJECTILE_SPEED, 0, pid, vx=vx, vy=vy)
                            # No apply_state needed if constructor takes all values, but call if exists for consistency
                            if hasattr(new_proj, 'apply_state'): new_proj.apply_state(proj_data)
                            new_projectile_dict[pid] = new_proj
                       except Exception as e: print(f"ERROR creating projectile {pid} from snapshot: {e}")
                  else: print(f"WARN: Invalid projectile data in snapshot for {pid}. Skipping.")

        self.projectiles = new_projectile_dict # Replace projectile dictionary
        # --- End Sync Projectiles ---

        print("DEBUG: Finished applying full snapshot.")


    def apply_incremental_update(self, update_data):
        """Applies smaller, targeted updates received over the network (Client only)."""
        if self.network_mode == "sp" or self.network_mode == "host": return # Only clients process these

        update_type = update_data.get('type')
        data = update_data.get('data')
        net_id = update_data.get('net_id') # For single item removal/update
        ids = update_data.get('ids')       # For batch removal

        try: # Wrap processing in a try-except block for safety
            if update_type == 'player_join':
                pid = data.get('id')
                if pid is not None and pid not in self.players:
                    # Create new player based on join data
                    new_p = Player(data['x'], data['y'], pid, data['name'], data['color_idx'])
                    self.players[pid] = new_p
                    print(f"CLIENT: Player {pid} ('{new_p.name}') joined.")
                elif pid == self.local_player_id and not self.players.get(pid):
                    # Recreate local player if missing (e.g., after some error)
                    self.players[pid] = Player(data['x'], data['y'], pid, data['name'], data['color_idx'])

            elif update_type == 'player_leave':
                pid = update_data.get('player_id')
                if pid is not None and pid in self.players:
                    print(f"CLIENT: Player {pid} left.")
                    del self.players[pid]

            elif update_type == 'assign_id': # Server assigns client its ID
                assigned_id = data.get('id')
                if assigned_id is not None:
                     self.local_player_id = assigned_id
                     print(f"CLIENT: Assigned Player ID: {self.local_player_id}")
                     # Ensure player object exists after assignment
                     if self.local_player_id not in self.players:
                          # Need initial pos/name/color - maybe request full state again?
                          # Or server should send player data with assign_id
                          print(f"WARN: Player object for assigned ID {self.local_player_id} not found.")


            elif update_type == 'game_status': # Game over/win
                status = update_data.get('status')
                self.game_over = (status == 'over')
                self.game_won = (status == 'won')
                if self.game_over: print("CLIENT: Received Game Over status.")
                if self.game_won: print("CLIENT: Received Game Won status.")

            elif update_type == 'resource_update': # Full resource dict update
                if isinstance(data, dict): self.resources = data

            elif update_type == 'wave_update': # Wave number, timer, status
                 if isinstance(data, dict):
                      self.wave_number = data.get('number', self.wave_number)
                      self.wave_timer = data.get('timer', self.wave_timer)
                      self.in_wave = data.get('in_wave', self.in_wave)

            elif update_type == 'structure_add': # Add a single new structure
                 sid = data.get('net_id')
                 b_type = data.get('type')
                 gx, gy = data.get('gx'), data.get('gy')
                 info = self.building_info.get(b_type)
                 if sid and info and gx is not None and gy is not None and sid not in self.structures:
                     BuildingClass = info['class']
                     orient = data.get('orientation', EAST) if b_type == BUILDING_CONVEYOR else None
                     new_s = BuildingClass(gx, gy, orient) if orient is not None else BuildingClass(gx, gy)
                     new_s.network_id = sid
                     new_s.apply_state(data) # Apply full state from message
                     self.structures[sid] = new_s
                     # Place on grid
                     if 0 <= gx < self.grid_width and 0 <= gy < self.grid_height: self.grid[gx][gy] = new_s
                     if b_type == BUILDING_CORE: self.core = new_s # Assign core ref

            elif update_type == 'structure_update': # Update state of existing structure
                 sid = data.get('net_id')
                 if sid in self.structures:
                     self.structures[sid].apply_state(data)
                     # Also update core ref if it's the core being updated
                     if self.core and sid == self.core.network_id: self.core.apply_state(data)

            elif update_type == 'structure_remove': # Remove single structure by ID
                 if net_id and net_id in self.structures:
                     s = self.structures[net_id]
                     gx, gy = s.grid_x, s.grid_y
                     del self.structures[net_id]
                     # Clear grid cell or restore resource patch visual
                     if 0 <= gx < self.grid_width and 0 <= gy < self.grid_height and self.grid[gx][gy] == s:
                          base_type = self.base_terrain.get((gx, gy))
                          self.grid[gx][gy] = ResourcePatch(gx, gy, base_type) if base_type else None
                     if self.core and net_id == self.core.network_id: self.core = None # Clear core ref

            elif update_type == 'structures_remove': # Remove multiple structures by ID list
                 if ids and isinstance(ids, list):
                     for sid in ids:
                         if sid in self.structures:
                             s = self.structures[sid]; gx, gy = s.grid_x, s.grid_y
                             del self.structures[sid]
                             if 0 <= gx < self.grid_width and 0 <= gy < self.grid_height and self.grid[gx][gy] == s:
                                  base_type = self.base_terrain.get((gx, gy))
                                  self.grid[gx][gy] = ResourcePatch(gx, gy, base_type) if base_type else None
                             if self.core and sid == self.core.network_id: self.core = None

            elif update_type == 'enemy_add': # Add single enemy
                eid = data.get('net_id')
                if eid and eid not in self.enemies:
                    target_coords = (self.map_width_px/2, self.map_height_px/2) # Placeholder target
                    new_e = Enemy(data['x'], data['y'], target_coords, data['hp'], ENEMY_SPEED, ENEMY_DAMAGE, ENEMY_ATTACK_COOLDOWN, eid)
                    new_e.apply_state(data)
                    self.enemies[eid] = new_e

            elif update_type == 'enemies_remove': # Remove multiple enemies by ID list
                if ids and isinstance(ids, list):
                    for eid in ids:
                        if eid in self.enemies: del self.enemies[eid]

            elif update_type == 'projectile_add': # Add single projectile
                 pid = data.get('net_id')
                 if pid and pid not in self.projectiles:
                     px, py, vx, vy = data.get('x'), data.get('y'), data.get('vx'), data.get('vy')
                     if px is not None and py is not None and vx is not None and vy is not None:
                         new_p = Projectile(px, py, None, PROJECTILE_SPEED, 0, pid, vx=vx, vy=vy)
                         self.projectiles[pid] = new_p

            elif update_type == 'projectiles_remove': # Remove multiple projectiles by ID list
                 if ids and isinstance(ids, list):
                     for pid in ids:
                         if pid in self.projectiles: del self.projectiles[pid]

            # Add more incremental update types as needed (e.g., player position, structure HP only)

        except Exception as e:
             print(f"ERROR applying incremental update (type: {update_type}): {e}")
             # Consider requesting full state sync from server on error?


    # --- Music Control Methods ---
    def _setup_music_controls_ui(self):
        """Calculates the positions for music control buttons and volume slider."""
        try:
            screen_w = self.screen.get_width()
            btn_size = 28
            margin = 10
            slider_height = 8
            slider_width = 80
            handle_height = 16
            handle_width = 10
            slider_bottom_margin = 8

            # Slider Positioning
            slider_y = 10
            slider_x = screen_w - margin - slider_width

            self.volume_slider_track_rect = pygame.Rect(slider_x, slider_y, slider_width, slider_height)
            handle_center_x = slider_x + int(self.current_volume * slider_width)
            handle_y = slider_y + (slider_height / 2) - (handle_height / 2)
            self.volume_slider_handle_rect = pygame.Rect(0, handle_y, handle_width, handle_height)
            self.volume_slider_handle_rect.centerx = handle_center_x

            # Button Positioning (relative to slider)
            buttons_y = slider_y + slider_height + slider_bottom_margin
            buttons_x_start = screen_w - margin - (btn_size * 3 + margin * 2)

            self.prev_button_rect = pygame.Rect(buttons_x_start, buttons_y, btn_size, btn_size)
            self.play_pause_button_rect = pygame.Rect(buttons_x_start + btn_size + margin, buttons_y, btn_size, btn_size)
            self.next_button_rect = pygame.Rect(buttons_x_start + (btn_size + margin) * 2, buttons_y, btn_size, btn_size)
        except Exception as e:
             print(f"Error setting up music controls UI: {e}")
             self.volume_slider_track_rect = None
             self.volume_slider_handle_rect = None
             self.prev_button_rect = None
             self.play_pause_button_rect = None
             self.next_button_rect = None


    def load_and_play_song(self, index):
        """Loads and plays a song by index from the game music list."""
        if not self.game_music_files or not (0 <= index < len(self.game_music_files)):
            print("WARN: Invalid song index or no music files.")
            self.current_song_index = -1
            self.music_playing = False
            try: pygame.mixer.music.stop()
            except pygame.error: pass
            return

        self.current_song_index = index
        song_path = self.game_music_files[self.current_song_index]
        try:
            print(f"MUSIC: Loading '{os.path.basename(song_path)}'")
            pygame.mixer.music.load(song_path)
            pygame.mixer.music.set_volume(self.current_volume) # Ensure volume is set before playing
            pygame.mixer.music.play(0) # Play once
            pygame.mixer.music.set_endevent(MUSIC_END_EVENT)
            self.music_playing = True
        except pygame.error as e:
            print(f"ERROR: Could not load/play music '{song_path}': {e}")
            self.music_playing = False
            self.current_song_index = -1

    def play_next_song(self):
        """Plays the next song in the list, wrapping around."""
        if not self.game_music_files: return
        next_index = 0 if self.current_song_index == -1 else (self.current_song_index + 1) % len(self.game_music_files)
        self.load_and_play_song(next_index)

    def play_prev_song(self):
        """Plays the previous song in the list, wrapping around."""
        if not self.game_music_files: return
        prev_index = len(self.game_music_files) - 1 if self.current_song_index == -1 else (self.current_song_index - 1) % len(self.game_music_files)
        self.load_and_play_song(prev_index)

    def toggle_pause(self):
        """Toggles pause/unpause for the game music."""
        if not self.game_music_files:
             print("WARN: No game music files to play/pause.")
             return

        try:
            if pygame.mixer.music.get_busy(): # Is music playing or paused?
                if self.music_playing: # We think it's playing, so pause it
                    pygame.mixer.music.pause()
                    self.music_playing = False
                    print("MUSIC: Paused")
                else: # We think it's paused, so unpause it
                    pygame.mixer.music.unpause()
                    self.music_playing = True
                    print("MUSIC: Unpaused")
            else: # Music is not busy (stopped or never started)
                 print("MUSIC: No song active or finished, starting next song.")
                 # Start the next song (or first if none was selected)
                 self.play_next_song()

        except pygame.error as e:
            print(f"ERROR: Music pause/unpause/play error: {e}")
            # Reset state potentially
            self.music_playing = pygame.mixer.music.get_busy() and not self.music_playing # Try to resync based on mixer state

    def handle_music_end_event(self):
        """Called from main loop when MUSIC_END_EVENT is received."""
        print("MUSIC: Song finished, playing next.")
        # When a song naturally ends, automatically play the next one
        self.music_playing = False # Mark as not playing before starting next
        self.play_next_song()
    # --- End Music Control ---

# --- Network Server Class ---
# (Server class remains the same as previous corrected version, including set_game_instance)
class Server:
    def __init__(self, host, port):
        self.host = host; self.port = port; self.server_socket = None
        self.clients = {}; self.sockets_list = []; self.next_player_id = 1
        self.running = False; self.game_lock = threading.Lock()
        self.initial_snapshot = None; self.queued_inputs = deque()
        self.game = None # Reference to the Game instance
    def set_game_instance(self, game_instance): self.game = game_instance
    def start(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port)); self.server_socket.listen(MAX_PLAYERS)
            self.server_socket.setblocking(False); self.sockets_list = [self.server_socket]
            self.running = True; print(f"SERVER: Listening on {self.host}:{self.port}")
        except Exception as e: print(f"SERVER: Failed start - {e}"); self.running = False
    def stop(self):
        self.running = False; print("SERVER: Shutting down...")
        for sock in list(self.clients.keys()): self._disconnect_client(sock, "Server shutdown")
        if self.server_socket:
            try: self.server_socket.close()
            except Exception as e: print(f"SERVER: Error closing server socket: {e}")
        self.server_socket = None; self.sockets_list = []; self.clients = {}
        print("SERVER: Shutdown complete.")
    def _handle_new_connection(self, client_socket, address):
        if len(self.clients) >= MAX_PLAYERS -1: # Account for host player
            print(f"SERVER: Refused {address}. Server full."); msg = encode_message({'type':'error', 'message': 'Server full'})
            try:
                if msg: client_socket.sendall(msg)
            except Exception: pass
            client_socket.close(); return
        print(f"SERVER: New connection from {address}")
        client_socket.setblocking(False); self.sockets_list.append(client_socket)
    def _disconnect_client(self, client_socket, reason=""):
        if client_socket in self.sockets_list: self.sockets_list.remove(client_socket)
        player_info = self.clients.pop(client_socket, None); pid = player_info['id'] if player_info else None
        try: client_socket.close()
        except Exception as e: print(f"SERVER: Error closing client socket: {e}")
        if pid is not None:
            print(f"SERVER: Player {pid} disconnected. Reason: {reason}")
            # Remove player from game instance
            if self.game and pid in self.game.players:
                 with self.game_lock: del self.game.players[pid]
            self.broadcast_message({'type': 'player_leave', 'player_id': pid}, exclude_socket=None)
        else: print(f"SERVER: Unknown connection closed. Reason: {reason}")
    def _process_client_message(self, client_socket, message):
        msg_type = message.get('type'); game = self.game
        if not game: print("SERVER ERROR: Game ref missing!"); self._disconnect_client(client_socket, "Internal server error"); return
        if msg_type == 'join_request':
            pname = message.get('name', f"Player{self.next_player_id}")
            cidx = message.get('color_idx', self.next_player_id % len(COLOR_PLAYER_OPTIONS))
            pid = self.next_player_id; self.next_player_id += 1
            self.clients[client_socket] = {'id': pid, 'addr': client_socket.getpeername(), 'name': pname, 'color_idx': cidx}
            print(f"SERVER: Player {pid} ('{pname}') joining...")
            start_x, start_y = 0, 0
            if game.core: start_x, start_y = grid_to_world_center(game.core.grid_x, game.core.grid_y - (1 + pid))
            else: start_x, start_y = game.map_width_px / 2, game.map_height_px / 2
            start_x = max(TILE_SIZE, min(start_x, game.map_width_px - TILE_SIZE))
            start_y = max(TILE_SIZE, min(start_y, game.map_height_px - TILE_SIZE))
            new_player_obj = Player(start_x, start_y, pid, name=pname, color_index=cidx)
            with self.game_lock: game.players[pid] = new_player_obj
            print(f"SERVER: Added Player {pid} to game.")
            try: # Send ID
                 id_msg = encode_message({'type': 'assign_id', 'data': {'id': pid}})
                 if id_msg: client_socket.sendall(id_msg); print(f"SERVER: Sent assign_id ({pid})")
                 else: raise ValueError("Encode ID failed")
            except Exception as e: print(f"SERVER: Error sending ID to {pid}: {e}"); self._disconnect_client(client_socket, "Send ID failed"); return
            fresh_snapshot = None # Generate snapshot AFTER adding player
            try:
                with self.game_lock: fresh_snapshot = game.get_full_snapshot()
                if not fresh_snapshot: raise ValueError("Snapshot gen failed")
                print(f"SERVER: Generated fresh snapshot")
            except Exception as e: print(f"SERVER: Error gen snapshot: {e}"); self._disconnect_client(client_socket, "Snapshot gen error"); return
            try: # Send State
                state_msg = encode_message({'type': 'initial_state', 'data': fresh_snapshot})
                if state_msg: client_socket.sendall(state_msg); print(f"SERVER: Sent initial state to {pid}")
                else: raise ValueError("Encode state failed")
            except Exception as e: print(f"SERVER: Error sending state to {pid}: {e}"); self._disconnect_client(client_socket, "Send state failed"); return
            # Inform others
            new_p_state = fresh_snapshot['players'].get(str(pid)) or fresh_snapshot['players'].get(pid)
            if new_p_state:
                 self.broadcast_message({'type': 'player_join', 'data': new_p_state}, exclude_socket=client_socket)
                 print(f"SERVER: Broadcasted join for {pid}.")
            else: print(f"CRITICAL WARN: State for new player {pid} not in fresh snapshot!")
        elif msg_type == 'input':
            player_info = self.clients.get(client_socket)
            if player_info: payload = message.get('payload');
            if payload: self.queued_inputs.append({'player_id': player_info['id'], 'payload': payload})
        else: print(f"SERVER: Unknown msg type '{msg_type}'")
    def update(self):
        if not self.running: return
        try: read_sockets, _, except_sockets = select.select(self.sockets_list, [], self.sockets_list, 0.01)
        except ValueError: # Handle closed socket error during select
             valid_sockets = [s for s in self.sockets_list if s and s.fileno() >= 0]
             closed_sockets = [s for s in self.sockets_list if s not in valid_sockets]
             self.sockets_list = valid_sockets
             for sock in closed_sockets: self._disconnect_client(sock, "Invalid socket detected in select")
             return # Skip this update cycle
        for notified in read_sockets:
            if notified == self.server_socket:
                try: client_sock, addr = self.server_socket.accept(); self._handle_new_connection(client_sock, addr)
                except Exception as e: print(f"SERVER: Error accept connection: {e}")
            else:
                try:
                    message = receive_message(notified)
                    if message is None: self._disconnect_client(notified, "Connection closed")
                    else: self._process_client_message(notified, message)
                except (ConnectionResetError, ConnectionAbortedError) as e: self._disconnect_client(notified, f"Connection error: {e}")
                except Exception as e: print(f"SERVER: Error process client msg: {e}"); self._disconnect_client(notified, f"Processing error: {e}")
        for notified in except_sockets: self._disconnect_client(notified, "Socket exception")
    def get_queued_inputs(self): inputs = list(self.queued_inputs); self.queued_inputs.clear(); return inputs
    def broadcast_message(self, msg_data, exclude_socket=None):
        msg_bytes = encode_message(msg_data)
        if not msg_bytes: print("SERVER: Encode broadcast failed."); return
        for sock in list(self.clients.keys()):
            if sock != exclude_socket:
                try: sock.sendall(msg_bytes)
                except Exception as e: print(f"SERVER: Error broadcast to {self.clients.get(sock,{}).get('id','?')}: {e}"); self._disconnect_client(sock, f"Broadcast error: {e}")

# --- Network Client Class ---
# (Client class remains the same as previous corrected version)
class Client:
    def __init__(self, host_ip, port, player_settings):
        self.host_ip = host_ip; self.port = port; self.player_settings = player_settings
        self.socket = None; self.connected = False; self.running = False
        self.received_messages = deque()
    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM); self.socket.settimeout(5.0)
            print(f"CLIENT: Connecting to {self.host_ip}:{self.port}..."); self.socket.connect((self.host_ip, self.port))
            self.socket.setblocking(False); self.connected = True; self.running = True; print(f"CLIENT: Connected!")
            join_msg = {'type': 'join_request', 'name': self.player_settings.get('name','?'), 'color_idx': self.player_settings.get('color_index',0)}
            self.send_message(join_msg); return True
        except socket.timeout: print(f"CLIENT: Timeout."); self.disconnect(); return False
        except Exception as e: print(f"CLIENT: Connect failed - {e}"); self.disconnect(); return False
    def disconnect(self):
        self.running = False; self.connected = False
        if self.socket: print("CLIENT: Disconnecting...")
        try: self.socket.close()
        except Exception as e: print(f"CLIENT: Error closing: {e}")
        self.socket = None; print("CLIENT: Disconnected.")
    def send_message(self, msg_data):
        if not self.connected or not self.socket: return False
        msg_bytes = encode_message(msg_data)
        if not msg_bytes: print("CLIENT: Encode failed."); return False
        try: self.socket.sendall(msg_bytes); return True
        except Exception as e: print(f"CLIENT: Send error: {e}."); self.disconnect(); return False
    def update(self):
        if not self.running or not self.connected: return
        while True:
            try:
                ready, _, _ = select.select([self.socket], [], [], 0);
                if not ready: break
                message = receive_message(self.socket)
                if message is None: print("CLIENT: Server disconnected."); self.disconnect(); break
                else: self.received_messages.append(message)
            except (ConnectionResetError, ConnectionAbortedError): print("CLIENT: Connection lost."); self.disconnect(); break
            except socket.error as e:
                 if e.errno != 10035 and e.errno != 11: print(f"CLIENT: Recv error: {e}."); self.disconnect()
                 break # Break on error or no data
            except Exception as e: print(f"CLIENT: Unexpected recv error: {e}"); self.disconnect(); break
    def get_received_messages(self): msgs = list(self.received_messages); self.received_messages.clear(); return msgs


# --- Main Menu Class ---
# (MainMenu class remains the same as previous version)
class MainMenu:
    def __init__(self, screen, clock):
        self.screen = screen; self.clock = clock; self.buttons = []; self.title = "Mindurka Reworked"
        self.selected_action = None
        button_defs = [
            ("Singleplayer", "play_sp", -100, True), ("Host LAN Game", "host_mp", -50, True),
            ("Join LAN Game", "join_mp", 0, True), ("Settings", "settings", 50, True), ("Quit", "quit", 120, True) ]
        cx, cy = screen.get_width() // 2, screen.get_height() // 2 + 50
        bw, bh = 250, 50
        for text, action, y_off, enabled in button_defs:
            r = pygame.Rect(cx - bw // 2, cy + y_off - bh // 2, bw, bh)
            self.buttons.append({'rect': r, 'text': text, 'action': action, 'enabled': enabled})
    def handle_event(self, event):
        self.selected_action = None
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for btn in self.buttons:
                if btn['enabled'] and btn['rect'].collidepoint(event.pos): self.selected_action = btn['action']; break
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: self.selected_action = "quit"
    def get_action(self): action = self.selected_action; self.selected_action = None; return action
    def draw(self):
        self.screen.fill(COLOR_DARK_GRAY)
        cx, ch = self.screen.get_width(), self.screen.get_height()
        draw_text(self.screen, self.title, 80, cx // 2, ch // 4, COLOR_MENU_TITLE, align="center")
        mouse_pos = pygame.mouse.get_pos()
        for btn in self.buttons:
            color = COLOR_MENU_BUTTON_DISABLED if not btn['enabled'] else \
                    COLOR_MENU_BUTTON_HOVER if btn['rect'].collidepoint(mouse_pos) else COLOR_MENU_BUTTON
            text_col = COLOR_GRAY if not btn['enabled'] else COLOR_WHITE
            pygame.draw.rect(self.screen, color, btn['rect']); pygame.draw.rect(self.screen, COLOR_BLACK, btn['rect'], 2)
            draw_text(self.screen, btn['text'], 30, btn['rect'].centerx, btn['rect'].centery, text_col, align="center")
        draw_text(self.screen, "Version: a15", 16, cx - 10, ch - 20, COLOR_GRAY, align="bottomright")

# --- Main Application Loop ---
def main():
    pygame.init()
    pygame.font.init()

    # --- Load Application Configuration ---
    # Define default config first
    app_config = {
        'name': "Player",
        'color_index': 0,
        'host_ip': "127.0.0.1",
        'resolution_index': DEFAULT_RESOLUTION_INDEX,
        'network_interval': DEFAULT_NETWORK_UPDATE_INTERVAL,
        'volume': DEFAULT_MUSIC_VOLUME, # Default volume
    }
    loaded_volume = DEFAULT_MUSIC_VOLUME # Separate variable for loading

    print(f"Attempting to load configuration from {CONFIG_FILENAME}...")
    try:
        with open(CONFIG_FILENAME, 'r') as f:
            loaded_config = json.load(f)
            # Validate and update app_config with loaded values
            app_config['name'] = str(loaded_config.get('name', app_config['name'])).strip()[:16]
            app_config['color_index'] = int(loaded_config.get('color_index', app_config['color_index']))
            app_config['host_ip'] = str(loaded_config.get('host_ip', app_config['host_ip'])).strip()
            app_config['resolution_index'] = int(loaded_config.get('resolution_index', app_config['resolution_index']))
            app_config['network_interval'] = float(loaded_config.get('network_interval', app_config['network_interval']))
            loaded_volume = max(0.0, min(1.0, float(loaded_config.get('volume', DEFAULT_MUSIC_VOLUME))))
            print("Configuration loaded successfully.")
    except FileNotFoundError:
        print(f"Configuration file '{CONFIG_FILENAME}' not found. Using defaults.")
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        print(f"Error loading or parsing configuration file: {e}. Using defaults.")

    # --- Validate loaded/default config values ---
    if not (0 <= app_config['resolution_index'] < len(AVAILABLE_RESOLUTIONS)):
        print(f"WARN: Invalid resolution index ({app_config['resolution_index']}) found. Resetting to default.")
        app_config['resolution_index'] = DEFAULT_RESOLUTION_INDEX
    try:
        net_interval = float(app_config['network_interval'])
        app_config['network_interval'] = max(MIN_NETWORK_UPDATE_INTERVAL, min(net_interval, MAX_NETWORK_UPDATE_INTERVAL))
    except (ValueError, TypeError):
        print(f"WARN: Invalid network interval ({app_config['network_interval']}) found. Resetting to default.")
        app_config['network_interval'] = DEFAULT_NETWORK_UPDATE_INTERVAL
    if not (0 <= app_config['color_index'] < len(COLOR_PLAYER_OPTIONS)):
         print(f"WARN: Invalid color index ({app_config['color_index']}). Clamping.")
         app_config['color_index'] = max(0, min(app_config['color_index'], len(COLOR_PLAYER_OPTIONS) - 1))
    app_config['volume'] = loaded_volume # Assign validated volume to app_config

    print(f"Final Initial Config: Name='{app_config['name']}', ResIndex={app_config['resolution_index']}, NetInterval={app_config['network_interval']:.4f}, Volume={app_config['volume']:.2f}")
    # --- END Load Configuration ---

    # --- Mixer Initialization ---
    menu_music_loaded = False
    try:
        pygame.mixer.init()
        print("Audio Mixer Initialized.")
        pygame.mixer.music.set_volume(app_config['volume']) # Set initial volume
        try:
            if os.path.exists(MAIN_MENU_MUSIC_FILE):
                pygame.mixer.music.load(MAIN_MENU_MUSIC_FILE)
                print(f"Main menu music '{MAIN_MENU_MUSIC_FILE}' loaded.")
                menu_music_loaded = True
            else:
                print(f"WARN: Main menu music file not found: {MAIN_MENU_MUSIC_FILE}")
        except pygame.error as e:
            print(f"ERROR: Could not load main menu music: {e}")
    except pygame.error as e:
        print(f"ERROR: Failed to initialize audio mixer: {e}")
    # -----------------------------

    # --- Screen Initialization ---
    try:
        initial_width, initial_height = AVAILABLE_RESOLUTIONS[app_config['resolution_index']]
    except IndexError:
        print(f"FATAL: Corrected resolution index still invalid? Using default.")
        app_config['resolution_index'] = DEFAULT_RESOLUTION_INDEX
        initial_width, initial_height = AVAILABLE_RESOLUTIONS[DEFAULT_RESOLUTION_INDEX]
    screen = pygame.display.set_mode((initial_width, initial_height))
    pygame.display.set_caption(GAME_TITLE)
    clock = pygame.time.Clock()
    # --- End Screen Init ---

    # --- Font Initialization ---
    init_fonts()
    if not font_medium: print("FATAL: Font load failed."); pygame.quit(); sys.exit()
    # -------------------------

    # --- State Definitions ---
    STATE_MAIN_MENU = 0
    STATE_PLAYING_SP = 1
    STATE_SETTINGS = 2
    STATE_HOSTING = 3
    STATE_JOINING = 4
    STATE_PLAYING_MP_CLIENT = 5
    STATE_SHOW_IP = 6
    STATE_PROMPT_NEW_LOAD = 7
    # -----------------------

    current_state = STATE_MAIN_MENU
    previous_state = -1 # Track state changes for music

    # --- Initialize Menus ---
    main_menu = MainMenu(screen, clock)
    settings_menu = SettingsMenu(screen, clock,
                                 app_config['name'], app_config['color_index'],
                                 app_config['resolution_index'], app_config['network_interval'])
    settings_menu.current_ip = app_config['host_ip']
    # ----------------------

    # --- Game and Network Instance Variables ---
    game_instance = None
    server_instance = None
    client_instance = None
    # -----------------------------------------

    app_running = True
    current_network_interval = app_config['network_interval']
    last_network_update_time = 0.0
    local_ip_address = get_local_ip()

    # --- Variables for New/Load Prompt ---
    prompt_mode_target = None # 'sp' or 'host'
    prompt_save_exists = False
    prompt_buttons = []
    # ------------------------------------

    # --- Helper Function for Save/Load ---
    def save_game_state(game_mode):
        """Saves the current game instance state to the appropriate file."""
        if not game_instance: return False
        filename = SAVE_FILENAME_SP if game_mode == 'sp' else SAVE_FILENAME_HOST
        print(f"Attempting to save game state to {filename}...")
        try:
            snapshot = game_instance.get_full_snapshot()
            if snapshot:
                 snapshot['game_mode_for_save'] = game_mode # Ensure mode is saved
                 with open(filename, 'w') as f:
                      json.dump(snapshot, f, indent=2)
                 print("Game state saved successfully.")
                 return True
            else:
                 print("Failed to get game snapshot for saving.")
                 return False
        except Exception as e:
            print(f"ERROR: Could not save game state: {e}")
            return False

    def load_game_state(game_mode):
        """Loads game state from the appropriate file."""
        filename = SAVE_FILENAME_SP if game_mode == 'sp' else SAVE_FILENAME_HOST
        print(f"Attempting to load game state from {filename}...")
        try:
            with open(filename, 'r') as f:
                load_data = json.load(f)
            loaded_mode = load_data.get('game_mode_for_save')
            if loaded_mode != game_mode:
                 print(f"WARN: Save file mode ({loaded_mode}) doesn't match requested mode ({game_mode}). Aborting load.")
                 return None
            print("Game state loaded successfully.")
            return load_data
        except FileNotFoundError:
            print(f"Save file '{filename}' not found.")
            return None
        except (json.JSONDecodeError, TypeError, ValueError, KeyError) as e:
            print(f"Error loading or parsing save file: {e}. Cannot load.")
            return None
    # --- End Save/Load Helpers ---

    # --- Play initial menu music ---
    if menu_music_loaded:
        try:
            pygame.mixer.music.play(-1, fade_ms=MUSIC_FADE_MS)
        except pygame.error as e:
            print(f"ERROR: Failed to play initial menu music: {e}")
    # -----------------------------

    # =================== #
    # --- MAIN LOOP --- #
    # =================== #
    while app_running:
        dt = min(clock.tick(FPS) / 1000.0, 0.1) # Delta time in seconds
        events_this_frame = pygame.event.get()
        action = None # Action determined by menu or game state changes

        # --- Global Event Processing (Quit, Music End) ---
        for event in events_this_frame:
            if event.type == pygame.QUIT:
                app_running = False; break
            if event.type == MUSIC_END_EVENT:
                if game_instance and current_state in [STATE_PLAYING_SP, STATE_HOSTING, STATE_PLAYING_MP_CLIENT]:
                    game_instance.handle_music_end_event()
        if not app_running: break
        # --- End Global Events ---

        # --- State Change Music & Volume Logic ---
        if current_state != previous_state:
            print(f"State changed from {previous_state} to {current_state}")
            is_game_state = current_state in [STATE_PLAYING_SP, STATE_HOSTING, STATE_PLAYING_MP_CLIENT]
            was_menu_state = previous_state == STATE_MAIN_MENU
            was_game_state = previous_state in [STATE_PLAYING_SP, STATE_HOSTING, STATE_PLAYING_MP_CLIENT]
            is_settings_state = current_state == STATE_SETTINGS

            # Fade out music if leaving menu (but NOT going to settings) OR leaving game
            if (was_menu_state and not is_settings_state) or was_game_state:
                 if pygame.mixer.music.get_busy():
                     try: pygame.mixer.music.fadeout(MUSIC_FADE_MS)
                     except pygame.error: pass # Ignore errors during fadeout

            # Play menu music if entering MAIN MENU
            if current_state == STATE_MAIN_MENU and menu_music_loaded:
                 if not pygame.mixer.music.get_busy(): # Start only if not already playing/fading
                     try:
                         pygame.mixer.music.stop()
                         pygame.mixer.music.load(MAIN_MENU_MUSIC_FILE)
                         pygame.mixer.music.set_volume(app_config['volume'])
                         pygame.mixer.music.play(-1, fade_ms=MUSIC_FADE_MS)
                         print(f"Menu music playing at volume {app_config['volume']:.2f}.")
                     except pygame.error as e: print(f"ERROR: Failed to play menu music: {e}")

            # Set mixer volume when entering any game state or settings
            if is_game_state or is_settings_state:
                 try:
                      pygame.mixer.music.set_volume(app_config['volume'])
                      print(f"State {current_state} entered, mixer volume set to {app_config['volume']:.2f}.")
                 except pygame.error as e: print(f"WARN: Error setting volume on state entry: {e}")

            previous_state = current_state # Update tracker
        # --- END State Change Music Logic ---

        # --- Update Network Instances ---
        if server_instance and server_instance.running: server_instance.update()
        if client_instance and client_instance.running:
            client_instance.update()
            if not client_instance.connected and current_state == STATE_PLAYING_MP_CLIENT:
                print("CLIENT: Disconnected. Returning to menu.")
                current_state = STATE_MAIN_MENU; game_instance = None; client_instance = None
                continue
        # --- End Network Update ---

        # -------------------------- #
        # --- STATE MACHINE --- #
        # -------------------------- #

        # --- Main Menu ---
        if current_state == STATE_MAIN_MENU:
            main_menu.screen = screen
            for event in events_this_frame: main_menu.handle_event(event)
            action = main_menu.get_action()
            if action == "quit":
                app_running = False
            elif action == "play_sp" or action == "host_mp":
                # Transition to Prompt State
                prompt_mode_target = 'sp' if action == "play_sp" else 'host'
                save_file = SAVE_FILENAME_SP if prompt_mode_target == 'sp' else SAVE_FILENAME_HOST
                prompt_save_exists = os.path.exists(save_file)
                current_state = STATE_PROMPT_NEW_LOAD
                # Setup prompt buttons
                prompt_buttons = []
                btn_w, btn_h = 250, 50; cx, cy = screen.get_width()//2, screen.get_height()//2
                prompt_buttons.append({'rect': pygame.Rect(cx-btn_w//2, cy-btn_h*1.5-10, btn_w, btn_h), 'text': 'Start New Game', 'action': 'new_game'})
                if prompt_save_exists:
                     prompt_buttons.append({'rect': pygame.Rect(cx-btn_w//2, cy-btn_h*0.5, btn_w, btn_h), 'text': 'Load Game', 'action': 'load_game'})
                prompt_buttons.append({'rect': pygame.Rect(cx-btn_w//2, cy+btn_h*0.5+10, btn_w, btn_h), 'text': 'Cancel', 'action': 'cancel_prompt'})
            elif action == "join_mp":
                current_state = STATE_JOINING;
                target_ip = app_config.get('host_ip', '127.0.0.1')
                client_instance = Client(target_ip, DEFAULT_PORT, app_config)
                if client_instance.connect():
                    game_instance = Game(screen, clock, app_config, network_mode="client", client=client_instance)
                    # Client volume is controlled locally via slider, config sets initial
                    if game_instance: game_instance.current_volume = app_config['volume']
                    current_state = STATE_PLAYING_MP_CLIENT
                else:
                    print(f"Error: Failed connect to {target_ip}."); client_instance = None; current_state = STATE_MAIN_MENU
            elif action == "settings":
                settings_menu.screen = screen;
                settings_menu.current_name = app_config['name']
                settings_menu.selected_color_index = app_config['color_index']
                settings_menu.current_resolution_index = app_config['resolution_index']
                settings_menu.current_network_interval_str = f"{current_network_interval:.4f}"
                settings_menu.current_ip = app_config['host_ip']
                settings_menu.input_active = settings_menu.ip_input_active = settings_menu.interval_input_active = False
                settings_menu._setup_ui();
                current_state = STATE_SETTINGS

        # --- New/Load Prompt ---
        elif current_state == STATE_PROMPT_NEW_LOAD:
            clicked_action = None
            for event in events_this_frame:
                 if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                      for btn in prompt_buttons:
                           if btn['rect'].collidepoint(event.pos): clicked_action = btn['action']; break
                 elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: clicked_action = 'cancel_prompt'
            if clicked_action:
                 if clicked_action == 'cancel_prompt': current_state = STATE_MAIN_MENU
                 else:
                      load_data = None
                      if clicked_action == 'load_game':
                           load_data = load_game_state(prompt_mode_target)
                           if load_data is None: current_state = STATE_MAIN_MENU; continue # Load failed

                      # Start Game (New or Loaded)
                      if prompt_mode_target == 'sp':
                           game_instance = Game(screen, clock, app_config, network_mode='sp', load_data=load_data)
                           if game_instance: game_instance.current_volume = app_config['volume']
                           current_state = STATE_PLAYING_SP
                      elif prompt_mode_target == 'host':
                           server_instance = Server('', DEFAULT_PORT)
                           game_instance = Game(screen, clock, app_config, network_mode='host', server=server_instance, load_data=load_data)
                           if game_instance: game_instance.current_volume = app_config['volume']
                           server_instance.set_game_instance(game_instance)
                           server_instance.start()
                           if server_instance.running:
                                with server_instance.game_lock: server_instance.initial_snapshot = game_instance.get_full_snapshot()
                                print(f"HOST: Initial snapshot created for {'loaded' if load_data else 'new'} game.")
                                current_state = STATE_SHOW_IP
                           else:
                                print("Error: Failed server start."); server_instance=None; game_instance=None; current_state = STATE_MAIN_MENU
            # Drawing handled below in draw section

        # --- Settings ---
        elif current_state == STATE_SETTINGS:
            settings_menu.screen = screen;
            settings_action = None
            for event in events_this_frame:
                settings_action = settings_menu.handle_event(event)
                if settings_action == 'back': break
            settings_menu.update(dt)
            if settings_action == 'back':
                new_settings = settings_menu.get_settings();
                resolution_changed = (new_settings['resolution_index'] != app_config['resolution_index'])
                # Update app_config (volume not handled by settings menu)
                app_config.update({k: v for k, v in new_settings.items() if k != 'volume'}) # Exclude volume
                current_network_interval = app_config['network_interval']
                print(f"Settings Updated & Stored in app_config")
                if resolution_changed: # Apply resolution change
                    try:
                        new_w, new_h = AVAILABLE_RESOLUTIONS[app_config['resolution_index']]
                        screen = pygame.display.set_mode((new_w, new_h))
                        main_menu.screen = screen; settings_menu.screen = screen
                        if game_instance: game_instance.screen = screen
                    except Exception as e:
                        print(f"ERROR applying resolution: {e}")
                        app_config['resolution_index'] = DEFAULT_RESOLUTION_INDEX
                        def_w, def_h = AVAILABLE_RESOLUTIONS[DEFAULT_RESOLUTION_INDEX]
                        screen = pygame.display.set_mode((def_w, def_h))
                        main_menu.screen = screen; settings_menu.screen = screen
                        if game_instance: game_instance.screen = screen
                current_state = STATE_MAIN_MENU

        # --- Show IP ---
        elif current_state == STATE_SHOW_IP:
            esc_pressed = False # Only check for ESC to cancel
            for event in events_this_frame:
                 if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: esc_pressed = True; break
            if esc_pressed:
                 print("Hosting cancelled."); current_state = STATE_MAIN_MENU
                 if server_instance: server_instance.stop(); server_instance = None
                 game_instance = None
            else: current_state = STATE_HOSTING # Auto-transition to hosting logic
            # Drawing handled below

        # --- Hosting Game ---
        elif current_state == STATE_HOSTING:
            if not game_instance or not server_instance or not server_instance.running:
                print("ERROR: Hosting state invalid."); current_state = STATE_MAIN_MENU
                if server_instance: server_instance.stop(); server_instance = None
                game_instance = None; continue

            queued_inputs = server_instance.get_queued_inputs()
            host_esc_pressed = False
            with server_instance.game_lock:
                for net_input in queued_inputs: # Process client inputs
                    pid, payload = net_input['player_id'], net_input['payload']
                    act_type, act_data = payload.get('action'), payload.get('data')
                    player = game_instance.players.get(pid)
                    if player: # Apply actions
                         if act_type == 'move': player.move_x, player.move_y = act_data.get('x',0), act_data.get('y',0)
                         elif act_type == 'place': game_instance.action_place_structure(pid, act_data['type'], act_data['gx'], act_data['gy'], act_data['orient'])
                         elif act_type == 'remove': game_instance.action_remove_structure(pid, act_data['gx'], act_data['gy'])
                         elif act_type == 'upgrade': game_instance.action_upgrade_structure(pid, act_data['gx'], act_data['gy'])

                game_instance.handle_events(events_this_frame) # Handle host input
                if not game_instance.running: host_esc_pressed = True # Host pressed ESC

                game_instance.dt = dt; game_instance.update() # Update game simulation

                app_config['volume'] = game_instance.current_volume # Sync volume back
                try: pygame.mixer.music.set_volume(app_config['volume'])
                except pygame.error: pass

            current_time = time.time() # Broadcast state periodically
            if current_time - last_network_update_time >= current_network_interval:
                last_network_update_time = current_time; snapshot = None
                with server_instance.game_lock: snapshot = game_instance.get_full_snapshot()
                if snapshot: server_instance.broadcast_message({'type': 'state_update', 'data': snapshot})

            if host_esc_pressed: # Handle host leaving
                save_game_state('host')
                current_state = STATE_MAIN_MENU;
                if server_instance: server_instance.stop(); server_instance = None;
                game_instance = None

        # --- Playing as Client ---
        elif current_state == STATE_PLAYING_MP_CLIENT:
            if not game_instance or not client_instance:
                print("ERROR: Client state invalid."); current_state = STATE_MAIN_MENU
                if client_instance: client_instance.disconnect(); client_instance = None
                game_instance = None; continue

            game_instance.screen = screen # Update screen ref
            client_esc_pressed = False
            error_processing = False
            try: # Process server messages
                for msg in client_instance.get_received_messages():
                    msg_type, msg_data = msg.get('type'), msg.get('data')
                    if not msg_type: continue
                    if msg_type == 'initial_state': game_instance.apply_full_snapshot(msg_data)
                    elif msg_type == 'state_update': game_instance.apply_full_snapshot(msg_data)
                    else: game_instance.apply_incremental_update(msg)
            except Exception as e:
                print(f"CLIENT ERROR processing server msg: {e}"); # import traceback; traceback.print_exc()
                client_esc_pressed = True; error_processing = True # Force exit

            if not error_processing: # Handle local input and update visuals
                game_instance.handle_events(events_this_frame)
                if not game_instance.running: client_esc_pressed = True # Client pressed ESC

                app_config['volume'] = game_instance.current_volume # Sync volume back
                try: pygame.mixer.music.set_volume(app_config['volume'])
                except pygame.error: pass

                game_instance.dt = dt; game_instance.update() # Client-side updates

            if client_esc_pressed: # Handle client leaving
                current_state = STATE_MAIN_MENU
                if client_instance: client_instance.disconnect(); client_instance = None
                game_instance = None

        # --- Playing Singleplayer ---
        elif current_state == STATE_PLAYING_SP:
            if not game_instance:
                print("ERROR: SP state invalid."); current_state = STATE_MAIN_MENU; continue

            game_instance.screen = screen
            sp_esc_pressed = False

            game_instance.handle_events(events_this_frame) # Handle input
            if not game_instance.running: sp_esc_pressed = True # Player pressed ESC

            game_instance.dt = dt; game_instance.update() # Update game simulation

            app_config['volume'] = game_instance.current_volume # Sync volume back
            try: pygame.mixer.music.set_volume(app_config['volume'])
            except pygame.error: pass

            if sp_esc_pressed: # Handle player leaving
                save_game_state('sp')
                current_state = STATE_MAIN_MENU; game_instance = None

        # --- End State Machine ---

        # ------------------- #
        # --- DRAWING --- #
        # ------------------- #
        screen.fill(COLOR_DARK_GRAY) # Default background

        if current_state == STATE_MAIN_MENU:
            if main_menu: main_menu.draw()
        elif current_state == STATE_PROMPT_NEW_LOAD:
            # Prompt draws itself
            prompt_title = "Singleplayer" if prompt_mode_target == 'sp' else "Host Game"
            draw_text(screen, prompt_title, 48, screen.get_width()//2, screen.get_height()//3, COLOR_UI_HEADER, align="center")
            mouse_pos_draw = pygame.mouse.get_pos()
            for btn in prompt_buttons:
                 color = COLOR_MENU_BUTTON_HOVER if btn['rect'].collidepoint(mouse_pos_draw) else COLOR_MENU_BUTTON
                 pygame.draw.rect(screen, color, btn['rect'])
                 pygame.draw.rect(screen, COLOR_BLACK, btn['rect'], 2)
                 draw_text(screen, btn['text'], 30, btn['rect'].centerx, btn['rect'].centery, COLOR_WHITE, align="center")
        elif current_state == STATE_SETTINGS:
            if settings_menu: settings_menu.draw()
        elif current_state == STATE_SHOW_IP:
             # Draw IP info while briefly in this state before HOSTING starts drawing game
            current_w, current_h = screen.get_width(), screen.get_height()
            draw_text(screen, f"Hosting on IP: {local_ip_address}", 36, current_w//2, current_h//2 - 40, COLOR_WHITE, align="center")
            draw_text(screen, f"Port: {DEFAULT_PORT}", 36, current_w//2, current_h//2, COLOR_WHITE, align="center")
            draw_text(screen, f"Update Interval: {current_network_interval:.3f}s", 24, current_w//2, current_h//2 + 40, COLOR_GRAY, align="center")
            draw_text(screen, "Waiting for players... Press ESC to cancel", 24, current_w//2, current_h - 50, COLOR_GRAY, align="center")
        elif current_state in [STATE_HOSTING, STATE_PLAYING_MP_CLIENT, STATE_PLAYING_SP]:
            if game_instance: game_instance.draw()
            else: draw_text(screen, "Error: Game not loaded", 30, screen.get_width()//2, screen.get_height()//2, COLOR_RED, "center")
        elif current_state == STATE_JOINING:
            draw_text(screen, f"Connecting to {app_config.get('host_ip', '?')}...", 30, screen.get_width()//2, screen.get_height()//2, COLOR_WHITE, "center")

        pygame.display.flip() # Update the screen
    # --- End Main Loop ---


    # =================== #
    # --- CLEANUP --- #
    # =================== #
    print("Exiting Application.")

    # --- Save Game on Graceful Exit (if in SP/Host state) ---
    if game_instance and current_state in [STATE_PLAYING_SP, STATE_HOSTING]:
         save_game_state(game_instance.network_mode)
    # --- End Save Game on Exit ---

    # --- Save Application Configuration ---
    print(f"Attempting to save configuration to {CONFIG_FILENAME}...")
    try:
        # Ensure latest volume is in app_config
        if game_instance: app_config['volume'] = game_instance.current_volume
        elif 'volume' not in app_config: app_config['volume'] = DEFAULT_MUSIC_VOLUME

        with open(CONFIG_FILENAME, 'w') as f: json.dump(app_config, f, indent=4)
        print("Configuration saved successfully.")
    except IOError as e: print(f"ERROR: Could not save configuration file: {e}")
    # --- End Save Config ---

    # --- Stop Music & Mixer ---
    try:
        pygame.mixer.music.stop()
        pygame.mixer.quit()
    except pygame.error: pass
    # -------------------------

    # --- Stop Network Instances ---
    if server_instance: server_instance.stop()
    if client_instance: client_instance.disconnect()
    # --------------------------

    pygame.quit() # Uninitialize Pygame modules
    print("Application finished.")
    sys.exit()


# --- Main execution block ---
if __name__ == '__main__':
    # Print version and basic info
    print(f"Starting {GAME_TITLE} (v15.3 - Save/Load & Music Fix)...")
    print(f"Networking: {MAX_PLAYERS} players max, Port {DEFAULT_PORT}")
    print(f"Default Resolution Index: {DEFAULT_RESOLUTION_INDEX}, Default Net Interval: {DEFAULT_NETWORK_UPDATE_INTERVAL:.3f}s")
    try:
        main() # Run the main application loop
    except Exception as e: # Catch unexpected errors in main
        print("\n--- UNHANDLED TOP-LEVEL ERROR ---")
        import traceback
        traceback.print_exc()
        print("---------------------------------")
        try: pygame.quit() # Attempt cleanup
        except Exception: pass
        sys.exit("Exited due to critical error.")