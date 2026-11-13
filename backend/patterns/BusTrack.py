from gridmas import *
import math
import json
import asyncio
import requests
import datetime

# --- CONFIGURATION ---
BASE_URL = "https://tfe-opendata.com/api/v1/live_bus_times/"

# TREE GEOGRAPHY
TREE_LAT = 55.91171246811926 
TREE_LON = -3.3200582160049947
TREE_Y_PLUS_BEARING = 135 

# STOP DEFINITIONS
MY_STOPS = [
    {
        "id": "36234875",  # Avenue Leaving
        "name": "Avenue Leaving",
        "lat": 55.9103046, "lon": -3.3174695,
        "filter": None, "min_wait": 0,
        "exclude": ["45"] # Block Route 45
    },
    {
        "id": "36246836", # Back Campus
        "name": "Back Campus",
        "lat": 55.9122074, "lon": -3.3244850,
        "filter": None, "min_wait": 0,
        "exclude": []
    },
    {
        "id": "36246389", # Hermiston Park and Ride
        "name": "Hermiston Arrivals",
        "lat": 55.9171544, "lon": -3.3140322,
        "filter": None, "min_wait": 0,
        # FIX: Added 70 and X40 to the block list
        "exclude": ["45", "70", "X40"] 
    }
]

# DISPLAY SETTINGS
SEQUENCE_LENGTH = 400  
SWITCH_INTERVAL = SEQUENCE_LENGTH * 1 

MATWX = 7; MATWY = 8; MATWZ = 25

# --- BUS COLOURS ---
ROUTE_COLORS = {
    "25": (149, 27, 129), "34": (43, 33, 113), "35": (186, 49, 61),
    "45": (81, 184, 187), "32": (247, 148, 29)
}
DEFAULT_COLOR = (255, 190, 0)

# --- GLOBAL STATE ---
bus_cache = {} 
is_fetching = False

# --- HELPER CLASSES ---
class boundingBox():
    def __init__(self):
        self.minX, self.maxX = math.inf, -math.inf
        self.minY, self.maxY = math.inf, -math.inf
        self.minZ, self.maxZ = math.inf, -math.inf
        self.wX = self.wY = self.wZ = 0
    def update(self, x, y, z):
        self.minX, self.maxX = min(self.minX, x), max(self.maxX, x)
        self.minY, self.maxY = min(self.minY, y), max(self.maxY, y)
        self.minZ, self.maxZ = min(self.minZ, z), max(self.maxZ, z)
    def finalize(self):
        self.wX = self.maxX - self.minX
        self.wY = self.maxY - self.minY
        self.wZ = self.maxZ - self.minZ
    def normalize(self, x, y, z):
        lx = (x - self.minX) / self.wX if self.wX else 0
        ly = (y - self.minY) / self.wY if self.wY else 0
        lz = (z - self.minZ) / self.wZ if self.wZ else 0
        return lx, ly, lz

class matrix():
    def __init__(self, lx, ly, lz, bb):
        self._list = [[0, 0, 0] for _ in range(lx * ly * lz)]
        self._strideX = 1; self._strideY = lx; self._strideZ = lx * ly
        self._bb = bb; self._wX = lx; self._wY = ly; self._wZ = lz
    def set(self, x, y, z, val):
        if 0 <= x < self._wX and 0 <= y < self._wY and 0 <= z < self._wZ:
            self._list[x * self._strideX + y * self._strideY + z * self._strideZ] = val
    def getTree(self, x, y, z):
        localX, localY, localZ = self._bb.normalize(x, y, z)
        localX = int(localX * (self._wX - 1))
        localY = int(localY * (self._wY - 1))
        localZ = int(localZ * (self._wZ - 1))
        idx = localX * self._strideX + localY * self._strideY + localZ * self._strideZ
        return self._list[idx]
    def clear(self):
         self._list = [[0, 0, 0] for _ in range(len(self._list))]

# --- GEOMETRY MATH ---
def to_rad(deg): return deg * math.pi / 180.0
def to_deg(rad): return rad * 180.0 / math.pi
def calculate_bearing(lat1, lon1, lat2, lon2):
    phi1 = to_rad(lat1); phi2 = to_rad(lat2); dLon = to_rad(lon2 - lon1)
    y = math.sin(dLon) * math.cos(phi2)
    x = math.cos(phi1)*math.sin(phi2) - math.sin(phi1)*math.cos(phi2)*math.cos(dLon)
    theta = math.atan2(y, x)
    return (to_deg(theta) + 360.0) % 360.0

# --- FONT ---
BIG_FONT = {
    '1': [[0,0,1,0,0],[0,1,1,0,0],[0,0,1,0,0],[0,0,1,0,0],[0,0,1,0,0],[0,0,1,0,0],[0,1,1,1,0]],
    '2': [[0,1,1,1,0],[1,0,0,0,1],[0,0,0,0,1],[0,0,0,1,0],[0,0,1,0,0],[0,1,0,0,0],[1,1,1,1,1]],
    '3': [[0,1,1,1,0],[1,0,0,0,1],[0,0,0,0,1],[0,0,1,1,0],[0,0,0,0,1],[1,0,0,0,1],[0,1,1,1,0]],
    '4': [[0,0,0,1,0],[0,0,1,1,0],[0,1,0,1,0],[1,0,0,1,0],[1,1,1,1,1],[0,0,0,1,0],[0,0,0,1,0]],
    '5': [[1,1,1,1,1],[1,0,0,0,0],[1,1,1,1,0],[0,0,0,0,1],[0,0,0,0,1],[1,0,0,0,1],[0,1,1,1,0]],
    '6': [[0,1,1,1,0],[1,0,0,0,0],[1,0,0,0,0],[1,1,1,1,0],[1,0,0,0,1],[1,0,0,0,1],[0,1,1,1,0]],
    '7': [[1,1,1,1,1],[0,0,0,0,1],[0,0,0,1,0],[0,0,1,0,0],[0,1,0,0,0],[0,1,0,0,0],[0,1,0,0,0]],
    '8': [[0,1,1,1,0],[1,0,0,0,1],[1,0,0,0,1],[0,1,1,1,0],[1,0,0,0,1],[1,0,0,0,1],[0,1,1,1,0]],
    '9': [[0,1,1,1,0],[1,0,0,0,1],[1,0,0,0,1],[0,1,1,1,1],[0,0,0,0,1],[0,0,0,0,1],[0,1,1,1,0]],
    '0': [[0,1,1,1,0],[1,0,0,0,1],[1,0,0,1,1],[1,1,0,0,1],[1,0,0,0,1],[1,0,0,0,1],[0,1,1,1,0]],
    '?': [[0,1,1,1,0],[1,0,0,0,1],[0,0,0,1,0],[0,0,1,0,0],[0,0,1,0,0],[0,0,0,0,0],[0,0,1,0,0]]
}

# --- SETUP ---
coords_data = coords()
treeBB = boundingBox()
for i in coords_data: treeBB.update(i[0], i[1], i[2])
treeBB.finalize()
workMat = matrix(MATWX, MATWY, MATWZ, treeBB)
t = 0

# --- DATA FETCHING (SORT LOGIC) ---
def parse_best_bus(bus_data, filter_str=None, min_wait_threshold=0, excluded_routes=None):
    if not bus_data: return {'minutes': 99, 'route': '??'}
    now = datetime.datetime.now()
    current_minutes = now.hour * 60 + now.minute
    
    if excluded_routes is None: excluded_routes = []
    
    valid_buses = [] # Collect all valid options

    for route in bus_data:
        r_name = route.get('routeName', '??')
        
        # Check Exclusion
        if r_name in excluded_routes:
            continue

        for dep in route.get('departures', []):
            dest = dep.get('destination', '').lower()
            
            # Filter Check
            matches_filter = True
            if filter_str:
                matches_filter = False
                keywords = [k.strip().lower() for k in filter_str.split(',')]
                for k in keywords:
                    if k in dest: matches_filter = True
            
            if not matches_filter: continue 

            # Time Calc
            local_time = dep.get('ineoUTCTime', '')
            bus_mins = 9999
            if len(local_time) >= 5:
                try:
                    h, m = int(local_time[:2]), int(local_time[3:5])
                    bus_mins = h * 60 + m
                    if bus_mins < 360 and current_minutes > 1080: bus_mins += 1440
                except: pass
            
            if bus_mins == 9999 and dep.get('displayTime') == 'Due':
                 bus_mins = current_minutes
            
            if bus_mins != 9999:
                 wait = bus_mins - current_minutes
                 
                 # --- DEBUG PRINTOUT ---
                 status_msg = ""
                 if wait < min_wait_threshold: status_msg = "(IGNORED/GHOST)"
                 print(f"   Route {r_name} to {dest}: {wait}m {status_msg}")
                 
                 if wait < min_wait_threshold: continue 
                 
                 # Add to list for sorting
                 valid_buses.append({
                     'route': r_name,
                     'minutes': wait,
                     'dest': dest
                 })

    # SORT BY TIME (Ascending)
    valid_buses.sort(key=lambda x: x['minutes'])

    if len(valid_buses) > 0:
        return valid_buses[0] # Return the single best bus
    
    return {'minutes': 99, 'route': '??'}

def fetch_loop():
    global bus_cache, is_fetching
    for stop in MY_STOPS:
        stop_id = stop['id']
        filter_rule = stop['filter']
        threshold = stop.get('min_wait', 0)
        excluded = stop.get('exclude', [])
        
        print(f"\n--- Fetching {stop['name']} ---") # Debug Header
        
        try:
            response = requests.get(f"{BASE_URL}{stop_id}")
            if response.status_code == 200:
                data = response.json()
                info = parse_best_bus(data, filter_rule, threshold, excluded)
                bus_cache[stop_id] = info
                print(f"-> CHOSEN: Route {info['route']} in {info['minutes']}m")
        except Exception as e: print(f"Error {stop_id}: {e}")
    is_fetching = False

# --- RENDERER ---
def draw_text_angular(pixels_list, digit_char, bearing_deg, color_rgb):
    font_grid = BIG_FONT.get(digit_char, BIG_FONT['?'])
    font_h, font_w = len(font_grid), len(font_grid[0])  
    
    WIDTH_ANGLE = 120  
    Z_BOTTOM = 0.4; Z_TOP = 2.8       
    target_facing_rad = to_rad(90 - (bearing_deg - TREE_Y_PLUS_BEARING))

    for pixel in pixels_list:
        if Z_BOTTOM < pixel.z < Z_TOP:
            p_angle = math.atan2(pixel.y, pixel.x)
            diff = math.atan2(math.sin(p_angle - target_facing_rad), math.cos(p_angle - target_facing_rad))
            diff_deg = to_deg(diff)
            if abs(diff_deg) < (WIDTH_ANGLE / 2):
                norm_x = 1.0 - ((diff_deg + (WIDTH_ANGLE/2)) / WIDTH_ANGLE)
                font_x = int(norm_x * font_w)
                norm_y = (Z_TOP - pixel.z) / (Z_TOP - Z_BOTTOM)
                font_y = int(norm_y * font_h)
                if 0 <= font_x < font_w and 0 <= font_y < font_h:
                    if font_grid[font_y][font_x] == 1: pixel.set_rgb(*color_rgb) 
                    else: pixel.set_rgb(0,0,0) 
                else: pixel.set_rgb(0,0,0)

def draw():
    global t, is_fetching
    workMat.clear()
    
    # 1. Background Fetch
    if (t % 500 == 0) and not is_fetching:
        is_fetching = True
        fetch_loop()

    # 2. Determine Stop
    stop_index = (t // SWITCH_INTERVAL) % len(MY_STOPS)
    active_stop = MY_STOPS[stop_index]
    
    # 2. Get Real-Time Info
    current_info = bus_cache.get(active_stop['id'], {'route': '??', 'minutes': 99})
    bearing = calculate_bearing(TREE_LAT, TREE_LON, active_stop['lat'], active_stop['lon'])

    # 3. Clear Pixels
    pix_list = pixels()
    for LED, pixel in enumerate(pix_list):
        pixel.set_rgb(0, 0, 0)

    # 4. Display Sequence
    cycle_t = t % SEQUENCE_LENGTH
    
    route = str(current_info['route'])
    minutes_str = str(current_info['minutes'])
    
    route_color = ROUTE_COLORS.get(route, DEFAULT_COLOR)
    time_color = (255, 255, 255) # White

    char_to_draw = " "
    active_color = (0,0,0)

    # Phase 1: Route (0-200)
    if cycle_t < 200:
        active_color = route_color
        char_to_draw = route[0] if len(route) > 0 else "?"
        if len(route) > 1 and cycle_t > 100:
            char_to_draw = route[1]
            
    # Phase 2: Time (200-400)
    else:
        active_color = time_color
        char_to_draw = minutes_str[0] if len(minutes_str) > 0 else "0"
        if len(minutes_str) > 1 and cycle_t > 300:
            char_to_draw = minutes_str[1]

    draw_text_angular(pix_list, char_to_draw, bearing, active_color)
    t = t + 1
