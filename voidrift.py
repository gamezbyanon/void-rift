"""
██╗   ██╗ ██████╗ ██╗██████╗     ██████╗ ██╗███████╗████████╗
██║   ██║██╔═══██╗██║██╔══██╗    ██╔══██╗██║██╔════╝╚══██╔══╝
██║   ██║██║   ██║██║██║  ██║    ██████╔╝██║█████╗     ██║
╚██╗ ██╔╝██║   ██║██║██║  ██║    ██╔══██╗██║██╔══╝     ██║
 ╚████╔╝ ╚██████╔╝██║██████╔╝    ██║  ██║██║██║        ██║
  ╚═══╝   ╚═════╝ ╚═╝╚═════╝     ╚═╝  ╚═╝╚═╝╚═╝        ╚═╝

coded by @non G00nz
"""

import pygame, math, random, sys, time, json
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict
import array as arr

# ═══════════════════════════════════════════════════════════════
#   CONSTANTS & CONFIGURATION
# ═══════════════════════════════════════════════════════════════
W, H     = 1280, 800
FPS      = 60
TITLE    = "VOID RIFT"

# World layers
LAYER_BG       = 0
LAYER_EFFECTS  = 1
LAYER_ENEMIES  = 2
LAYER_PLAYER   = 3
LAYER_BULLETS  = 4
LAYER_UI       = 5

# Difficulty scaling per sector
SECTOR_CONFIG = {
    1:  {"enemy_hp": 1.0,  "enemy_spd": 1.0,  "spawn_rate": 1.0,  "name": "OUTER RIM"},
    2:  {"enemy_hp": 1.4,  "enemy_spd": 1.1,  "spawn_rate": 1.2,  "name": "ASTEROID BELT"},
    3:  {"enemy_hp": 1.9,  "enemy_spd": 1.25, "spawn_rate": 1.5,  "name": "NEBULA CORE"},
    4:  {"enemy_hp": 2.6,  "enemy_spd": 1.4,  "spawn_rate": 1.8,  "name": "DARK MATTER ZONE"},
    5:  {"enemy_hp": 3.5,  "enemy_spd": 1.6,  "spawn_rate": 2.2,  "name": "VOID RIFT"},
}

# ═══════════════════════════════════════════════════════════════
#   COLORS
# ═══════════════════════════════════════════════════════════════
class C:
    BG          = (4,   6,   18)
    WHITE       = (255, 255, 255)
    BLACK       = (0,   0,   0)
    GRAY        = (100, 110, 130)
    DARK        = (15,  18,  40)
    PANEL       = (10,  12,  30)

    CYAN        = (0,   220, 255)
    CYAN_DIM    = (0,   120, 160)
    BLUE        = (30,  80,  255)
    BLUE_DARK   = (10,  30,  100)
    NEON_BLUE   = (60,  140, 255)

    GREEN       = (60,  255, 100)
    GREEN_DIM   = (20,  120, 50)
    NEON_GREEN  = (80,  255, 150)

    RED         = (255, 50,  60)
    RED_DARK    = (120, 20,  25)
    ORANGE      = (255, 130, 30)
    ORANGE_DIM  = (130, 65,  10)

    YELLOW      = (255, 230, 40)
    GOLD        = (255, 190, 20)
    GOLD_DIM    = (140, 100, 10)

    PURPLE      = (180, 60,  255)
    PURPLE_DIM  = (80,  20,  130)
    PINK        = (255, 80,  180)

    TEAL        = (0,   200, 180)
    LIME        = (150, 255, 50)

    # Ship colors by class
    SHIP_SCOUT    = (80,  200, 255)
    SHIP_FIGHTER  = (255, 100, 60)
    SHIP_PHANTOM  = (160, 80,  255)
    SHIP_TITAN    = (60,  255, 180)

    # Enemy colors
    ENE_DRONE     = (255, 80,  80)
    ENE_HUNTER    = (255, 150, 30)
    ENE_BOMBER    = (200, 50,  255)
    ENE_FORTRESS  = (80,  80,  255)
    ENE_LEECH     = (80,  255, 120)
    ENE_GHOST     = (200, 200, 255)
    ENE_BOSS      = (255, 50,  50)

# ═══════════════════════════════════════════════════════════════
#   GAME STATE ENUM
# ═══════════════════════════════════════════════════════════════
class GS(Enum):
    TITLE       = auto()
    SHIP_SELECT = auto()
    UPGRADE     = auto()
    SECTOR_MAP  = auto()
    GAMEPLAY    = auto()
    BOSS_INTRO  = auto()
    PAUSED      = auto()
    GAME_OVER   = auto()
    VICTORY     = auto()

# ═══════════════════════════════════════════════════════════════
#   PARTICLE SYSTEM  (pooled for performance)
# ═══════════════════════════════════════════════════════════════
class Particle:
    __slots__ = ('x','y','vx','vy','life','max_life','color','size',
                 'gravity','fade','trail','shape','spin','spin_v')
    def __init__(self):
        self.x = self.y = self.vx = self.vy = 0.0
        self.life = self.max_life = 1.0
        self.color = (255,255,255)
        self.size = 3.0
        self.gravity = 0.0
        self.fade = True
        self.trail = False
        self.shape = 'circle'   # circle | square | star
        self.spin = 0.0
        self.spin_v = 0.0

    def reset(self, x, y, vx, vy, life, color, size=3, gravity=0,
              fade=True, trail=False, shape='circle', spin_v=0):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.life = self.max_life = life
        self.color = color
        self.size = size
        self.gravity = gravity
        self.fade = fade
        self.trail = trail
        self.shape = shape
        self.spin = random.uniform(0, 360)
        self.spin_v = spin_v

POOL_SIZE = 3000

class ParticleSystem:
    def __init__(self):
        self.pool   = [Particle() for _ in range(POOL_SIZE)]
        self.active: List[Particle] = []
        self.free   = list(range(POOL_SIZE))
        self.trail_surf = pygame.Surface((W, H), pygame.SRCALPHA)

    def _get(self):
        if self.free:
            p = self.pool[self.free.pop()]
            self.active.append(p)
            return p
        return None

    def emit(self, x, y, color, count=10, speed=3, size=4,
             spread=360, gravity=0, life=1.0, fade=True,
             trail=False, shape='circle', spin_v=0, speed_min=None):
        for _ in range(count):
            p = self._get()
            if not p: break
            a = math.radians(random.uniform(0, spread))
            spd_min = speed_min if speed_min is not None else speed * 0.3
            spd = random.uniform(spd_min, speed)
            p.reset(x, y, math.cos(a)*spd, math.sin(a)*spd,
                    random.uniform(life*0.6, life),
                    color, random.uniform(size*0.5, size),
                    gravity, fade, trail, shape, spin_v)

    def emit_explosion(self, x, y, color, secondary=None, count=40):
        self.emit(x, y, color, count=count//2, speed=7, size=6,
                  gravity=0.04, life=1.2)
        self.emit(x, y, color, count=count//4, speed=3, size=3,
                  life=0.8, fade=True)
        if secondary:
            self.emit(x, y, secondary, count=count//4, speed=5,
                      size=4, life=1.0, shape='square')
        # Shockwave ring
        for i in range(16):
            a = math.radians(i * 22.5)
            p = self._get()
            if p:
                p.reset(x, y, math.cos(a)*9, math.sin(a)*9,
                        0.4, C.WHITE, 2, 0, True)

    def emit_thrust(self, x, y, angle, color, intensity=1.0):
        a = math.radians(angle + 180)
        spread = 30
        for _ in range(int(4 * intensity)):
            p = self._get()
            if not p: break
            da = math.radians(random.uniform(-spread/2, spread/2))
            spd = random.uniform(2, 5) * intensity
            p.reset(x + random.uniform(-3,3), y + random.uniform(-3,3),
                    math.cos(a+da)*spd, math.sin(a+da)*spd,
                    random.uniform(0.15, 0.4),
                    color, random.uniform(2, 5), 0, True)

    def emit_laser_impact(self, x, y, color):
        self.emit(x, y, color, count=12, speed=4, size=3, life=0.5)
        self.emit(x, y, C.WHITE, count=5, speed=6, size=2, life=0.3)

    def emit_pickup(self, x, y, color):
        for i in range(20):
            a = math.radians(i * 18)
            p = self._get()
            if p:
                p.reset(x, y, math.cos(a)*3, math.sin(a)*3,
                        0.8, color, 4, -0.05, True, False, 'star')

    def emit_warp(self, x, y):
        for _ in range(30):
            a = math.radians(random.uniform(0, 360))
            r = random.uniform(0, 80)
            px = x + math.cos(a) * r
            py = y + math.sin(a) * r
            p = self._get()
            if p:
                p.reset(px, py, math.cos(a)*-2, math.sin(a)*-2,
                        0.6, C.CYAN, 3, 0, True)

    def update(self):
        dt = 1/FPS
        done = []
        for p in self.active:
            p.x += p.vx
            p.y += p.vy
            p.vy += p.gravity
            p.vx *= 0.98
            p.life -= dt / p.max_life * 1.0
            p.spin += p.spin_v
            if p.life <= 0:
                done.append(p)
        for p in done:
            self.active.remove(p)
            self.free.append(self.pool.index(p))

    def draw(self, surf):
        for p in self.active:
            alpha_f = max(0.0, p.life) if p.fade else 1.0
            alpha = int(255 * alpha_f)
            r = max(1, int(p.size * alpha_f))
            col = tuple(min(255, int(c)) for c in p.color[:3])

            if p.shape == 'circle':
                pygame.draw.circle(surf, col, (int(p.x), int(p.y)), r)
            elif p.shape == 'square':
                rect = pygame.Rect(int(p.x)-r, int(p.y)-r, r*2, r*2)
                pygame.draw.rect(surf, col, rect)
            elif p.shape == 'star':
                cx, cy = int(p.x), int(p.y)
                pts = []
                for i in range(5):
                    a_out = math.radians(p.spin + i*72)
                    a_in  = math.radians(p.spin + i*72 + 36)
                    pts.append((cx+int(math.cos(a_out)*r*1.5),
                                cy+int(math.sin(a_out)*r*1.5)))
                    pts.append((cx+int(math.cos(a_in)*r*0.6),
                                cy+int(math.sin(a_in)*r*0.6)))
                if len(pts) >= 3:
                    pygame.draw.polygon(surf, col, pts)

# ═══════════════════════════════════════════════════════════════
#   SCROLLING STAR FIELD  (multi-layer parallax)
# ═══════════════════════════════════════════════════════════════
class StarField:
    def __init__(self):
        self.layers = []
        # 3 depth layers
        for depth, count, speed_range, size_range in [
            (0, 200, (0.2, 0.6), (1, 1)),
            (1, 100, (0.6, 1.2), (1, 2)),
            (2,  50, (1.2, 2.0), (2, 3)),
        ]:
            stars = []
            for _ in range(count):
                stars.append({
                    'x': random.uniform(0, W),
                    'y': random.uniform(0, H),
                    'speed': random.uniform(*speed_range),
                    'size':  random.randint(*size_range),
                    'brightness': random.uniform(0.4, 1.0),
                    'twinkle_phase': random.uniform(0, math.pi*2),
                    'twinkle_speed': random.uniform(1, 4),
                    'color_shift': random.choice([
                        (255,255,255), (200,220,255), (255,220,200), (200,255,240)
                    ])
                })
            self.layers.append(stars)

        # Nebula clouds
        self.nebulae = []
        for _ in range(5):
            self.nebulae.append({
                'x': random.uniform(-200, W+200),
                'y': random.uniform(-200, H+200),
                'radius': random.randint(120, 280),
                'color': random.choice([
                    (20,5,60,40), (5,20,50,35), (30,10,50,30),
                    (5,40,60,25), (40,5,40,30)
                ]),
                'speed': random.uniform(0.05, 0.2),
            })

        self.t = 0.0

    def update(self, scroll_speed=1.0):
        self.t += 1/FPS
        for layer in self.layers:
            for s in layer:
                s['y'] += s['speed'] * scroll_speed
                if s['y'] > H + 5:
                    s['y'] = -5
                    s['x'] = random.uniform(0, W)
        for n in self.nebulae:
            n['y'] += n['speed'] * scroll_speed
            if n['y'] > H + 300:
                n['y'] = -300
                n['x'] = random.uniform(-200, W+200)

    def draw(self, surf):
        # Nebulae
        for n in self.nebulae:
            ns = pygame.Surface((n['radius']*2, n['radius']*2), pygame.SRCALPHA)
            r, g, b, a = n['color']
            pygame.draw.circle(ns, (r,g,b,a), (n['radius'], n['radius']), n['radius'])
            surf.blit(ns, (int(n['x']-n['radius']), int(n['y']-n['radius'])))

        # Stars
        for layer in self.layers:
            for s in layer:
                twinkle = 0.7 + 0.3 * math.sin(self.t * s['twinkle_speed'] + s['twinkle_phase'])
                b = int(255 * s['brightness'] * twinkle)
                cr, cg, cb = s['color_shift']
                col = (int(cr*b/255), int(cg*b/255), int(cb*b/255))
                if s['size'] == 1:
                    surf.set_at((int(s['x']), int(s['y'])), col)
                else:
                    pygame.draw.circle(surf, col, (int(s['x']), int(s['y'])), s['size'])

        # Occasional shooting star
        if random.random() < 0.003:
            sx = random.randint(0, W)
            sy = random.randint(0, H//2)
            for i in range(8):
                px = sx - i*12
                py = sy + i*4
                if 0 <= px < W and 0 <= py < H:
                    surf.set_at((px, py), (255, 255, 200))

# ═══════════════════════════════════════════════════════════════
#   WEAPONS SYSTEM
# ═══════════════════════════════════════════════════════════════
class WeaponType(Enum):
    LASER       = "LASER"
    SPREAD      = "SPREAD SHOT"
    PLASMA      = "PLASMA CANNON"
    RAILGUN     = "RAILGUN"
    HOMING      = "HOMING MISSILES"
    VORTEX      = "VORTEX BEAM"
    ION_BURST   = "ION BURST"
    CHAIN       = "CHAIN LIGHTNING"

WEAPON_DATA = {
    WeaponType.LASER:     {"dmg":8,   "spd":16, "cd":0.12, "color":C.CYAN,   "size":4,  "pierce":False, "desc":"Rapid-fire precision beam"},
    WeaponType.SPREAD:    {"dmg":6,   "spd":12, "cd":0.20, "color":C.YELLOW, "size":5,  "pierce":False, "desc":"5-way spread burst"},
    WeaponType.PLASMA:    {"dmg":25,  "spd":9,  "cd":0.55, "color":C.PURPLE, "size":10, "pierce":False, "desc":"Heavy plasma ball"},
    WeaponType.RAILGUN:   {"dmg":60,  "spd":22, "cd":1.20, "color":C.WHITE,  "size":3,  "pierce":True,  "desc":"Piercing hypersonic slug"},
    WeaponType.HOMING:    {"dmg":20,  "spd":7,  "cd":0.60, "color":C.ORANGE, "size":6,  "pierce":False, "desc":"Lock-on heat-seeker"},
    WeaponType.VORTEX:    {"dmg":4,   "spd":10, "cd":0.06, "color":C.TEAL,   "size":7,  "pierce":True,  "desc":"Continuous spinning vortex"},
    WeaponType.ION_BURST: {"dmg":15,  "spd":14, "cd":0.35, "color":C.LIME,   "size":8,  "pierce":False, "desc":"EMP shockwave pulse"},
    WeaponType.CHAIN:     {"dmg":12,  "spd":11, "cd":0.30, "color":C.PINK,   "size":5,  "pierce":False, "desc":"Arcs between enemies"},
}

@dataclass
class Bullet:
    x: float; y: float
    vx: float; vy: float
    dmg: int; color: tuple
    size: int; pierce: bool
    owner: str = "player"  # player | enemy
    homing_target: Optional[object] = None
    homing_strength: float = 0.08
    chain_count: int = 0
    alive: bool = True
    age: float = 0.0
    weapon_type: Optional[WeaponType] = None
    trail: List = field(default_factory=list)

    def update(self, enemies=None):
        self.age += 1/FPS
        if self.age > 4.0:
            self.alive = False
            return

        # Homing
        if self.homing_target and enemies:
            if self.homing_target in enemies and self.homing_target.alive:
                tx = self.homing_target.x - self.x
                ty = self.homing_target.y - self.y
                dist = math.hypot(tx, ty)
                if dist > 5:
                    nx, ny = tx/dist, ty/dist
                    spd = math.hypot(self.vx, self.vy)
                    self.vx += nx * self.homing_strength * spd
                    self.vy += ny * self.homing_strength * spd
                    spd2 = math.hypot(self.vx, self.vy)
                    if spd2 > 0:
                        self.vx = self.vx/spd2 * spd
                        self.vy = self.vy/spd2 * spd
            else:
                self.homing_target = None

        # Vortex spin
        if self.weapon_type == WeaponType.VORTEX:
            angle = math.atan2(self.vy, self.vx)
            angle += 0.05
            spd = math.hypot(self.vx, self.vy)
            self.vx = math.cos(angle) * spd
            self.vy = math.sin(angle) * spd

        # Trail
        self.trail.append((self.x, self.y))
        if len(self.trail) > 8:
            self.trail.pop(0)

        self.x += self.vx
        self.y += self.vy

        if self.owner == "player":
            if self.y < -50 or self.x < -50 or self.x > W+50:
                self.alive = False
        else:
            if self.y > H+50 or self.x < -50 or self.x > W+50 or self.y < -50:
                self.alive = False

    def draw(self, surf, particles):
        if not self.alive:
            return
        # Trail
        for i, (tx, ty) in enumerate(self.trail):
            alpha_f = i / len(self.trail)
            tr = max(1, int(self.size * alpha_f * 0.6))
            col = tuple(int(c*alpha_f*0.5) for c in self.color)
            pygame.draw.circle(surf, col, (int(tx), int(ty)), tr)

        # Glow
        gr = self.size + 4
        gsurf = pygame.Surface((gr*2+2, gr*2+2), pygame.SRCALPHA)
        pygame.draw.circle(gsurf, (*self.color, 60), (gr+1, gr+1), gr)
        surf.blit(gsurf, (int(self.x)-gr-1, int(self.y)-gr-1))

        # Core
        pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), self.size)
        pygame.draw.circle(surf, C.WHITE,    (int(self.x), int(self.y)), max(1, self.size-2))

        # Homing swirl
        if self.homing_target:
            a = self.age * 6
            for i in range(3):
                da = a + i * 2.09
                px = self.x + math.cos(da) * self.size * 2
                py = self.y + math.sin(da) * self.size * 2
                pygame.draw.circle(surf, C.ORANGE, (int(px), int(py)), 2)

# ═══════════════════════════════════════════════════════════════
#   SHIP CLASSES
# ═══════════════════════════════════════════════════════════════
@dataclass
class ShipClass:
    name: str; color: tuple; desc: str
    hp: int; shield: int; speed: float
    fire_rate: float   # multiplier
    weapons: List[WeaponType]
    ability_name: str; ability_desc: str
    ability_cd: float
    special_shape: str  # affects draw

SHIP_CLASSES = [
    ShipClass("SCOUT",   C.SHIP_SCOUT,   "Fast interceptor. Low health, high speed.",
              80,  40,  5.5, 1.4,
              [WeaponType.LASER, WeaponType.SPREAD],
              "AFTERBURNER", "Massive speed boost + invincibility (3s)", 8.0,
              "scout"),
    ShipClass("FIGHTER", C.SHIP_FIGHTER, "Balanced warship. Jack of all trades.",
              140, 60,  4.0, 1.0,
              [WeaponType.LASER, WeaponType.PLASMA, WeaponType.HOMING],
              "MISSILE BARRAGE", "Fire 12 homing missiles in all directions", 10.0,
              "fighter"),
    ShipClass("PHANTOM", C.SHIP_PHANTOM, "Stealth assassin. Phase through enemies.",
              100, 80,  4.5, 1.2,
              [WeaponType.RAILGUN, WeaponType.CHAIN, WeaponType.VORTEX],
              "PHASE SHIFT", "Brief invincibility + massive damage burst", 12.0,
              "phantom"),
    ShipClass("TITAN",   C.SHIP_TITAN,   "Heavy destroyer. Slow but devastating.",
              220, 120, 2.8, 0.7,
              [WeaponType.PLASMA, WeaponType.ION_BURST, WeaponType.RAILGUN],
              "OMEGA STRIKE", "Massive AOE explosion destroying all weak enemies", 15.0,
              "titan"),
]

class Player:
    def __init__(self, ship_class: ShipClass):
        self.cls = ship_class
        self.x = W / 2
        self.y = H - 120
        self.angle = -90.0    # degrees, -90 = pointing up
        self.speed = ship_class.speed
        self.vx = 0.0; self.vy = 0.0

        self.max_hp      = ship_class.hp
        self.hp          = ship_class.hp
        self.max_shield  = ship_class.shield
        self.shield      = ship_class.shield
        self.shield_regen= 8.0   # per second
        self.shield_delay= 3.0   # seconds after hit before regen

        self.weapons     = list(ship_class.weapons)
        self.active_weapon_idx = 0
        self.weapon_cd   = 0.0
        self.fire_rate_mult = ship_class.fire_rate

        self.ability_cd    = 0.0
        self.ability_active= False
        self.ability_timer = 0.0

        self.invincible    = False
        self.invincible_t  = 0.0
        self.hit_flash     = 0.0

        self.score         = 0
        self.credits       = 100
        self.combo         = 0
        self.combo_timer   = 0.0
        self.combo_mult    = 1.0
        self.max_combo     = 0
        self.kills         = 0
        self.shots_fired   = 0
        self.shots_hit     = 0

        self.upgrades: Dict[str, int] = {
            "damage":   0,  # 0-5
            "fire_rate":0,
            "shield":   0,
            "speed":    0,
            "hp":       0,
            "special":  0,  # weapon-specific enhancement
        }

        self.shield_hit_timer = 0.0
        self.thrust = False
        self.t = 0.0

        # Afterburner (scout)
        self.afterburner_active = False
        # Phase shift (phantom)
        self.phase_active = False
        # Collected powerups
        self.active_powerups: List[dict] = []

        # Wing engine positions (for thrust particles)
        self.engine_offsets = self._get_engine_offsets()

    def _get_engine_offsets(self):
        s = self.cls.special_shape
        if s == "scout":   return [(-12, 15), (12, 15)]
        if s == "fighter": return [(-18, 20), (18, 20), (0, 22)]
        if s == "phantom": return [(-10, 18), (10, 18)]
        if s == "titan":   return [(-25, 25), (25, 25), (0, 28)]
        return [(0, 15)]

    @property
    def active_weapon(self):
        return self.weapons[self.active_weapon_idx % len(self.weapons)]

    def switch_weapon(self):
        self.active_weapon_idx = (self.active_weapon_idx + 1) % len(self.weapons)
        self.weapon_cd = 0.0

    def update(self, keys, dt, bounds=(0,0,W,H)):
        self.t += dt

        # Movement
        dx = dy = 0
        spd = self.speed * (1 + self.upgrades["speed"] * 0.15)
        if self.afterburner_active:
            spd *= 2.2

        if keys[pygame.K_w] or keys[pygame.K_UP]:    dy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:  dy += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:  dx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx += 1

        self.thrust = (dx != 0 or dy != 0)

        if dx and dy:
            dx *= 0.7071; dy *= 0.7071

        # Smooth velocity
        target_vx = dx * spd * 60
        target_vy = dy * spd * 60
        accel = 0.2
        self.vx += (target_vx - self.vx) * accel
        self.vy += (target_vy - self.vy) * accel

        self.x = max(30, min(W-30, self.x + self.vx * dt))
        self.y = max(30, min(H-30, self.y + self.vy * dt))

        # Tilt based on horizontal movement
        tilt = -self.vx * 0.02
        self.angle = -90 + tilt

        # Shield regen
        self.shield_hit_timer = max(0, self.shield_hit_timer - dt)
        if self.shield_hit_timer <= 0 and self.shield < self.max_shield:
            regen = self.shield_regen * (1 + self.upgrades["shield"] * 0.3)
            self.shield = min(self.max_shield, self.shield + regen * dt)

        # Cooldowns
        self.weapon_cd    = max(0, self.weapon_cd - dt)
        self.ability_cd   = max(0, self.ability_cd - dt)
        self.invincible_t = max(0, self.invincible_t - dt)
        self.hit_flash    = max(0, self.hit_flash - dt * 3)
        if self.invincible_t <= 0:
            self.invincible = False

        # Combo decay
        self.combo_timer = max(0, self.combo_timer - dt)
        if self.combo_timer <= 0 and self.combo > 0:
            self.combo = 0
            self.combo_mult = 1.0

        # Combo multiplier
        if   self.combo >= 50: self.combo_mult = 6.0
        elif self.combo >= 30: self.combo_mult = 4.0
        elif self.combo >= 15: self.combo_mult = 3.0
        elif self.combo >= 8:  self.combo_mult = 2.0
        elif self.combo >= 4:  self.combo_mult = 1.5
        else:                  self.combo_mult = 1.0

        # Ability timer
        if self.ability_active:
            self.ability_timer = max(0, self.ability_timer - dt)
            if self.ability_timer <= 0:
                self.ability_active = False
                self.afterburner_active = False
                self.phase_active = False
                self.invincible = False

        # Active powerups
        for pw in self.active_powerups[:]:
            pw['timer'] -= dt
            if pw['timer'] <= 0:
                self.active_powerups.remove(pw)

    def take_damage(self, amount):
        if self.invincible:
            return 0
        if self.phase_active:
            return 0

        actual = amount
        if self.shield > 0:
            absorbed = min(self.shield, actual)
            self.shield -= absorbed
            actual -= absorbed
            self.shield_hit_timer = self.shield_delay

        if actual > 0:
            self.hp -= actual
            self.hit_flash = 1.0

        return amount

    def add_score(self, points, x=None, y=None):
        scored = int(points * self.combo_mult)
        self.score += scored
        self.combo += 1
        self.combo_timer = 3.5
        if self.combo > self.max_combo:
            self.max_combo = self.combo
        return scored

    def fire(self, bullets: List[Bullet], enemies, particles: ParticleSystem):
        wdata = WEAPON_DATA[self.active_weapon]
        cd = wdata["cd"] / (self.fire_rate_mult * (1 + self.upgrades["fire_rate"]*0.2))
        if self.weapon_cd > 0:
            return

        self.weapon_cd = cd
        self.shots_fired += 1
        dmg = int(wdata["dmg"] * (1 + self.upgrades["damage"] * 0.25))
        col = wdata["color"]
        spd = wdata["spd"]
        sz  = wdata["size"]
        pierce = wdata["pierce"]
        wt = self.active_weapon

        fx, fy = self.x, self.y - 20

        if wt == WeaponType.LASER:
            bullets.append(Bullet(fx, fy, 0, -spd, dmg, col, sz, pierce,
                                  weapon_type=wt))

        elif wt == WeaponType.SPREAD:
            for angle_off in [-30, -15, 0, 15, 30]:
                a = math.radians(-90 + angle_off)
                bullets.append(Bullet(fx, fy, math.cos(a)*spd, math.sin(a)*spd,
                                      dmg, col, sz, False, weapon_type=wt))

        elif wt == WeaponType.PLASMA:
            bullets.append(Bullet(fx, fy, 0, -spd, dmg, col, sz, pierce,
                                  weapon_type=wt))
            particles.emit(fx, fy-10, col, count=6, speed=2, size=6)

        elif wt == WeaponType.RAILGUN:
            # Instant-travel beam - pierce all
            bullets.append(Bullet(fx, fy, 0, -spd*2, dmg, col, sz, True,
                                  weapon_type=wt))
            # Visual beam flash
            particles.emit(fx, fy, C.WHITE, count=15, speed=3, size=3, life=0.2)

        elif wt == WeaponType.HOMING:
            # Find up to 3 closest enemies
            targets = sorted(enemies, key=lambda e: math.hypot(e.x-fx, e.y-fy))[:3]
            for i, t in enumerate(targets):
                a = math.radians(-90 + i*30 - 30)
                b = Bullet(fx, fy, math.cos(a)*spd, math.sin(a)*spd,
                           dmg, col, sz, False, weapon_type=wt)
                b.homing_target = t
                bullets.append(b)

        elif wt == WeaponType.VORTEX:
            base_angle = math.radians(self.t * 200 - 90)
            for i in range(3):
                a = base_angle + math.radians(i * 120)
                bullets.append(Bullet(fx, fy, math.cos(a)*spd, math.sin(a)*spd,
                                      dmg, col, sz, True, weapon_type=wt))

        elif wt == WeaponType.ION_BURST:
            for i in range(8):
                a = math.radians(i * 45 - 90)
                bullets.append(Bullet(fx, fy, math.cos(a)*spd, math.sin(a)*spd,
                                      dmg, col, sz, False, weapon_type=wt))
            particles.emit(fx, fy, col, count=20, speed=5, size=8, life=0.4)

        elif wt == WeaponType.CHAIN:
            # Fires toward nearest enemy
            if enemies:
                target = min(enemies, key=lambda e: math.hypot(e.x-fx, e.y-fy))
                tx = target.x - fx; ty = target.y - fy
                dist = math.hypot(tx, ty)
                if dist > 0:
                    nx, ny = tx/dist, ty/dist
                    b = Bullet(fx, fy, nx*spd, ny*spd, dmg, col, sz, False,
                               weapon_type=wt)
                    b.chain_count = 3
                    bullets.append(b)
            else:
                bullets.append(Bullet(fx, fy, 0, -spd, dmg, col, sz, False,
                                      weapon_type=wt))

    def use_ability(self, bullets, enemies, particles):
        if self.ability_cd > 0:
            return
        self.ability_cd = self.cls.ability_cd
        self.ability_active = True

        if self.cls.special_shape == "scout":  # Afterburner
            self.afterburner_active = True
            self.invincible = True
            self.invincible_t = 3.0
            self.ability_timer = 3.0
            particles.emit(self.x, self.y, C.CYAN, count=30, speed=8, life=0.8)

        elif self.cls.special_shape == "fighter":  # Missile Barrage
            self.ability_timer = 0.1
            for i in range(12):
                a = math.radians(i * 30)
                target = None
                if enemies:
                    target = random.choice(enemies)
                wdata = WEAPON_DATA[WeaponType.HOMING]
                b = Bullet(self.x, self.y,
                           math.cos(a)*wdata["spd"], math.sin(a)*wdata["spd"],
                           wdata["dmg"]*2, C.ORANGE, 8, False,
                           weapon_type=WeaponType.HOMING)
                b.homing_target = target
                bullets.append(b)
            particles.emit_explosion(self.x, self.y, C.ORANGE, C.YELLOW, 30)

        elif self.cls.special_shape == "phantom":  # Phase Shift
            self.phase_active = True
            self.invincible = True
            self.invincible_t = 2.0
            self.ability_timer = 2.0
            particles.emit(self.x, self.y, C.PURPLE, count=40, speed=6, life=1.0,
                           shape='star')
            # Damage pulse
            for e in enemies[:]:
                d = math.hypot(e.x - self.x, e.y - self.y)
                if d < 200:
                    e.take_damage(80)
                    particles.emit_explosion(e.x, e.y, C.PURPLE)

        elif self.cls.special_shape == "titan":  # Omega Strike
            self.ability_timer = 0.5
            # Screen-wide shockwave
            for e in enemies[:]:
                if e.max_hp <= 150:
                    e.hp = 0
                    e.alive = False
                else:
                    e.take_damage(int(e.max_hp * 0.6))
                particles.emit_explosion(e.x, e.y, C.TEAL, C.WHITE, 25)
            particles.emit(self.x, self.y, C.TEAL, count=80, speed=15, life=1.5,
                           spread=360)

    def draw(self, surf, particles, dt):
        cx, cy = int(self.x), int(self.y)
        col = self.cls.color
        t = self.t

        # Invincibility flicker
        if self.invincible and int(t * 15) % 2 == 0:
            col = C.WHITE

        # Hit flash
        if self.hit_flash > 0:
            intensity = self.hit_flash
            col = (int(col[0] + (255-col[0])*intensity),
                   int(col[1] * (1-intensity*0.5)),
                   int(col[2] * (1-intensity*0.5)))
            col = tuple(min(255, max(0, c)) for c in col)

        # Phase shift visual
        if self.phase_active:
            for i in range(3):
                off_x = int(math.sin(t*8+i*2.1)*15)
                off_y = int(math.cos(t*8+i*2.1)*15)
                self._draw_ship_shape(surf, cx+off_x, cy+off_y,
                                      (*C.PURPLE, 80), self.cls.special_shape)

        self._draw_ship_shape(surf, cx, cy, col, self.cls.special_shape)

        # Shield bubble
        if self.shield > 0:
            shield_f = self.shield / self.max_shield
            r = 36
            ss = pygame.Surface((r*2+4, r*2+4), pygame.SRCALPHA)
            a = int(60 * shield_f)
            if self.shield_hit_timer > (self.shield_delay - 0.3):
                a = min(180, a + 100)  # flash on hit
            pygame.draw.circle(ss, (*C.CYAN_DIM, a), (r+2, r+2), r, 3)
            pygame.draw.circle(ss, (*C.CYAN, int(a*0.4)), (r+2, r+2), r)
            surf.blit(ss, (cx-r-2, cy-r-2))

        # Engine thrust particles
        if self.thrust or self.afterburner_active:
            a_rad = math.radians(self.angle + 90)
            intensity = 2.0 if self.afterburner_active else 1.0
            thrust_col = C.CYAN if self.afterburner_active else (100, 180, 255)
            for ox, oy in self.engine_offsets:
                # Rotate offset by ship angle
                rot = math.radians(self.angle + 90)
                rx = ox*math.cos(rot) - oy*math.sin(rot)
                ry = ox*math.sin(rot) + oy*math.cos(rot)
                particles.emit_thrust(cx+rx, cy+ry, self.angle, thrust_col, intensity)

        # Afterburner trail
        if self.afterburner_active:
            particles.emit(cx, cy, C.CYAN, count=3, speed=3, size=8,
                           life=0.4, fade=True, spread=360)

    def _draw_ship_shape(self, surf, cx, cy, col, shape):
        t = self.t
        # Gentle bob
        cy_draw = cy + int(math.sin(t * 2) * 1.5)

        if shape == "scout":
            # Sleek, narrow fighter
            pts = [
                (cx, cy_draw - 28),
                (cx - 18, cy_draw + 18),
                (cx - 8, cy_draw + 10),
                (cx,     cy_draw + 4),
                (cx + 8, cy_draw + 10),
                (cx + 18, cy_draw + 18),
            ]
            pygame.draw.polygon(surf, col, pts)
            pygame.draw.polygon(surf, C.WHITE, pts, 1)
            # Cockpit
            pygame.draw.ellipse(surf, C.CYAN, (cx-6, cy_draw-18, 12, 16))
            # Wing lights
            pygame.draw.circle(surf, C.YELLOW, (cx-18, cy_draw+16), 3)
            pygame.draw.circle(surf, C.GREEN, (cx+18, cy_draw+16), 3)

        elif shape == "fighter":
            # Broader warship
            pts = [
                (cx,     cy_draw - 30),
                (cx - 8, cy_draw - 10),
                (cx - 28, cy_draw + 15),
                (cx - 20, cy_draw + 22),
                (cx - 10, cy_draw + 15),
                (cx,      cy_draw + 8),
                (cx + 10, cy_draw + 15),
                (cx + 20, cy_draw + 22),
                (cx + 28, cy_draw + 15),
                (cx + 8,  cy_draw - 10),
            ]
            pygame.draw.polygon(surf, col, pts)
            pygame.draw.polygon(surf, C.WHITE, pts, 1)
            # Cockpit
            pygame.draw.ellipse(surf, (150, 200, 255), (cx-7, cy_draw-22, 14, 20))
            # Cannons
            pygame.draw.rect(surf, C.GRAY, (cx-26, cy_draw+5, 5, 14))
            pygame.draw.rect(surf, C.GRAY, (cx+21, cy_draw+5, 5, 14))
            pygame.draw.circle(surf, C.RED, (cx-24, cy_draw-2), 3)
            pygame.draw.circle(surf, C.RED, (cx+24, cy_draw-2), 3)

        elif shape == "phantom":
            # Angular stealth
            pts = [
                (cx,     cy_draw - 32),
                (cx - 6, cy_draw - 8),
                (cx - 30, cy_draw + 20),
                (cx - 14, cy_draw + 12),
                (cx,      cy_draw + 2),
                (cx + 14, cy_draw + 12),
                (cx + 30, cy_draw + 20),
                (cx + 6,  cy_draw - 8),
            ]
            pygame.draw.polygon(surf, col, pts)
            pygame.draw.polygon(surf, C.WHITE, pts, 1)
            # Core glow
            gs = pygame.Surface((20,20), pygame.SRCALPHA)
            r = int(6 + 2 * math.sin(t * 4))
            pygame.draw.circle(gs, (*C.PURPLE, 180), (10,10), r)
            surf.blit(gs, (cx-10, cy_draw-10))
            # Cockpit
            pygame.draw.ellipse(surf, (200, 150, 255), (cx-5, cy_draw-24, 10, 18))

        elif shape == "titan":
            # Heavy, squat destroyer
            pts = [
                (cx,     cy_draw - 26),
                (cx - 12, cy_draw - 8),
                (cx - 36, cy_draw + 10),
                (cx - 36, cy_draw + 26),
                (cx - 20, cy_draw + 28),
                (cx,      cy_draw + 20),
                (cx + 20, cy_draw + 28),
                (cx + 36, cy_draw + 26),
                (cx + 36, cy_draw + 10),
                (cx + 12, cy_draw - 8),
            ]
            pygame.draw.polygon(surf, col, pts)
            pygame.draw.polygon(surf, C.WHITE, pts, 1)
            # Armor plates
            pygame.draw.rect(surf, tuple(int(c*0.6) for c in col),
                             (cx-10, cy_draw-20, 20, 16))
            # Cockpit
            pygame.draw.ellipse(surf, C.TEAL, (cx-8, cy_draw-20, 16, 20))
            # Dual cannons
            pygame.draw.rect(surf, C.GRAY, (cx-22, cy_draw-8, 6, 20))
            pygame.draw.rect(surf, C.GRAY, (cx+16, cy_draw-8, 6, 20))

# ═══════════════════════════════════════════════════════════════
#   ENEMY TYPES
# ═══════════════════════════════════════════════════════════════
class EnemyType(Enum):
    DRONE     = "DRONE"
    HUNTER    = "HUNTER"
    BOMBER    = "BOMBER"
    FORTRESS  = "FORTRESS"
    LEECH     = "LEECH"
    GHOST     = "GHOST"
    BOSS_1    = "WARLORD"
    BOSS_2    = "VOID TITAN"
    BOSS_3    = "RIFT DESTROYER"

ENEMY_DATA = {
    EnemyType.DRONE:    {"hp":30,   "spd":2.5, "dmg":8,  "score":100, "col":C.ENE_DRONE,   "sz":14, "fire_cd":1.8, "credits":5},
    EnemyType.HUNTER:   {"hp":60,   "spd":3.5, "dmg":12, "score":250, "col":C.ENE_HUNTER,  "sz":16, "fire_cd":1.2, "credits":10},
    EnemyType.BOMBER:   {"hp":100,  "spd":1.8, "dmg":25, "score":400, "col":C.ENE_BOMBER,  "sz":22, "fire_cd":2.5, "credits":15},
    EnemyType.FORTRESS: {"hp":200,  "spd":1.0, "dmg":15, "score":600, "col":C.ENE_FORTRESS,"sz":28, "fire_cd":0.8, "credits":25},
    EnemyType.LEECH:    {"hp":45,   "spd":4.0, "dmg":6,  "score":150, "col":C.ENE_LEECH,   "sz":12, "fire_cd":3.0, "credits":8},
    EnemyType.GHOST:    {"hp":70,   "spd":2.0, "dmg":18, "score":350, "col":C.ENE_GHOST,   "sz":18, "fire_cd":1.5, "credits":12},
}

class Enemy:
    def __init__(self, etype: EnemyType, x: float, y: float,
                 hp_mult=1.0, spd_mult=1.0):
        self.etype = etype
        self.x = float(x)
        self.y = float(y)

        d = ENEMY_DATA.get(etype, ENEMY_DATA[EnemyType.DRONE])
        self.max_hp   = int(d["hp"] * hp_mult)
        self.hp       = self.max_hp
        self.speed    = d["spd"] * spd_mult
        self.dmg      = d["dmg"]
        self.score    = d["score"]
        self.color    = d["col"]
        self.size     = d["sz"]
        self.fire_cd  = d["fire_cd"]
        self.credits  = d["credits"]
        self.fire_timer = random.uniform(0, self.fire_cd)
        self.alive    = True

        self.vx = 0.0; self.vy = 0.0
        self.angle  = 90.0   # facing down initially
        self.t      = random.uniform(0, math.pi*2)  # phase offset
        self.pattern_t = 0.0
        self.hit_flash = 0.0
        self.is_boss = etype in (EnemyType.BOSS_1, EnemyType.BOSS_2, EnemyType.BOSS_3)

        # Movement pattern
        self.pattern = self._assign_pattern()
        self.pattern_origin_x = x
        self.entry_done = False
        self.entry_y_target = random.uniform(80, 250) if not self.is_boss else H/3

        # Chain lightning chain list
        self.chained = False

    def _assign_pattern(self):
        if self.etype == EnemyType.DRONE:
            return random.choice(["straight", "zigzag", "swoop"])
        if self.etype == EnemyType.HUNTER:
            return "chase"
        if self.etype == EnemyType.BOMBER:
            return "slow_dive"
        if self.etype == EnemyType.FORTRESS:
            return random.choice(["patrol", "strafe"])
        if self.etype == EnemyType.LEECH:
            return "circle_player"
        if self.etype == EnemyType.GHOST:
            return "phase_move"
        return "straight"

    def take_damage(self, amount):
        self.hp -= amount
        self.hit_flash = 1.0
        if self.hp <= 0:
            self.alive = False

    def update(self, dt, player_x, player_y, bullets: List[Bullet],
               particles: ParticleSystem):
        self.t += dt
        self.pattern_t += dt
        self.hit_flash = max(0, self.hit_flash - dt * 4)

        if self.hp <= 0:
            self.alive = False
            return

        # Entry animation
        if not self.entry_done:
            self.y += self.speed * 2 * dt * 60 * 0.016
            if self.y >= self.entry_y_target:
                self.entry_done = True
            return

        # Movement patterns
        p = self.pattern

        if p == "straight":
            self.y += self.speed * dt * 60 * 0.016
            self.x += math.sin(self.t * 1.5) * 0.5

        elif p == "zigzag":
            self.y += self.speed * 0.8 * dt * 60 * 0.016
            self.x += math.sin(self.t * 3) * self.speed * 1.5

        elif p == "swoop":
            self.y += self.speed * 0.6 * dt * 60 * 0.016
            self.x = self.pattern_origin_x + math.sin(self.pattern_t * 2) * 120

        elif p == "chase":
            dx = player_x - self.x; dy = player_y - self.y
            dist = math.hypot(dx, dy)
            if dist > 0:
                nx, ny = dx/dist, dy/dist
                target_dist = 200
                if dist > target_dist:
                    self.x += nx * self.speed * dt * 60 * 0.016
                    self.y += ny * self.speed * dt * 60 * 0.016
                else:
                    # Orbit
                    perp_x, perp_y = -ny, nx
                    self.x += perp_x * self.speed * 0.8 * dt * 60 * 0.016
                    self.y += perp_y * self.speed * 0.8 * dt * 60 * 0.016

        elif p == "slow_dive":
            self.y += self.speed * 0.5 * dt * 60 * 0.016
            if self.y > H * 0.5:
                # Dive toward player
                dx = player_x - self.x
                self.x += dx * 0.02

        elif p == "patrol":
            self.x = self.pattern_origin_x + math.sin(self.pattern_t * 0.8) * 200
            self.y += 0.1

        elif p == "strafe":
            self.x += math.cos(self.t * 2) * self.speed
            self.y = max(80, min(200, self.y + math.sin(self.t)*0.5))

        elif p == "circle_player":
            angle = self.t * 2
            radius = 180
            target_x = player_x + math.cos(angle) * radius
            target_y = player_y + math.sin(angle) * radius
            self.x += (target_x - self.x) * 0.06
            self.y += (target_y - self.y) * 0.06

        elif p == "phase_move":
            # Teleport-like movement
            self.x += math.sin(self.t * 4) * self.speed * 1.2
            self.y += math.cos(self.t * 2) * self.speed * 0.5

        # Clamp to screen
        self.x = max(20, min(W-20, self.x))
        if not self.is_boss:
            if self.y > H + 60:
                self.alive = False
                return

        # Aim angle toward player
        dx = player_x - self.x; dy = player_y - self.y
        self.angle = math.degrees(math.atan2(dy, dx))

        # Firing
        self.fire_timer -= dt
        if self.fire_timer <= 0:
            self.fire_timer = self.fire_cd * random.uniform(0.8, 1.2)
            self._fire(bullets, player_x, player_y)

    def _fire(self, bullets: List[Bullet], px, py):
        dx = px - self.x; dy = py - self.y
        dist = math.hypot(dx, dy)
        if dist == 0: return
        nx, ny = dx/dist, dy/dist
        spd = 5.0

        if self.etype == EnemyType.DRONE:
            bullets.append(Bullet(self.x, self.y+self.size, nx*spd, ny*spd,
                                  self.dmg, C.RED, 5, False, "enemy"))

        elif self.etype == EnemyType.HUNTER:
            # Aimed + prediction
            bullets.append(Bullet(self.x, self.y+self.size, nx*6, ny*6,
                                  self.dmg, C.ORANGE, 5, False, "enemy"))

        elif self.etype == EnemyType.BOMBER:
            # Spread shot
            for a_off in [-20, 0, 20]:
                a = math.atan2(dy, dx) + math.radians(a_off)
                bullets.append(Bullet(self.x, self.y, math.cos(a)*4, math.sin(a)*4,
                                      self.dmg, C.PURPLE, 7, False, "enemy"))

        elif self.etype == EnemyType.FORTRESS:
            # Rapid triple
            for a_off in [-8, 0, 8]:
                a = math.atan2(dy, dx) + math.radians(a_off)
                bullets.append(Bullet(self.x, self.y, math.cos(a)*7, math.sin(a)*7,
                                      self.dmg, (100,100,255), 5, False, "enemy"))

        elif self.etype == EnemyType.LEECH:
            # Only fires when close
            if dist < 150:
                bullets.append(Bullet(self.x, self.y, nx*8, ny*8,
                                      self.dmg, C.GREEN, 6, False, "enemy"))

        elif self.etype == EnemyType.GHOST:
            # 8-directional
            for i in range(8):
                a = math.radians(i * 45)
                bullets.append(Bullet(self.x, self.y, math.cos(a)*3.5, math.sin(a)*3.5,
                                      self.dmg//2, C.ENE_GHOST, 4, False, "enemy"))

    def draw(self, surf):
        cx, cy = int(self.x), int(self.y)
        col = self.color
        t = self.t

        if self.hit_flash > 0:
            col = tuple(min(255, int(c + self.hit_flash * (255-c))) for c in col[:3])

        # HP bar (show if damaged)
        if self.hp < self.max_hp:
            bar_w = self.size * 2 + 10
            bar_h = 4
            bx = cx - bar_w//2
            by = cy - self.size - 10
            pygame.draw.rect(surf, C.RED_DARK, (bx, by, bar_w, bar_h))
            hp_f = max(0, self.hp / self.max_hp)
            bar_col = C.GREEN if hp_f > 0.5 else C.YELLOW if hp_f > 0.25 else C.RED
            pygame.draw.rect(surf, bar_col, (bx, by, int(bar_w*hp_f), bar_h))

        if self.etype == EnemyType.DRONE:
            # Diamond shape
            pts = [(cx, cy-self.size), (cx+self.size, cy),
                   (cx, cy+self.size), (cx-self.size, cy)]
            pygame.draw.polygon(surf, col, pts)
            pygame.draw.polygon(surf, C.WHITE, pts, 1)
            pygame.draw.circle(surf, C.RED, (cx, cy), 5)

        elif self.etype == EnemyType.HUNTER:
            # Arrow pointing toward player
            a = math.radians(self.angle)
            pts = [
                (cx + math.cos(a)*self.size*1.4, cy + math.sin(a)*self.size*1.4),
                (cx + math.cos(a+2.4)*self.size, cy + math.sin(a+2.4)*self.size),
                (cx - math.cos(a)*self.size*0.5, cy - math.sin(a)*self.size*0.5),
                (cx + math.cos(a-2.4)*self.size, cy + math.sin(a-2.4)*self.size),
            ]
            pygame.draw.polygon(surf, col, pts)
            pygame.draw.polygon(surf, C.WHITE, pts, 1)
            pygame.draw.circle(surf, C.YELLOW, (cx, cy), 4)

        elif self.etype == EnemyType.BOMBER:
            # Fat hexagon
            pts = []
            for i in range(6):
                a = math.radians(i*60 + t*20)
                pts.append((cx + math.cos(a)*self.size, cy + math.sin(a)*self.size))
            pygame.draw.polygon(surf, col, pts)
            pygame.draw.polygon(surf, C.WHITE, pts, 1)
            # Bomb indicator
            inner_pts = []
            for i in range(6):
                a = math.radians(i*60 + t*20 + 30)
                inner_pts.append((cx + math.cos(a)*self.size*0.5,
                                  cy + math.sin(a)*self.size*0.5))
            pygame.draw.polygon(surf, C.RED, inner_pts)

        elif self.etype == EnemyType.FORTRESS:
            # Square with rotating turrets
            hw = self.size
            pygame.draw.rect(surf, col, (cx-hw, cy-hw, hw*2, hw*2))
            pygame.draw.rect(surf, C.WHITE, (cx-hw, cy-hw, hw*2, hw*2), 2)
            for i in range(4):
                a = math.radians(i*90 + t*30)
                tx = cx + math.cos(a) * hw * 0.8
                ty = cy + math.sin(a) * hw * 0.8
                pygame.draw.circle(surf, C.BLUE, (int(tx), int(ty)), 5)

        elif self.etype == EnemyType.LEECH:
            # Spiky circle
            pts = []
            for i in range(12):
                r = self.size * (1.4 if i%2==0 else 0.7)
                a = math.radians(i*30 + t*50)
                pts.append((cx + math.cos(a)*r, cy + math.sin(a)*r))
            pygame.draw.polygon(surf, col, pts)
            pygame.draw.polygon(surf, C.WHITE, pts, 1)
            pygame.draw.circle(surf, C.GREEN, (cx, cy), 4)

        elif self.etype == EnemyType.GHOST:
            # Transparent with pulsing outline
            alpha = int(120 + 80*math.sin(t*3))
            gs = pygame.Surface((self.size*3, self.size*3), pygame.SRCALPHA)
            pygame.draw.circle(gs, (*col, alpha),
                               (self.size, self.size), self.size)
            surf.blit(gs, (cx-self.size, cy-self.size))
            r = int(self.size + 4*math.sin(t*4))
            pygame.draw.circle(surf, col, (cx, cy), r, 2)

# ═══════════════════════════════════════════════════════════════
#   BOSS CLASS
# ═══════════════════════════════════════════════════════════════
class Boss:
    def __init__(self, boss_type: EnemyType, sector: int):
        self.boss_type = boss_type
        self.x = W / 2
        self.y = -200.0   # starts off screen
        self.alive = True
        self.t = 0.0
        self.phase = 1
        self.entry_done = False

        cfg = {
            EnemyType.BOSS_1: {
                "name": "WARLORD MK-VII",
                "hp": 1200, "sz": 60, "col": (255,80,80),
                "phases": 3, "spd": 1.5,
            },
            EnemyType.BOSS_2: {
                "name": "VOID TITAN",
                "hp": 2200, "sz": 80, "col": (80,80,255),
                "phases": 3, "spd": 1.2,
            },
            EnemyType.BOSS_3: {
                "name": "RIFT DESTROYER",
                "hp": 3500, "sz": 90, "col": (255,50,200),
                "phases": 4, "spd": 1.0,
            },
        }
        c = cfg[boss_type]
        self.name      = c["name"]
        self.max_hp    = c["hp"] + sector * 400
        self.hp        = self.max_hp
        self.size      = c["sz"]
        self.color     = c["col"]
        self.num_phases= c["phases"]
        self.speed     = c["spd"]

        self.score     = self.max_hp * 2
        self.credits   = 200 + sector * 50

        self.fire_timers = [0.0, 0.0, 0.0, 0.0]
        self.fire_cds    = [0.6, 1.2, 2.0, 3.0]
        self.angle = 90.0
        self.pattern_t = 0.0
        self.hit_flash = 0.0
        self.etype = boss_type
        self.is_boss = True
        self.chained = False

    @property
    def phase_threshold(self):
        return 1.0 - (self.phase-1) / self.num_phases

    def check_phase(self):
        hp_f = self.hp / self.max_hp
        new_phase = min(self.num_phases,
                        int((1.0 - hp_f) * self.num_phases) + 1)
        if new_phase > self.phase:
            self.phase = new_phase
            return True  # phase changed
        return False

    def take_damage(self, amount):
        self.hp -= amount
        self.hit_flash = 1.0
        if self.hp <= 0:
            self.alive = False

    def update(self, dt, player_x, player_y, bullets, particles):
        self.t += dt
        self.pattern_t += dt
        self.hit_flash = max(0, self.hit_flash - dt * 3)

        if not self.entry_done:
            self.y += 1.5
            if self.y >= 150:
                self.entry_done = True
            return

        # Boss movement patterns by phase
        if self.phase == 1:
            self.x = W/2 + math.sin(self.pattern_t * 0.5) * (W/3)
            self.y = 150 + math.sin(self.pattern_t * 0.3) * 40

        elif self.phase == 2:
            self.x = W/2 + math.sin(self.pattern_t * 0.9) * (W/2.5)
            self.y = 160 + math.sin(self.pattern_t * 0.6) * 60
            # More aggressive

        elif self.phase == 3:
            # Erratic
            self.x = W/2 + math.sin(self.pattern_t * 1.5) * (W/2.2)
            self.y = 170 + math.cos(self.pattern_t * 0.8) * 80
            # Occasional charge
            if int(self.pattern_t * 2) % 8 == 0:
                dy = player_y - self.y
                self.y += dy * 0.01

        elif self.phase >= 4:
            # Frenzy
            self.x = W/2 + math.sin(self.pattern_t * 2) * (W/2)
            self.y = 140 + math.sin(self.pattern_t * 1.2) * 100

        self.x = max(self.size+10, min(W-self.size-10, self.x))
        self.y = max(self.size, min(H*0.5, self.y))

        # Aim
        dx = player_x - self.x; dy = player_y - self.y
        self.angle = math.degrees(math.atan2(dy, dx))

        # Firing patterns per phase
        self._fire_patterns(dt, bullets, player_x, player_y)

    def _fire_patterns(self, dt, bullets, px, py):
        phase = self.phase

        # Pattern 1: aimed burst
        self.fire_timers[0] -= dt
        if self.fire_timers[0] <= 0:
            self.fire_timers[0] = self.fire_cds[0] / max(1, phase * 0.7)
            dx = px - self.x; dy = py - self.y
            dist = math.hypot(dx, dy)
            if dist > 0:
                nx, ny = dx/dist, dy/dist
                spd = 5 + phase * 0.5
                for a_off in range(-20, 21, 20 if phase < 3 else 10):
                    a = math.atan2(dy, dx) + math.radians(a_off)
                    bullets.append(Bullet(self.x, self.y+self.size,
                                          math.cos(a)*spd, math.sin(a)*spd,
                                          20+phase*5, self.color, 7, False, "enemy"))

        # Pattern 2: spiral
        if phase >= 2:
            self.fire_timers[1] -= dt
            if self.fire_timers[1] <= 0:
                self.fire_timers[1] = self.fire_cds[1]
                num = 8 + phase * 2
                for i in range(num):
                    a = math.radians(i * (360/num) + self.t * 80)
                    bullets.append(Bullet(self.x, self.y,
                                          math.cos(a)*4, math.sin(a)*4,
                                          15, (255,150,50), 6, False, "enemy"))

        # Pattern 3: column bombs
        if phase >= 3:
            self.fire_timers[2] -= dt
            if self.fire_timers[2] <= 0:
                self.fire_timers[2] = self.fire_cds[2]
                for bx in [W*0.25, W*0.5, W*0.75]:
                    bullets.append(Bullet(bx, self.y+self.size, 0, 7,
                                          30, (200,50,255), 9, False, "enemy"))

        # Pattern 4: rage
        if phase >= 4:
            self.fire_timers[3] -= dt
            if self.fire_timers[3] <= 0:
                self.fire_timers[3] = self.fire_cds[3]
                dx = px - self.x; dy = py - self.y
                dist = math.hypot(dx, dy)
                if dist > 0:
                    nx, ny = dx/dist, dy/dist
                    for i in range(5):
                        a_off = random.uniform(-15, 15)
                        a = math.atan2(dy, dx) + math.radians(a_off)
                        bullets.append(Bullet(self.x, self.y,
                                              math.cos(a)*9, math.sin(a)*9,
                                              40, C.WHITE, 8, True, "enemy"))

    def draw(self, surf):
        cx, cy = int(self.x), int(self.y)
        t = self.t
        col = self.color
        sz = self.size

        if self.hit_flash > 0:
            f = self.hit_flash
            col = (min(255, int(col[0]*(1-f) + 255*f)),
                   int(col[1]*(1-f)),
                   int(col[2]*(1-f)))

        phase = self.phase

        if self.boss_type == EnemyType.BOSS_1:
            # WARLORD: Heavy cruiser shape
            # Main hull
            hull = [
                (cx, cy-sz), (cx-sz*0.6, cy-sz*0.3),
                (cx-sz*0.8, cy+sz*0.4), (cx-sz*0.4, cy+sz*0.7),
                (cx, cy+sz*0.5),
                (cx+sz*0.4, cy+sz*0.7), (cx+sz*0.8, cy+sz*0.4),
                (cx+sz*0.6, cy-sz*0.3),
            ]
            pygame.draw.polygon(surf, col, hull)
            pygame.draw.polygon(surf, C.WHITE, hull, 2)
            # Rotating gun turrets
            for i in range(4):
                a = math.radians(i*90 + t*40)
                tx = cx + math.cos(a)*sz*0.5
                ty = cy + math.sin(a)*sz*0.5
                pygame.draw.circle(surf, C.RED, (int(tx), int(ty)), 8)
                bx = tx + math.cos(a)*12; by = ty + math.sin(a)*12
                pygame.draw.line(surf, C.GRAY, (int(tx), int(ty)), (int(bx), int(by)), 3)
            # Core reactor
            cr = int(10 + 4*math.sin(t*6))
            pygame.draw.circle(surf, C.YELLOW, (cx, cy), cr)
            pygame.draw.circle(surf, C.WHITE, (cx, cy), cr//2)

        elif self.boss_type == EnemyType.BOSS_2:
            # VOID TITAN: Massive cube-like form
            hw = sz
            # Outer ring
            for i in range(6):
                a = math.radians(i*60 + t*15)
                r = sz + 12
                ox = cx + math.cos(a)*r; oy = cy + math.sin(a)*r
                pygame.draw.circle(surf, col, (int(ox), int(oy)), 10)
                pygame.draw.line(surf, col, (cx, cy), (int(ox), int(oy)), 2)
            # Body
            pts = [(cx + math.cos(math.radians(i*60+t*8))*sz,
                    cy + math.sin(math.radians(i*60+t*8))*sz) for i in range(6)]
            pygame.draw.polygon(surf, col, pts)
            pygame.draw.polygon(surf, C.WHITE, pts, 2)
            # Energy core
            for ring in range(3):
                r2 = int((sz*0.7 - ring*12) + 4*math.sin(t*4+ring))
                alpha = 180 - ring*40
                rs = pygame.Surface((r2*2+4, r2*2+4), pygame.SRCALPHA)
                pygame.draw.circle(rs, (*C.BLUE, alpha), (r2+2, r2+2), r2)
                surf.blit(rs, (cx-r2-2, cy-r2-2))
            # Eye
            eye_r = int(8 + 3*math.sin(t*10))
            pygame.draw.circle(surf, C.CYAN, (cx, cy), eye_r)

        elif self.boss_type == EnemyType.BOSS_3:
            # RIFT DESTROYER: Monstrous organic-mechanical hybrid
            # Tentacle-like arms
            for i in range(6):
                a_base = math.radians(i*60 + t*20)
                pts = [(cx, cy)]
                for seg in range(5):
                    a = a_base + math.sin(t*3+seg*0.5) * 0.4
                    r = sz * 0.4 * (seg+1)
                    px2 = cx + math.cos(a)*r; py2 = cy + math.sin(a)*r
                    pts.append((px2, py2))
                if len(pts) >= 2:
                    for j in range(len(pts)-1):
                        thick = max(1, 6-j)
                        pygame.draw.line(surf, col,
                                         (int(pts[j][0]), int(pts[j][1])),
                                         (int(pts[j+1][0]), int(pts[j+1][1])), thick)
            # Main body
            for ring in range(4):
                r2 = sz - ring * 14
                a_off = t * (20 + ring*15)
                pcount = 8 - ring
                ring_pts = [(cx + math.cos(math.radians(i*(360/pcount)+a_off))*r2,
                             cy + math.sin(math.radians(i*(360/pcount)+a_off))*r2)
                            for i in range(pcount)]
                c2 = tuple(int(c * (1 - ring*0.15)) for c in col[:3])
                pygame.draw.polygon(surf, c2, ring_pts)
                pygame.draw.polygon(surf, C.WHITE, ring_pts, 1)

            # Core void
            for ri in range(4):
                r3 = int((sz//3 - ri*5) + 3*math.sin(t*8+ri))
                gs2 = pygame.Surface((r3*2+2, r3*2+2), pygame.SRCALPHA)
                alpha2 = 220 - ri*30
                c3 = [(255,50,200), (200,50,255), (100,50,255), (50,50,255)][ri]
                pygame.draw.circle(gs2, (*c3, alpha2), (r3+1, r3+1), r3)
                surf.blit(gs2, (cx-r3-1, cy-r3-1))

        # HP bar
        bar_w = sz * 2 + 40
        bar_h = 12
        bx = cx - bar_w//2; by = cy - sz - 30
        pygame.draw.rect(surf, C.RED_DARK, (bx-1, by-1, bar_w+2, bar_h+2))
        pygame.draw.rect(surf, C.RED_DARK, (bx, by, bar_w, bar_h))
        hp_f = max(0, self.hp / self.max_hp)
        hp_col = C.GREEN if hp_f > 0.6 else C.YELLOW if hp_f > 0.3 else C.RED
        pygame.draw.rect(surf, hp_col, (bx, by, int(bar_w*hp_f), bar_h))
        pygame.draw.rect(surf, C.WHITE, (bx, by, bar_w, bar_h), 1)

        # Phase indicator pips
        for i in range(self.num_phases):
            pip_col = C.YELLOW if i < self.phase else C.GRAY
            pygame.draw.circle(surf, pip_col,
                               (bx + int(bar_w * (i+1) / (self.num_phases+1)), by-8), 5)

        # Boss name
        name_surf = pygame.font.SysFont("impact", 18).render(
            f"☠ {self.name}  ☠", True, col)
        nr = name_surf.get_rect(centerx=cx, bottom=by-14)
        surf.blit(name_surf, nr)

# ═══════════════════════════════════════════════════════════════
#   POWER-UP DROPS
# ═══════════════════════════════════════════════════════════════
class PowerupType(Enum):
    HEALTH      = "HEALTH PACK"
    SHIELD      = "SHIELD CHARGE"
    WEAPON_UP   = "WEAPON BOOST"
    SCORE_MULT  = "SCORE FRENZY"
    INVINCIBLE  = "INVINCIBILITY"
    BOMB        = "NOVA BOMB"
    CREDIT      = "CREDIT CACHE"
    AMMO        = "HYPER AMMO"

POWERUP_COLORS = {
    PowerupType.HEALTH:     C.GREEN,
    PowerupType.SHIELD:     C.CYAN,
    PowerupType.WEAPON_UP:  C.YELLOW,
    PowerupType.SCORE_MULT: C.GOLD,
    PowerupType.INVINCIBLE: C.WHITE,
    PowerupType.BOMB:       C.RED,
    PowerupType.CREDIT:     C.PURPLE,
    PowerupType.AMMO:       C.ORANGE,
}

class Powerup:
    def __init__(self, x, y, ptype: PowerupType = None):
        self.x = float(x)
        self.y = float(y)
        self.vy = 1.5
        self.ptype = ptype or random.choice(list(PowerupType))
        self.color = POWERUP_COLORS[self.ptype]
        self.t = random.uniform(0, math.pi*2)
        self.alive = True
        self.size = 16

    def update(self, dt):
        self.t += dt * 3
        self.y += self.vy
        if self.y > H + 40:
            self.alive = False

    def draw(self, surf):
        cx, cy = int(self.x), int(self.y + math.sin(self.t)*4)
        col = self.color
        sz = self.size
        t = self.t

        # Glow
        gs = pygame.Surface((sz*3, sz*3), pygame.SRCALPHA)
        glow_a = int(80 + 40*math.sin(t*2))
        pygame.draw.circle(gs, (*col, glow_a), (sz, sz), sz+4)
        surf.blit(gs, (cx-sz, cy-sz))

        # Outer ring
        r = int(sz + 2*math.sin(t*3))
        pygame.draw.circle(surf, col, (cx, cy), r, 2)

        # Icon by type
        if self.ptype == PowerupType.HEALTH:
            pygame.draw.rect(surf, col, (cx-sz//2, cy-3, sz, 6))
            pygame.draw.rect(surf, col, (cx-3, cy-sz//2, 6, sz))

        elif self.ptype == PowerupType.SHIELD:
            arc_rect = pygame.Rect(cx-sz//2, cy-sz//2, sz, sz)
            pygame.draw.arc(surf, col, arc_rect, math.pi*0.2, math.pi*0.8, 3)
            pygame.draw.arc(surf, col, arc_rect, math.pi*1.2, math.pi*1.8, 3)

        elif self.ptype == PowerupType.WEAPON_UP:
            pts = [(cx, cy-sz//2), (cx-sz//3, cy), (cx, cy-sz//5),
                   (cx+sz//3, cy), (cx, cy+sz//2)]
            pygame.draw.lines(surf, col, False, pts, 2)

        elif self.ptype == PowerupType.SCORE_MULT:
            # Star
            for i in range(5):
                a = math.radians(i*72 - 90)
                px2 = cx + math.cos(a)*sz//2; py2 = cy + math.sin(a)*sz//2
                pygame.draw.circle(surf, col, (int(px2), int(py2)), 3)

        elif self.ptype == PowerupType.INVINCIBLE:
            pygame.draw.circle(surf, col, (cx, cy), sz//2, 2)
            pygame.draw.circle(surf, C.WHITE, (cx, cy), sz//4)

        elif self.ptype == PowerupType.BOMB:
            pygame.draw.circle(surf, col, (cx, cy), sz//2, 2)
            pygame.draw.line(surf, C.YELLOW, (cx, cy-sz//2), (cx+sz//4, cy-sz*0.7), 2)

        elif self.ptype == PowerupType.CREDIT:
            font = pygame.font.SysFont("impact", 14)
            s = font.render("$", True, col)
            surf.blit(s, s.get_rect(center=(cx, cy)))

        elif self.ptype == PowerupType.AMMO:
            for i in range(3):
                pygame.draw.rect(surf, col, (cx-6+i*5, cy-sz//2+2, 3, sz-4))

# ═══════════════════════════════════════════════════════════════
#   FLOATING TEXT (damage numbers, score popups)
# ═══════════════════════════════════════════════════════════════
@dataclass
class FloatText:
    text: str; x: float; y: float; vy: float; color: tuple
    life: float; max_life: float; size: int = 18
    bold: bool = False

    def update(self):
        self.y += self.vy
        self.vy -= 0.05
        self.life -= 1/FPS

    def draw(self, surf):
        alpha = max(0, self.life / self.max_life)
        font = pygame.font.SysFont("impact", self.size, bold=self.bold)
        col = tuple(min(255, int(c)) for c in self.color)
        rendered = font.render(self.text, True, col)
        rendered.set_alpha(int(255*alpha))
        surf.blit(rendered, rendered.get_rect(centerx=int(self.x), centery=int(self.y)))

# ═══════════════════════════════════════════════════════════════
#   UPGRADE SHOP DATA
# ═══════════════════════════════════════════════════════════════
UPGRADES_CATALOG = [
    {"id":"damage",    "name":"DAMAGE AMP",      "desc":"Increase weapon damage by 25%",     "base_cost":80,  "max_level":5, "color":C.RED},
    {"id":"fire_rate", "name":"RAPID FIRE",       "desc":"Increase fire rate by 20%",          "base_cost":70,  "max_level":5, "color":C.YELLOW},
    {"id":"shield",    "name":"SHIELD MATRIX",    "desc":"Boost shield capacity & regen 30%", "base_cost":90,  "max_level":5, "color":C.CYAN},
    {"id":"speed",     "name":"OVERDRIVE",        "desc":"Increase ship speed by 15%",         "base_cost":60,  "max_level":5, "color":C.NEON_GREEN},
    {"id":"hp",        "name":"HULL PLATING",     "desc":"Increase max HP by 20%",             "base_cost":100, "max_level":5, "color":C.GREEN},
    {"id":"special",   "name":"ABILITY ENHANCE",  "desc":"Reduce ability cooldown by 20%",    "base_cost":120, "max_level":5, "color":C.PURPLE},
]

# ═══════════════════════════════════════════════════════════════
#   WAVE / SECTOR MANAGER
# ═══════════════════════════════════════════════════════════════
class WaveManager:
    def __init__(self):
        self.sector = 1
        self.wave   = 1
        self.waves_per_sector = 5
        self.enemies_this_wave = 0
        self.enemies_spawned   = 0
        self.enemies_killed    = 0
        self.spawn_queue: List[Tuple[EnemyType, float]] = []  # (type, delay)
        self.spawn_timer = 0.0
        self.wave_complete = False
        self.boss_wave = False
        self.between_waves = False
        self.between_timer = 3.0
        self.total_waves_completed = 0

    def start_wave(self, wave, sector):
        self.wave = wave
        self.sector = sector
        self.enemies_spawned = 0
        self.enemies_killed  = 0
        self.wave_complete   = False
        self.spawn_queue     = []
        self.boss_wave = (wave == self.waves_per_sector)
        cfg = SECTOR_CONFIG.get(sector, SECTOR_CONFIG[5])

        if self.boss_wave:
            self.enemies_this_wave = 1
            boss_types = [EnemyType.BOSS_1, EnemyType.BOSS_2, EnemyType.BOSS_3]
            bt = boss_types[min(sector-1, 2)]
            self.spawn_queue = [(bt, 2.0)]
        else:
            # Build wave composition
            wave_difficulty = (sector-1) * self.waves_per_sector + wave
            count = 5 + wave_difficulty * 2
            self.enemies_this_wave = count
            types_available = self._available_types(sector, wave)

            for i in range(count):
                etype = random.choices(
                    types_available,
                    weights=[4 if t==EnemyType.DRONE else
                             3 if t==EnemyType.HUNTER else
                             2 for t in types_available]
                )[0]
                delay = i * (0.8 / cfg["spawn_rate"])
                self.spawn_queue.append((etype, delay))

        self.spawn_timer = 0.0

    def _available_types(self, sector, wave):
        types = [EnemyType.DRONE]
        if sector >= 1 and wave >= 2: types.append(EnemyType.HUNTER)
        if sector >= 1 and wave >= 3: types.append(EnemyType.LEECH)
        if sector >= 2: types.append(EnemyType.BOMBER)
        if sector >= 2 and wave >= 3: types.append(EnemyType.GHOST)
        if sector >= 3: types.append(EnemyType.FORTRESS)
        return types

    def update(self, dt, enemies: List[Enemy], boss_list) -> Optional[object]:
        """Returns a newly spawned enemy/boss or None."""
        if self.wave_complete:
            return None

        cfg = SECTOR_CONFIG.get(self.sector, SECTOR_CONFIG[5])

        # Process spawn queue
        if self.spawn_queue:
            self.spawn_timer += dt
            next_type, delay = self.spawn_queue[0]
            if self.spawn_timer >= delay:
                self.spawn_queue.pop(0)
                self.enemies_spawned += 1

                if next_type in (EnemyType.BOSS_1, EnemyType.BOSS_2, EnemyType.BOSS_3):
                    b = Boss(next_type, self.sector)
                    boss_list.append(b)
                    return b
                else:
                    x = random.uniform(40, W-40)
                    e = Enemy(next_type, x, -40,
                              hp_mult=cfg["enemy_hp"],
                              spd_mult=cfg["enemy_spd"])
                    enemies.append(e)
                    return e

        # Check wave complete
        all_dead = all(not e.alive for e in enemies) and \
                   all(not b.alive for b in boss_list)
        if self.enemies_spawned >= self.enemies_this_wave and all_dead:
            self.wave_complete = True
            self.total_waves_completed += 1

        return None

# ═══════════════════════════════════════════════════════════════
#   UI HELPERS
# ═══════════════════════════════════════════════════════════════
def draw_text(surf, text, font, color, x, y, center=True, shadow=True):
    if shadow:
        s = font.render(text, True, (0,0,0))
        r = s.get_rect()
        if center: r.center = (x+2, y+2)
        else: r.topleft = (x+2, y+2)
        surf.blit(s, r)
    rendered = font.render(text, True, color)
    r = rendered.get_rect()
    if center: r.center = (x, y)
    else: r.topleft = (x, y)
    surf.blit(rendered, r)
    return r

def draw_glow_text(surf, text, font, color, x, y, glow_radius=8, glow_col=None):
    gc = glow_col or color
    for gi in range(glow_radius, 0, -2):
        a = int(100 * (1 - gi/glow_radius))
        g = font.render(text, True, gc)
        g.set_alpha(a)
        surf.blit(g, g.get_rect(center=(x, y)))
    rendered = font.render(text, True, color)
    surf.blit(rendered, rendered.get_rect(center=(x, y)))

def draw_bar(surf, x, y, w, h, value, max_val, col, bg=C.DARK, border=True,
             glow=False, label=None, font=None):
    pygame.draw.rect(surf, bg, (x, y, w, h), border_radius=4)
    f = max(0, min(1, value / max_val)) if max_val > 0 else 0
    if f > 0:
        fw = max(1, int(w * f))
        pygame.draw.rect(surf, col, (x, y, fw, h), border_radius=4)
        if glow and f > 0.1:
            gs = pygame.Surface((fw+6, h+6), pygame.SRCALPHA)
            pygame.draw.rect(gs, (*col, 60), (0, 0, fw+6, h+6), border_radius=6)
            surf.blit(gs, (x-3, y-3))
    if border:
        pygame.draw.rect(surf, C.GRAY, (x, y, w, h), 1, border_radius=4)
    if label and font:
        draw_text(surf, label, font, C.WHITE, x + w//2, y + h//2)

class Button:
    def __init__(self, x, y, w, h, text, color=C.NEON_BLUE,
                 hover=C.CYAN, font=None, radius=8):
        self.rect = pygame.Rect(x-w//2, y-h//2, w, h)
        self.text = text; self.color = color; self.hover = hover
        self.font = font; self.radius = radius
        self.hovered = False; self.pulse = 0.0

    def update(self, mx, my):
        self.hovered = self.rect.collidepoint(mx, my)
        self.pulse = (self.pulse + 0.1) % (math.pi*2)

    def draw(self, surf):
        col = self.hover if self.hovered else self.color
        if self.hovered:
            gs = pygame.Surface((self.rect.w+16, self.rect.h+16), pygame.SRCALPHA)
            pygame.draw.rect(gs, (*col, 50), (0,0,self.rect.w+16,self.rect.h+16),
                             border_radius=self.radius+4)
            surf.blit(gs, (self.rect.x-8, self.rect.y-8))
        pygame.draw.rect(surf, col, self.rect, border_radius=self.radius)
        pygame.draw.rect(surf, C.WHITE, self.rect, 2, border_radius=self.radius)
        if self.font:
            draw_text(surf, self.text, self.font, C.WHITE,
                      self.rect.centerx, self.rect.centery)

    def clicked(self, ev):
        return (ev.type == pygame.MOUSEBUTTONDOWN and ev.button==1 and
                self.rect.collidepoint(ev.pos))

# ═══════════════════════════════════════════════════════════════
#   MAIN GAME
# ═══════════════════════════════════════════════════════════════
class VoidRift:
    def __init__(self):
        pygame.init()
        pygame.mixer.init(22050, -16, 2, 512)
        self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption(TITLE)
        self.clock  = pygame.time.Clock()

        # Fonts
        self.f_huge  = pygame.font.SysFont("impact", 90)
        self.f_big   = pygame.font.SysFont("impact", 54)
        self.f_med   = pygame.font.SysFont("impact", 34)
        self.f_sm    = pygame.font.SysFont("impact", 22)
        self.f_xs    = pygame.font.SysFont("impact", 16)
        self.f_title = pygame.font.SysFont("impact", 110)
        self.f_hud   = pygame.font.SysFont("couriernew", 16, bold=True)

        self.particles   = ParticleSystem()
        self.starfield   = StarField()
        self.state       = GS.TITLE
        self.tick        = 0
        self.dt          = 1/FPS

        # Game objects
        self.player: Optional[Player]       = None
        self.enemies:   List[Enemy]         = []
        self.bullets:   List[Bullet]        = []
        self.enemy_bullets: List[Bullet]    = []
        self.powerups:  List[Powerup]       = []
        self.float_texts: List[FloatText]   = []
        self.boss_list: List[Boss]          = []

        self.wave_mgr   = WaveManager()
        self.sector     = 1
        self.wave_in_sector = 1

        # UI selections
        self.selected_ship = 0

        # High score
        self.high_score = 0
        self.high_scores = []   # list of (score, ship_name)

        # Screen shake
        self.shake_x = 0.0; self.shake_y = 0.0
        self.shake_intensity = 0.0

        # Flash overlay
        self.flash_color = (0,0,0)
        self.flash_alpha  = 0.0

        # Pause
        self.pause_selected = 0

        # Boss intro
        self.boss_intro_timer = 0.0
        self.boss_intro_name  = ""

        # Between-wave
        self.wave_transition_timer = 0.0
        self.wave_transition_msg   = ""

        # Build sounds
        self._make_sounds()
        # Build buttons
        self._build_buttons()

        # Title animation
        self.title_t = 0.0

        # Chain lightning rendering
        self.chain_bolts: List[dict] = []

        # Background explosions for title
        self.bg_explosions = []

    # ─── SOUNDS (procedural) ────────────────────────────────────
    def _make_sounds(self):
        self.snd = {}
        sr = 22050

        def tone(freq, dur_ms, vol=0.3, wtype='sine', decay=True):
            n = int(sr * dur_ms / 1000)
            buf = []
            for i in range(n):
                t2 = i / sr
                if wtype == 'sine': v = math.sin(2*math.pi*freq*t2)
                elif wtype == 'square': v = 1.0 if math.sin(2*math.pi*freq*t2)>0 else -1.0
                elif wtype == 'noise': v = random.uniform(-1,1)
                elif wtype == 'saw': v = 2*(freq*t2 % 1) - 1
                else: v = 0
                if decay: v *= max(0, 1 - i/n)
                buf.append(int(v*vol*32767))
            a = arr.array('h', buf*2)
            return pygame.sndarray.make_sound(a)

        try:
            self.snd['laser']   = tone(800,  80, 0.15, 'square')
            self.snd['plasma']  = tone(200, 300, 0.25, 'saw')
            self.snd['hit']     = tone(150, 120, 0.35, 'noise')
            self.snd['explode'] = tone(80,  400, 0.4,  'noise')
            self.snd['powerup'] = tone(660, 200, 0.3,  'sine')
            self.snd['click']   = tone(440,  60, 0.2,  'square')
            self.snd['damage']  = tone(120, 300, 0.45, 'noise')
            self.snd['boss']    = tone(60,  600, 0.5,  'square')
            self.snd['warp']    = tone(300, 400, 0.3,  'saw')
            self.snd['combo']   = tone(880, 150, 0.2,  'sine')
        except Exception:
            pass

    def play(self, name):
        try:
            if name in self.snd: self.snd[name].play()
        except: pass

    # ─── BUTTONS ────────────────────────────────────────────────
    def _build_buttons(self):
        f = self.f_med; fs = self.f_sm
        # Title
        self.btn_play  = Button(W//2, 520, 280, 60, "START MISSION", C.NEON_BLUE, C.CYAN, f)
        self.btn_exit  = Button(W//2, 610, 280, 60, "EXIT",          C.RED,       C.ORANGE, f)
        # Ship select
        self.btn_ship_l = Button(210, 440, 60, 50, "◄", C.GRAY, C.WHITE, f)
        self.btn_ship_r = Button(W-210, 440, 60, 50, "►", C.GRAY, C.WHITE, f)
        self.btn_confirm= Button(W//2, 700, 300, 60, "DEPLOY SHIP", C.GREEN, C.NEON_GREEN, f)
        # Upgrade shop
        self.btn_launch = Button(W//2, 730, 320, 60, "LAUNCH MISSION", C.GREEN, C.NEON_GREEN, f)
        # Pause
        self.btn_resume = Button(W//2, 340, 260, 55, "RESUME",  C.NEON_BLUE, C.CYAN, fs)
        self.btn_quit_p = Button(W//2, 420, 260, 55, "QUIT",    C.RED,       C.ORANGE, fs)
        # Game over
        self.btn_retry  = Button(W//2, 520, 260, 55, "TRY AGAIN",   C.GREEN,    C.NEON_GREEN, fs)
        self.btn_menu   = Button(W//2, 600, 260, 55, "MAIN MENU",   C.NEON_BLUE, C.CYAN, fs)

    # ─── GAME INIT ──────────────────────────────────────────────
    def init_game(self, ship_idx):
        self.player       = Player(SHIP_CLASSES[ship_idx])
        self.enemies      = []
        self.bullets      = []
        self.enemy_bullets= []
        self.powerups     = []
        self.float_texts  = []
        self.boss_list    = []
        self.sector       = 1
        self.wave_in_sector = 1
        self.wave_mgr     = WaveManager()
        self.wave_mgr.start_wave(1, 1)
        self.particles    = ParticleSystem()
        self.flash_alpha  = 0.0
        self.chain_bolts  = []
        self.particles.emit_warp(self.player.x, self.player.y)
        self.play('warp')

    # ─── MAIN LOOP ──────────────────────────────────────────────
    def run(self):
        while True:
            self.dt = self.clock.tick(FPS) / 1000.0
            self.dt = min(self.dt, 0.033)  # cap dt
            self.tick += 1
            self.title_t += self.dt

            mx, my = pygame.mouse.get_pos()
            events = pygame.event.get()

            for e in events:
                if e.type == pygame.QUIT:
                    pygame.quit(); sys.exit()

            self.starfield.update(scroll_speed=1.0 if self.state==GS.GAMEPLAY else 0.3)

            if   self.state == GS.TITLE:       self._title(events, mx, my)
            elif self.state == GS.SHIP_SELECT: self._ship_select(events, mx, my)
            elif self.state == GS.UPGRADE:     self._upgrade_screen(events, mx, my)
            elif self.state == GS.GAMEPLAY:    self._gameplay(events, mx, my)
            elif self.state == GS.BOSS_INTRO:  self._boss_intro(events)
            elif self.state == GS.PAUSED:      self._paused(events, mx, my)
            elif self.state == GS.GAME_OVER:   self._game_over(events, mx, my)
            elif self.state == GS.VICTORY:     self._victory(events, mx, my)

            self.particles.update()

            # Screen shake decay
            self.shake_intensity = max(0, self.shake_intensity - self.dt * 8)
            self.shake_x = math.sin(self.tick * 0.8) * self.shake_intensity
            self.shake_y = math.cos(self.tick * 0.7) * self.shake_intensity

            # Flash decay
            self.flash_alpha = max(0, self.flash_alpha - self.dt * 3)

            pygame.display.flip()

    def _add_shake(self, intensity):
        self.shake_intensity = max(self.shake_intensity, intensity)

    def _add_flash(self, color, alpha):
        self.flash_color = color
        self.flash_alpha = max(self.flash_alpha, alpha)

    # ═══════════════════════════════════════════════════════════
    #   TITLE SCREEN
    # ═══════════════════════════════════════════════════════════
    def _title(self, events, mx, my):
        self.btn_play.update(mx, my)
        self.btn_exit.update(mx, my)

        for e in events:
            if self.btn_play.clicked(e):
                self.play('click')
                self.state = GS.SHIP_SELECT
            if self.btn_exit.clicked(e):
                pygame.quit(); sys.exit()

        # Occasional BG explosions
        if random.random() < 0.02:
            self.bg_explosions.append({
                'x': random.uniform(100, W-100),
                'y': random.uniform(100, H-200),
                'timer': 0.5,
                'color': random.choice([C.RED, C.ORANGE, C.YELLOW, C.CYAN, C.PURPLE])
            })
            self.particles.emit_explosion(
                random.uniform(100, W-100), random.uniform(100, H-200),
                random.choice([C.RED,C.ORANGE,C.PURPLE,C.CYAN]), count=20)

        surf = self.screen
        surf.fill(C.BG)
        self.starfield.draw(surf)
        self.particles.draw(surf)

        t = self.title_t

        # Decorative scan lines
        for y in range(0, H, 4):
            pygame.draw.line(surf, (0,0,0), (0,y), (W,y))
            # subtle

        # Animated title
        scale_y = int(5 * math.sin(t * 1.5))
        draw_glow_text(surf, "VOID", self.f_title, C.CYAN,
                       W//2 - 190, 180 + scale_y, glow_radius=20, glow_col=C.NEON_BLUE)
        draw_glow_text(surf, "RIFT", self.f_title, C.RED,
                       W//2 + 190, 180 + scale_y, glow_radius=20, glow_col=C.ORANGE)

        # Connecting energy between words
        mid_y = 170 + scale_y
        bolt_pts = [(W//2 - 80, mid_y)]
        bx = W//2 - 80
        while bx < W//2 + 80:
            bx += 10
            by = mid_y + random.randint(-15, 15)
            bolt_pts.append((bx, by))
            if len(bolt_pts) >= 2:
                pygame.draw.line(surf, C.WHITE, bolt_pts[-2], bolt_pts[-1], 2)

        # Subtitle
        draw_glow_text(surf, "DEEP SPACE ROGUELIKE COMBAT", self.f_sm,
                       C.GOLD, W//2, 300, glow_radius=6, glow_col=C.GOLD_DIM)
        draw_text(surf, "coded by @non G00nz", self.f_xs, C.GRAY, W//2, 335)

        # High score
        if self.high_score > 0:
            draw_text(surf, f"★ HIGH SCORE: {self.high_score:,} ★",
                      self.f_sm, C.GOLD, W//2, 380)

        self.btn_play.draw(surf)
        self.btn_exit.draw(surf)

        # Feature highlights
        features = ["5 SECTORS", "BOSS FIGHTS", "UPGRADE SYSTEM",
                    "8 WEAPONS", "COMBO SYSTEM", "4 SHIP CLASSES"]
        for i, ft in enumerate(features):
            fx = 140 + (i % 3) * 340
            fy = 680 + (i // 3) * 30
            draw_text(surf, f"◆ {ft}", self.f_xs, C.GRAY, fx, fy, center=False)

        # Version / controls hint
        draw_text(surf, "WASD/ARROWS: MOVE  |  CLICK/SPACE: FIRE  |  Q: SWITCH WEAPON  |  SHIFT: ABILITY",
                  self.f_xs, (50, 60, 80), W//2, H-20)

    # ═══════════════════════════════════════════════════════════
    #   SHIP SELECT
    # ═══════════════════════════════════════════════════════════
    def _ship_select(self, events, mx, my):
        self.btn_ship_l.update(mx, my)
        self.btn_ship_r.update(mx, my)
        self.btn_confirm.update(mx, my)

        for e in events:
            if self.btn_ship_l.clicked(e):
                self.selected_ship = (self.selected_ship - 1) % len(SHIP_CLASSES)
                self.play('click')
            if self.btn_ship_r.clicked(e):
                self.selected_ship = (self.selected_ship + 1) % len(SHIP_CLASSES)
                self.play('click')
            if self.btn_confirm.clicked(e):
                self.play('click')
                self.init_game(self.selected_ship)
                self.state = GS.GAMEPLAY
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_LEFT:  self.selected_ship = (self.selected_ship-1)%len(SHIP_CLASSES)
                if e.key == pygame.K_RIGHT: self.selected_ship = (self.selected_ship+1)%len(SHIP_CLASSES)
                if e.key == pygame.K_RETURN:
                    self.init_game(self.selected_ship); self.state = GS.GAMEPLAY

        surf = self.screen
        surf.fill(C.BG)
        self.starfield.draw(surf)

        sc = SHIP_CLASSES[self.selected_ship]

        draw_glow_text(surf, "SELECT YOUR VESSEL", self.f_big,
                       C.TITLE_GOLD if hasattr(C,'TITLE_GOLD') else C.GOLD,
                       W//2, 60, glow_radius=10, glow_col=C.ORANGE)
        draw_text(surf, f"[ {self.selected_ship+1} / {len(SHIP_CLASSES)} ]",
                  self.f_sm, C.GRAY, W//2, 110)

        # Ship preview
        temp_player = Player(sc)
        temp_player.x = W//2; temp_player.y = 360
        temp_player._draw_ship_shape(surf, W//2, 360, sc.color, sc.special_shape)

        # Spinning particles around ship
        for i in range(8):
            a = math.radians(i*45 + self.title_t * 80)
            px2 = W//2 + math.cos(a)*80
            py2 = 360 + math.sin(a)*80
            pygame.draw.circle(surf, sc.color, (int(px2), int(py2)), 3)

        # Ship name
        draw_glow_text(surf, sc.name, self.f_big, sc.color,
                       W//2, 200, glow_radius=12, glow_col=sc.color)
        draw_text(surf, sc.desc, self.f_sm, C.WHITE, W//2, 245)

        # Stats panel
        panel_x = W//2 - 480; panel_y = 460
        panel_w = 960; panel_h = 180

        bg = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(bg, (*C.DARK, 220), (0,0,panel_w,panel_h), border_radius=12)
        surf.blit(bg, (panel_x, panel_y))
        pygame.draw.rect(surf, sc.color, (panel_x, panel_y, panel_w, panel_h),
                         2, border_radius=12)

        stats = [
            ("HP",       sc.hp,         200, C.GREEN),
            ("SHIELD",   sc.shield,     150, C.CYAN),
            ("SPEED",    sc.speed,      6.0, C.YELLOW),
            ("FIRE RATE",sc.fire_rate,  2.0, C.ORANGE),
        ]
        for i, (label, val, max_v, col) in enumerate(stats):
            sx = panel_x + 30 + i * 240
            sy = panel_y + 25
            draw_text(surf, label, self.f_xs, C.GRAY, sx+70, sy, center=False)
            draw_bar(surf, sx, sy+20, 140, 14, val, max_v, col, glow=True)
            draw_text(surf, f"{val}", self.f_xs, C.WHITE, sx+150, sy+20, center=False)

        # Weapons
        draw_text(surf, "WEAPONS:", self.f_xs, C.GRAY, panel_x+30, panel_y+75, center=False)
        for i, wt in enumerate(sc.weapons):
            col_w = WEAPON_DATA[wt]["color"]
            draw_text(surf, f"• {wt.value}", self.f_xs, col_w,
                      panel_x + 30 + i*310, panel_y+95, center=False)

        # Ability
        draw_text(surf, f"ABILITY: {sc.ability_name}", self.f_sm, C.PURPLE,
                  panel_x+30, panel_y+125, center=False)
        draw_text(surf, sc.ability_desc, self.f_xs, C.GRAY,
                  panel_x+30, panel_y+150, center=False)

        self.btn_ship_l.draw(surf)
        self.btn_ship_r.draw(surf)
        self.btn_confirm.draw(surf)

        # Ship dots
        for i in range(len(SHIP_CLASSES)):
            col_d = SHIP_CLASSES[i].color if i==self.selected_ship else C.GRAY
            pygame.draw.circle(surf, col_d, (W//2 - (len(SHIP_CLASSES)-1)*15 + i*30, 670), 7)

    # ═══════════════════════════════════════════════════════════
    #   UPGRADE SCREEN
    # ═══════════════════════════════════════════════════════════
    def _upgrade_screen(self, events, mx, my):
        self.btn_launch.update(mx, my)
        for e in events:
            if self.btn_launch.clicked(e) or (e.type==pygame.KEYDOWN and e.key==pygame.K_RETURN):
                self.play('click')
                self._start_next_wave()
                self.state = GS.GAMEPLAY
            # Click upgrade
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                for i, upg in enumerate(UPGRADES_CATALOG):
                    btn_rect = self._upg_btn_rect(i)
                    if btn_rect.collidepoint(e.pos):
                        self._buy_upgrade(upg)

        surf = self.screen
        surf.fill(C.BG)
        self.starfield.draw(surf)

        p = self.player
        sector_cfg = SECTOR_CONFIG.get(self.sector, SECTOR_CONFIG[1])

        draw_glow_text(surf, "UPGRADE HANGAR", self.f_big, C.GOLD,
                       W//2, 50, glow_radius=10, glow_col=C.GOLD_DIM)
        draw_text(surf, f"SECTOR {self.sector}: {sector_cfg['name']}  |  WAVE {self.wave_in_sector}",
                  self.f_sm, C.GRAY, W//2, 95)
        draw_text(surf, f"CREDITS: {p.credits}", self.f_med, C.PURPLE, W//2, 130)
        draw_text(surf, f"SCORE: {p.score:,}  |  COMBO BEST: x{p.max_combo}",
                  self.f_sm, C.CYAN, W//2, 165)

        # Upgrades grid (2 columns)
        for i, upg in enumerate(UPGRADES_CATALOG):
            rect = self._upg_btn_rect(i)
            level = p.upgrades.get(upg["id"], 0)
            cost  = upg["base_cost"] * (level+1)
            maxed = level >= upg["max_level"]
            can_buy = p.credits >= cost and not maxed

            # Panel
            bg_col = (15, 20, 40) if can_buy else (10, 10, 20)
            hover  = rect.collidepoint(mx, my)
            if hover and can_buy: bg_col = (25, 30, 60)

            bg = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            pygame.draw.rect(bg, (*bg_col, 230), (0,0,rect.w,rect.h), border_radius=10)
            surf.blit(bg, rect.topleft)
            border_col = upg["color"] if can_buy else C.GRAY
            pygame.draw.rect(surf, border_col, rect, 2, border_radius=10)

            # Name
            draw_text(surf, upg["name"], self.f_sm, upg["color"],
                      rect.x+8, rect.y+16, center=False)
            # Desc
            draw_text(surf, upg["desc"], self.f_xs, C.GRAY,
                      rect.x+8, rect.y+38, center=False)
            # Level pips
            for lv in range(upg["max_level"]):
                pc = upg["color"] if lv < level else C.DARK
                pygame.draw.circle(surf, pc, (rect.x+8+lv*16, rect.y+60), 6)
                pygame.draw.circle(surf, C.GRAY, (rect.x+8+lv*16, rect.y+60), 6, 1)

            # Cost / maxed
            if maxed:
                draw_text(surf, "MAXED", self.f_xs, C.GOLD,
                          rect.right-50, rect.y+16, center=False)
            else:
                cost_col = C.GREEN if can_buy else C.RED
                draw_text(surf, f"${cost}", self.f_sm, cost_col,
                          rect.right-55, rect.y+16, center=False)

        # Player stats panel
        stats_x, stats_y = 50, 560
        pygame.draw.rect(surf, C.PANEL, (stats_x, stats_y, 380, 180), border_radius=10)
        pygame.draw.rect(surf, C.GRAY, (stats_x, stats_y, 380, 180), 1, border_radius=10)
        draw_text(surf, "SHIP STATUS", self.f_sm, C.CYAN, stats_x+190, stats_y+18)

        stat_rows = [
            ("HP",      p.hp, p.max_hp, C.GREEN),
            ("SHIELD",  p.shield, p.max_shield, C.CYAN),
        ]
        for si, (lbl, val, mx_v, col) in enumerate(stat_rows):
            sy = stats_y + 44 + si*40
            draw_text(surf, lbl, self.f_xs, C.GRAY, stats_x+12, sy, center=False)
            draw_bar(surf, stats_x+65, sy, 250, 16, val, mx_v, col, glow=True)
            draw_text(surf, f"{int(val)}/{int(mx_v)}", self.f_xs, C.WHITE,
                      stats_x+325, sy+1, center=False)

        draw_text(surf, f"WEAPON: {p.active_weapon.value}", self.f_xs, C.YELLOW,
                  stats_x+12, stats_y+130, center=False)
        draw_text(surf, f"KILLS: {p.kills}", self.f_xs, C.WHITE,
                  stats_x+200, stats_y+130, center=False)

        # Weapon list
        wep_x = W - 430; wep_y = 560
        pygame.draw.rect(surf, C.PANEL, (wep_x, wep_y, 380, 180), border_radius=10)
        pygame.draw.rect(surf, C.GRAY, (wep_x, wep_y, 380, 180), 1, border_radius=10)
        draw_text(surf, "ARSENAL", self.f_sm, C.PURPLE, wep_x+190, wep_y+18)
        for wi, wt in enumerate(p.weapons):
            wd = WEAPON_DATA[wt]
            active = (wi == p.active_weapon_idx)
            col_w = wd["color"] if active else C.GRAY
            prefix = "▶ " if active else "  "
            draw_text(surf, f"{prefix}{wt.value}  DMG:{wd['dmg']}",
                      self.f_xs, col_w, wep_x+12, wep_y+44+wi*28, center=False)

        self.btn_launch.draw(surf)

    def _upg_btn_rect(self, idx):
        cols = 3; col_i = idx % cols; row_i = idx // cols
        w_per = 370; h_per = 90; pad = 12
        x = 50 + col_i * (w_per + pad)
        y = 200 + row_i * (h_per + pad)
        return pygame.Rect(x, y, w_per, h_per)

    def _buy_upgrade(self, upg):
        p = self.player
        level = p.upgrades.get(upg["id"], 0)
        if level >= upg["max_level"]:
            return
        cost = upg["base_cost"] * (level+1)
        if p.credits >= cost:
            p.credits -= cost
            p.upgrades[upg["id"]] = level + 1
            self.play('powerup')
            # Apply immediate effects
            if upg["id"] == "hp":
                bonus = int(p.cls.hp * 0.2)
                p.max_hp += bonus; p.hp = min(p.hp + bonus, p.max_hp)
            if upg["id"] == "shield":
                bonus = int(p.cls.shield * 0.3)
                p.max_shield += bonus; p.shield = min(p.shield+bonus, p.max_shield)

    def _start_next_wave(self):
        self.wave_in_sector += 1
        if self.wave_in_sector > self.wave_mgr.waves_per_sector:
            self.wave_in_sector = 1
            self.sector += 1
            if self.sector > 5:
                self.state = GS.VICTORY
                return
        self.enemies = []; self.boss_list = []; self.bullets = []
        self.enemy_bullets = []
        self.wave_mgr.start_wave(self.wave_in_sector, self.sector)
        self.particles.emit_warp(self.player.x, self.player.y)

    # ═══════════════════════════════════════════════════════════
    #   GAMEPLAY
    # ═══════════════════════════════════════════════════════════
    def _gameplay(self, events, mx, my):
        keys = pygame.key.get_pressed()
        p = self.player

        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    self.state = GS.PAUSED
                if e.key == pygame.K_q:
                    p.switch_weapon()
                    self.play('click')
                if e.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                    p.use_ability(self.bullets, self.enemies, self.particles)
                    self.play('warp')

        # Fire
        fire = (keys[pygame.K_SPACE] or
                keys[pygame.K_z] or
                pygame.mouse.get_pressed()[0])
        if fire:
            p.fire(self.bullets, self.enemies + self.boss_list, self.particles)
            wt = p.active_weapon
            if wt == WeaponType.LASER:
                self.play('laser')
            elif wt in (WeaponType.PLASMA, WeaponType.RAILGUN):
                self.play('plasma')

        # Update player
        p.update(keys, self.dt)

        # Wave manager
        spawned = self.wave_mgr.update(self.dt, self.enemies, self.boss_list)
        if spawned and isinstance(spawned, Boss):
            self.state = GS.BOSS_INTRO
            self.boss_intro_timer = 3.0
            self.boss_intro_name = spawned.name
            self.play('boss')
            return

        # Update enemies
        for en in self.enemies[:]:
            en.update(self.dt, p.x, p.y, self.enemy_bullets, self.particles)
            if not en.alive:
                self._enemy_killed(en)
                self.enemies.remove(en)

        # Update bosses
        for b in self.boss_list[:]:
            old_phase = b.phase
            b.update(self.dt, p.x, p.y, self.enemy_bullets, self.particles)
            if b.check_phase() and b.alive:
                self._add_shake(15)
                self._add_flash(b.color, 0.4)
                self.particles.emit_explosion(b.x, b.y, b.color, C.WHITE, 50)
            if not b.alive:
                self._boss_killed(b)
                self.boss_list.remove(b)

        # Update player bullets
        for bul in self.bullets[:]:
            bul.update(self.enemies + self.boss_list)
            if not bul.alive:
                self.bullets.remove(bul)
                continue

            # Collision with enemies
            for en in self.enemies[:]:
                if not en.alive: continue
                d = math.hypot(bul.x-en.x, bul.y-en.y)
                if d < en.size + bul.size:
                    en.take_damage(bul.dmg)
                    self.particles.emit_laser_impact(bul.x, bul.y, bul.color)
                    p.shots_hit += 1
                    # Chain lightning
                    if bul.weapon_type == WeaponType.CHAIN and bul.chain_count > 0:
                        self._chain_to_next(bul, en, self.enemies)
                    if not bul.pierce:
                        bul.alive = False
                        break

            # Collision with boss
            for b in self.boss_list[:]:
                if not b.alive: continue
                d = math.hypot(bul.x-b.x, bul.y-b.y)
                if d < b.size + bul.size:
                    b.take_damage(bul.dmg)
                    self.particles.emit_laser_impact(bul.x, bul.y, bul.color)
                    p.shots_hit += 1
                    scored = p.add_score(bul.dmg * 2)
                    self.float_texts.append(FloatText(
                        f"+{scored}", bul.x, bul.y, -2, C.YELLOW, 0.8, 0.8, 16))
                    if not bul.pierce:
                        bul.alive = False
                        break

        # Update enemy bullets
        for bul in self.enemy_bullets[:]:
            bul.update()
            if not bul.alive:
                self.enemy_bullets.remove(bul)
                continue
            # Hit player
            d = math.hypot(bul.x-p.x, bul.y-p.y)
            if d < 20 + bul.size:
                dmg = p.take_damage(bul.dmg)
                if dmg > 0:
                    self.particles.emit(p.x, p.y, C.RED, count=8, speed=3)
                    self._add_shake(6)
                    self._add_flash(C.RED, 0.25)
                    self.play('damage')
                bul.alive = False
                self.enemy_bullets.remove(bul) if bul in self.enemy_bullets else None

        # Powerup collection
        for pw in self.powerups[:]:
            pw.update(self.dt)
            if not pw.alive:
                self.powerups.remove(pw)
                continue
            d = math.hypot(pw.x-p.x, pw.y-p.y)
            if d < 28:
                self._collect_powerup(pw, p)
                self.powerups.remove(pw)

        # Float text update
        for ft in self.float_texts[:]:
            ft.update()
            if ft.life <= 0:
                self.float_texts.remove(ft)

        # Chain bolt decay
        for cb in self.chain_bolts[:]:
            cb['timer'] -= self.dt
            if cb['timer'] <= 0:
                self.chain_bolts.remove(cb)

        # Player dead?
        if p.hp <= 0:
            self._add_flash(C.RED, 1.0)
            self._add_shake(20)
            self.particles.emit_explosion(p.x, p.y, C.CYAN, C.WHITE, 60)
            if p.score > self.high_score:
                self.high_score = p.score
            self.state = GS.GAME_OVER
            return

        # Wave complete?
        if self.wave_mgr.wave_complete and not self.boss_list and not self.enemies:
            self._wave_complete()

        # Draw
        self._draw_gameplay()

    def _chain_to_next(self, bul, last_hit, enemies):
        """Propagate chain lightning."""
        candidates = [e for e in enemies if e.alive and e != last_hit
                      and not e.chained]
        if candidates:
            nearest = min(candidates, key=lambda e: math.hypot(e.x-last_hit.x, e.y-last_hit.y))
            d = math.hypot(nearest.x-last_hit.x, nearest.y-last_hit.y)
            if d < 250:
                nearest.take_damage(bul.dmg // 2)
                nearest.chained = True
                self.chain_bolts.append({
                    'x1': last_hit.x, 'y1': last_hit.y,
                    'x2': nearest.x,  'y2': nearest.y,
                    'timer': 0.2, 'color': C.PINK,
                    'chain_left': bul.chain_count - 1,
                    'last': nearest,
                })
                bul.chain_count -= 1

    def _enemy_killed(self, en):
        p = self.player
        pts = p.add_score(en.score)
        p.credits += en.credits
        p.kills += 1

        self.particles.emit_explosion(en.x, en.y, en.color,
                                      secondary=C.YELLOW, count=25)
        self._add_shake(4)
        self.play('explode')

        self.float_texts.append(FloatText(
            f"+{pts}", en.x, en.y-20, -2.5, C.YELLOW, 1.2, 1.2,
            20 if p.combo_mult > 1 else 16, bold=(p.combo_mult > 2)))

        if p.combo_mult >= 2:
            self.float_texts.append(FloatText(
                f"x{p.combo_mult:.1f} COMBO!", en.x, en.y-50, -1.5,
                C.GOLD, 1.0, 1.0, 22, True))

        # Drop chance
        drop_roll = random.random()
        if drop_roll < 0.15:
            self.powerups.append(Powerup(en.x, en.y))
        elif drop_roll < 0.25:
            self.powerups.append(Powerup(en.x, en.y, PowerupType.CREDIT))

        # Combo sound threshold
        if p.combo in (5, 10, 20, 30, 50):
            self.play('combo')

    def _boss_killed(self, b):
        p = self.player
        pts = p.add_score(b.score)
        p.credits += b.credits
        p.kills += 1

        for _ in range(5):
            self.particles.emit_explosion(
                b.x + random.uniform(-80,80),
                b.y + random.uniform(-80,80),
                b.color, C.WHITE, 30)

        self._add_shake(25)
        self._add_flash(C.WHITE, 0.8)
        self.play('boss')

        self.float_texts.append(FloatText(
            f"BOSS DESTROYED! +{pts:,}", b.x, b.y-40, -2.0,
            C.GOLD, 3.0, 3.0, 32, True))

        # Guaranteed powerup storm
        for _ in range(8):
            px2 = b.x + random.uniform(-120,120)
            py2 = b.y + random.uniform(-60,60)
            self.powerups.append(Powerup(px2, py2))

    def _collect_powerup(self, pw, p):
        self.particles.emit_pickup(pw.x, pw.y, pw.color)
        self.play('powerup')

        pt = pw.ptype
        if pt == PowerupType.HEALTH:
            heal = int(p.max_hp * 0.25)
            p.hp = min(p.max_hp, p.hp + heal)
            self.float_texts.append(FloatText(f"+{heal} HP", pw.x, pw.y, -2, C.GREEN, 1.2, 1.2, 20, True))
        elif pt == PowerupType.SHIELD:
            p.shield = p.max_shield
            self.float_texts.append(FloatText("SHIELD FULL!", pw.x, pw.y, -2, C.CYAN, 1.2, 1.2, 20, True))
        elif pt == PowerupType.WEAPON_UP:
            p.active_powerups.append({'type':'dmg_boost','timer':10.0,'mult':1.5})
            p.upgrades["damage"] = min(5, p.upgrades["damage"] + 1)
            self.float_texts.append(FloatText("WEAPON UP!", pw.x, pw.y, -2, C.YELLOW, 1.2, 1.2, 22, True))
        elif pt == PowerupType.SCORE_MULT:
            p.combo += 10
            p.combo_timer = 8.0
            self.float_texts.append(FloatText("SCORE FRENZY!", pw.x, pw.y, -2, C.GOLD, 1.5, 1.5, 24, True))
        elif pt == PowerupType.INVINCIBLE:
            p.invincible = True
            p.invincible_t = 5.0
            self.float_texts.append(FloatText("INVINCIBLE!", pw.x, pw.y, -2, C.WHITE, 1.5, 1.5, 24, True))
        elif pt == PowerupType.BOMB:
            # AOE clear
            for en in self.enemies[:]:
                if math.hypot(en.x-p.x, en.y-p.y) < 350:
                    en.hp = 0; en.alive = False
                    self.particles.emit_explosion(en.x, en.y, C.RED, count=15)
            self.float_texts.append(FloatText("NOVA BOMB!", pw.x, pw.y, -2, C.RED, 1.2, 1.2, 24, True))
            self._add_shake(12)
            self._add_flash(C.ORANGE, 0.5)
        elif pt == PowerupType.CREDIT:
            bonus = random.randint(30, 80)
            p.credits += bonus
            self.float_texts.append(FloatText(f"+${bonus}", pw.x, pw.y, -2, C.PURPLE, 1.0, 1.0, 20))
        elif pt == PowerupType.AMMO:
            p.weapon_cd = 0.0
            p.active_powerups.append({'type':'rapid','timer':8.0})
            self.float_texts.append(FloatText("HYPER AMMO!", pw.x, pw.y, -2, C.ORANGE, 1.2, 1.2, 22, True))

    def _wave_complete(self):
        p = self.player
        p.credits += 50 + self.sector * 20 + self.wave_in_sector * 10
        # Show upgrade screen between waves (not after boss sectors go straight)
        self.state = GS.UPGRADE

    def _draw_gameplay(self):
        surf = self.screen
        ox, oy = int(self.shake_x), int(self.shake_y)
        surf.fill(C.BG)
        self.starfield.draw(surf)

        # Game objects
        for pw in self.powerups: pw.draw(surf)
        for en in self.enemies: en.draw(surf)
        for b in self.boss_list: b.draw(surf)

        # Chain bolts
        for cb in self.chain_bolts:
            alpha = int(255 * cb['timer'] / 0.2)
            steps = 8
            pts = [(cb['x1'], cb['y1'])]
            for i in range(1, steps):
                t2 = i / steps
                mx2 = cb['x1'] + (cb['x2']-cb['x1'])*t2
                my2 = cb['y1'] + (cb['y2']-cb['y1'])*t2
                jitter = 15 * (1 - t2)
                pts.append((mx2 + random.uniform(-jitter, jitter),
                             my2 + random.uniform(-jitter, jitter)))
            pts.append((cb['x2'], cb['y2']))
            for j in range(len(pts)-1):
                pygame.draw.line(surf, cb['color'],
                                 (int(pts[j][0]), int(pts[j][1])),
                                 (int(pts[j+1][0]), int(pts[j+1][1])), 2)

        # Bullets
        for bul in self.bullets:     bul.draw(surf, self.particles)
        for bul in self.enemy_bullets: bul.draw(surf, self.particles)

        # Player
        self.player.draw(surf, self.particles, self.dt)

        # Particles
        self.particles.draw(surf)

        # Float texts
        for ft in self.float_texts: ft.draw(surf)

        # Flash overlay
        if self.flash_alpha > 0:
            fs = pygame.Surface((W, H), pygame.SRCALPHA)
            a = int(self.flash_alpha * 180)
            fs.fill((*self.flash_color, a))
            surf.blit(fs, (0,0))

        # HUD
        self._draw_hud(surf)

    def _draw_hud(self, surf):
        p = self.player
        t = self.title_t

        # ── Left panel ──
        panel = pygame.Rect(10, 10, 280, 140)
        bg = pygame.Surface((280,140), pygame.SRCALPHA)
        pygame.draw.rect(bg, (5,8,25,200), (0,0,280,140), border_radius=10)
        surf.blit(bg, panel.topleft)
        pygame.draw.rect(surf, p.cls.color, panel, 1, border_radius=10)

        draw_text(surf, p.cls.name, self.f_xs, p.cls.color, 15, 20, center=False)

        draw_text(surf, "HP", self.f_xs, C.GRAY, 15, 44, center=False)
        draw_bar(surf, 45, 42, 220, 12, p.hp, p.max_hp, C.GREEN, glow=True,
                 label=f"{int(p.hp)}/{int(p.max_hp)}", font=self.f_xs)

        draw_text(surf, "SH", self.f_xs, C.GRAY, 15, 64, center=False)
        draw_bar(surf, 45, 62, 220, 12, p.shield, p.max_shield, C.CYAN, glow=True,
                 label=f"{int(p.shield)}/{int(p.max_shield)}", font=self.f_xs)

        # Weapon
        wt = p.active_weapon
        wd = WEAPON_DATA[wt]
        wname = wt.value
        draw_text(surf, f"WPN: {wname}", self.f_xs, wd["color"], 15, 88, center=False)

        # Weapon cooldown bar
        if p.weapon_cd > 0:
            base_cd = wd["cd"]/(p.fire_rate_mult*(1+p.upgrades["fire_rate"]*0.2))
            f2 = 1 - p.weapon_cd/base_cd
            draw_bar(surf, 15, 104, 250, 6, f2, 1.0, wd["color"])

        # Ability
        ability_col = C.PURPLE if p.ability_cd <= 0 else C.GRAY
        draw_text(surf, f"[SHIFT] {p.cls.ability_name}", self.f_xs, ability_col,
                  15, 120, center=False)
        if p.ability_cd > 0:
            draw_bar(surf, 15, 134, 250, 6, p.cls.ability_cd-p.ability_cd, p.cls.ability_cd,
                     C.PURPLE)

        # ── Top center: score, combo ──
        draw_glow_text(surf, f"{p.score:,}", self.f_med, C.WHITE, W//2, 28,
                       glow_radius=6, glow_col=C.CYAN_DIM)

        if p.combo_mult > 1 or p.combo > 0:
            combo_col = C.GOLD if p.combo_mult >= 3 else C.YELLOW
            draw_text(surf, f"x{p.combo_mult:.1f} COMBO [{p.combo}]",
                      self.f_sm, combo_col, W//2, 58)
            # Combo timer bar
            ctf = max(0, p.combo_timer / 3.5)
            draw_bar(surf, W//2-100, 74, 200, 4, ctf, 1.0, combo_col)

        # ── Right panel: sector/wave ──
        rpanel = pygame.Rect(W-220, 10, 210, 100)
        rb = pygame.Surface((210,100), pygame.SRCALPHA)
        pygame.draw.rect(rb, (5,8,25,200), (0,0,210,100), border_radius=10)
        surf.blit(rb, rpanel.topleft)
        pygame.draw.rect(surf, C.CYAN_DIM, rpanel, 1, border_radius=10)

        sec_cfg = SECTOR_CONFIG.get(self.sector, SECTOR_CONFIG[1])
        draw_text(surf, f"SECTOR {self.sector}", self.f_sm, C.CYAN, W-115, 28)
        draw_text(surf, sec_cfg["name"], self.f_xs, C.GRAY, W-115, 50)
        draw_text(surf, f"WAVE {self.wave_in_sector}/{self.wave_mgr.waves_per_sector}",
                  self.f_sm, C.WHITE, W-115, 72)

        # Boss HP bar (if boss alive)
        if self.boss_list:
            b = self.boss_list[0]
            bw = 500; bh = 20
            bx = (W-bw)//2; by = H-50
            pygame.draw.rect(surf, C.RED_DARK, (bx-2, by-2, bw+4, bh+4), border_radius=6)
            hp_f = max(0, b.hp/b.max_hp)
            bc = C.RED if hp_f < 0.3 else C.ORANGE if hp_f < 0.6 else C.YELLOW
            draw_bar(surf, bx, by, bw, bh, b.hp, b.max_hp, bc, glow=True)
            draw_text(surf, f"☠ {b.name}  {b.hp}/{b.max_hp}", self.f_xs, C.WHITE,
                      bx+bw//2, by+bh//2)
            # Phase pips
            for pi in range(b.num_phases):
                pc = C.YELLOW if pi < b.phase else C.GRAY
                pygame.draw.circle(surf, pc, (bx+50+pi*100, by-12), 6)

        # Credits display
        draw_text(surf, f"${p.credits}", self.f_xs, C.PURPLE, W-30, H-20)

        # Minimap enemies
        mm_x, mm_y, mm_w, mm_h = W-90, H-80, 80, 60
        mm = pygame.Surface((mm_w, mm_h), pygame.SRCALPHA)
        pygame.draw.rect(mm, (5,8,25,180), (0,0,mm_w,mm_h), border_radius=4)
        pygame.draw.rect(mm, C.GRAY, (0,0,mm_w,mm_h), 1, border_radius=4)
        # Player dot
        px2 = int(p.x / W * mm_w); py2 = int(p.y / H * mm_h)
        pygame.draw.circle(mm, C.CYAN, (px2, py2), 3)
        # Enemy dots
        for en in self.enemies:
            ex = int(en.x / W * mm_w); ey = int(en.y / H * mm_h)
            pygame.draw.circle(mm, en.color, (ex, ey), 2)
        for b in self.boss_list:
            bx2 = int(b.x/W*mm_w); by2 = int(b.y/H*mm_h)
            pygame.draw.circle(mm, b.color, (bx2, by2), 4)
        surf.blit(mm, (mm_x, mm_y))

        # Controls reminder
        draw_text(surf, "[Q] WEAPON  [SHIFT] ABILITY  [ESC] PAUSE",
                  self.f_xs, (40,50,70), W//2, H-12)

    # ═══════════════════════════════════════════════════════════
    #   BOSS INTRO
    # ═══════════════════════════════════════════════════════════
    def _boss_intro(self, events):
        for e in events:
            if e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE:
                self.boss_intro_timer = 0

        self.boss_intro_timer -= self.dt
        if self.boss_intro_timer <= 0:
            self.state = GS.GAMEPLAY
            return

        self._draw_gameplay()
        surf = self.screen

        # Dramatic overlay
        overlay = pygame.Surface((W,H), pygame.SRCALPHA)
        alpha = min(180, int((3.0-self.boss_intro_timer)/3.0 * 180))
        overlay.fill((0,0,0,120))
        surf.blit(overlay, (0,0))

        t = self.title_t
        pulse = abs(math.sin(t*4))

        draw_glow_text(surf, "⚠  BOSS ENCOUNTERED  ⚠",
                       self.f_big, C.RED, W//2, H//2-60,
                       glow_radius=16, glow_col=(100,0,0))
        draw_glow_text(surf, self.boss_intro_name, self.f_big,
                       C.YELLOW, W//2, H//2,
                       glow_radius=int(8+6*pulse), glow_col=C.ORANGE)
        draw_text(surf, "PREPARE FOR COMBAT", self.f_med, C.WHITE, W//2, H//2+70)
        draw_text(surf, f"[ SPACE ] to skip", self.f_xs, C.GRAY, W//2, H//2+110)

        # Dramatic scan lines
        for yi in range(0, H, 3):
            if (yi//3 + int(t*20)) % 3 == 0:
                pygame.draw.line(surf, (255,0,0,30), (0,yi), (W,yi))

    # ═══════════════════════════════════════════════════════════
    #   PAUSE
    # ═══════════════════════════════════════════════════════════
    def _paused(self, events, mx, my):
        self.btn_resume.update(mx, my)
        self.btn_quit_p.update(mx, my)

        for e in events:
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                self.state = GS.GAMEPLAY
            if self.btn_resume.clicked(e):
                self.play('click'); self.state = GS.GAMEPLAY
            if self.btn_quit_p.clicked(e):
                self.play('click'); self.state = GS.TITLE

        self._draw_gameplay()
        surf = self.screen

        overlay = pygame.Surface((W,H), pygame.SRCALPHA)
        overlay.fill((0,0,10,170))
        surf.blit(overlay, (0,0))

        draw_glow_text(surf, "PAUSED", self.f_big, C.CYAN, W//2, 240,
                       glow_radius=12, glow_col=C.CYAN_DIM)

        p = self.player
        draw_text(surf, f"SCORE: {p.score:,}", self.f_sm, C.WHITE, W//2, 300)

        stats_text = [
            f"KILLS: {p.kills}",
            f"CREDITS: ${p.credits}",
            f"MAX COMBO: x{p.max_combo}",
            f"SECTOR: {self.sector}  WAVE: {self.wave_in_sector}",
        ]
        for i, st in enumerate(stats_text):
            draw_text(surf, st, self.f_xs, C.GRAY, W//2, 330 + i*22)

        self.btn_resume.draw(surf)
        self.btn_quit_p.draw(surf)

    # ═══════════════════════════════════════════════════════════
    #   GAME OVER
    # ═══════════════════════════════════════════════════════════
    def _game_over(self, events, mx, my):
        self.btn_retry.update(mx, my)
        self.btn_menu.update(mx, my)

        for e in events:
            if self.btn_retry.clicked(e):
                self.play('click')
                self.init_game(self.selected_ship)
                self.state = GS.GAMEPLAY
            if self.btn_menu.clicked(e):
                self.play('click')
                self.state = GS.TITLE

        if random.random() < 0.04:
            self.particles.emit_explosion(
                random.uniform(100,W-100), random.uniform(100,H-300),
                C.RED, count=15)

        surf = self.screen
        surf.fill(C.BG)
        self.starfield.draw(surf)
        self.particles.draw(surf)

        t = self.title_t

        draw_glow_text(surf, "SHIP DESTROYED", self.f_big, C.RED,
                       W//2, 150, glow_radius=16, glow_col=(100,0,0))

        p = self.player
        new_hs = p.score >= self.high_score

        if new_hs:
            draw_glow_text(surf, "✦ NEW HIGH SCORE! ✦", self.f_med, C.GOLD,
                           W//2, 220, glow_radius=10, glow_col=C.ORANGE)
        draw_text(surf, f"SCORE: {p.score:,}", self.f_med, C.WHITE, W//2, 260 if not new_hs else 260)

        # Stats grid
        stats = [
            ("KILLS",        str(p.kills)),
            ("MAX COMBO",    f"x{p.max_combo}"),
            ("ACCURACY",     f"{int(p.shots_hit/max(1,p.shots_fired)*100)}%"),
            ("SECTOR",       f"{self.sector}"),
            ("WAVE",         f"{self.wave_in_sector}"),
            ("CREDITS EARNED", f"${p.credits}"),
        ]
        for i, (label, val) in enumerate(stats):
            cx_s = W//2 - 200 + (i%2)*400
            cy_s = 310 + (i//2)*36
            draw_text(surf, f"{label}:", self.f_xs, C.GRAY, cx_s, cy_s, center=False)
            draw_text(surf, val, self.f_sm, C.WHITE, cx_s+200, cy_s)

        self.btn_retry.draw(surf)
        self.btn_menu.draw(surf)

        draw_text(surf, f"HIGH SCORE: {self.high_score:,}", self.f_xs, C.GOLD,
                  W//2, H-30)

    # ═══════════════════════════════════════════════════════════
    #   VICTORY
    # ═══════════════════════════════════════════════════════════
    def _victory(self, events, mx, my):
        self.btn_menu.update(mx, my)
        for e in events:
            if self.btn_menu.clicked(e) or (e.type==pygame.KEYDOWN and e.key==pygame.K_RETURN):
                if self.player.score > self.high_score:
                    self.high_score = self.player.score
                self.state = GS.TITLE

        # Fireworks
        if random.random() < 0.08:
            col = random.choice([C.YELLOW,C.CYAN,C.GREEN,C.PURPLE,C.PINK,C.ORANGE])
            self.particles.emit_explosion(random.uniform(150,W-150),
                                          random.uniform(100,400), col, count=35)

        surf = self.screen
        surf.fill(C.BG)
        self.starfield.draw(surf)
        self.particles.draw(surf)

        t = self.title_t
        pulse = abs(math.sin(t*3))
        r_size = int(10 + 6*pulse)

        draw_glow_text(surf, "VOID RIFT DEFEATED!", self.f_big,
                       C.GOLD, W//2, 130, glow_radius=20, glow_col=C.ORANGE)
        draw_text(surf, "YOU SAVED THE GALAXY", self.f_med, C.WHITE, W//2, 205)

        p = self.player
        if p.score >= self.high_score:
            draw_glow_text(surf, f"✦ HIGH SCORE: {p.score:,} ✦",
                           self.f_med, C.GOLD, W//2, 260, glow_radius=8)
        else:
            draw_text(surf, f"FINAL SCORE: {p.score:,}", self.f_med, C.WHITE, W//2, 260)

        # Medals
        medals = []
        if p.kills >= 100:    medals.append(("⚔ VETERAN",       "100+ kills",        C.RED))
        if p.max_combo >= 20: medals.append(("⚡ COMBO MASTER",  "20+ combo",         C.YELLOW))
        accuracy = p.shots_hit/max(1,p.shots_fired)
        if accuracy >= 0.7:   medals.append(("🎯 SHARPSHOOTER", f"{int(accuracy*100)}% accuracy", C.CYAN))
        if p.credits >= 500:  medals.append(("💰 PROFITEER",    "$500+ credits",      C.PURPLE))

        if medals:
            draw_text(surf, "MEDALS EARNED:", self.f_sm, C.GRAY, W//2, 320)
            for i, (m_name, m_desc, m_col) in enumerate(medals):
                draw_glow_text(surf, m_name, self.f_sm, m_col,
                               W//2, 355 + i*40, glow_radius=6)
                draw_text(surf, m_desc, self.f_xs, C.GRAY, W//2, 375+i*40)

        self.btn_menu.draw(surf)


# ═══════════════════════════════════════════════════════════════
#   ENTRY POINT
# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    game = VoidRift()
    game.run()
