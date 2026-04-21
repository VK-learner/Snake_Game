import random
import sys
import math
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path

import pygame

WINDOW_WIDTH = 960
WINDOW_HEIGHT = 720
GRID_SIZE = 24
GRID_COLS = 28
GRID_ROWS = 24
PLAY_WIDTH = GRID_COLS * GRID_SIZE
PLAY_HEIGHT = GRID_ROWS * GRID_SIZE
PLAY_LEFT = (WINDOW_WIDTH - PLAY_WIDTH) // 2
PLAY_TOP = 110
FPS = 60

MAX_HEARTS = 3
POINTS_PER_LEVEL = 100
RAT_POINTS = 10
FROG_POINTS = 5

# Snake body color per level (body, head)
LEVEL_COLORS = [
    ((57, 255, 20),   (148, 255, 84)),   # L1 neon green
    ((0, 200, 255),   (100, 230, 255)),   # L2 cyan
    ((180, 0, 255),   (220, 100, 255)),   # L3 purple
    ((255, 140, 0),   (255, 200, 80)),    # L4 orange
    ((255, 50, 50),   (255, 130, 130)),   # L5 red
    ((255, 255, 0),   (255, 255, 160)),   # L6 yellow
    ((0, 255, 180),   (100, 255, 220)),   # L7 teal
    ((255, 80, 200),  (255, 160, 230)),   # L8 pink
]


class GameState(Enum):
    HOME = auto()
    PLAYING = auto()
    PAUSED = auto()
    GAME_OVER = auto()
    RESPAWNING = auto()


@dataclass
class Button:
    label: str
    rect: pygame.Rect
    action: str


@dataclass
class FoodItem:
    cell: tuple
    food_type: str          # "rat" or "frog"
    points: int
    anim_timer: float = 0.0
    scale: float = 1.0


class SnakeGame:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Neon Snake")
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()

        self.title_font  = pygame.font.SysFont("verdana", 54, bold=True)
        self.large_font  = pygame.font.SysFont("verdana", 30, bold=True)
        self.medium_font = pygame.font.SysFont("verdana", 22, bold=True)
        self.small_font  = pygame.font.SysFont("consolas", 18)

        self.bg_top      = (8, 12, 26)
        self.bg_bottom   = (20, 44, 58)
        self.panel_color = (12, 18, 34)
        self.panel_border= (86, 195, 255)
        self.grid_color  = (34, 59, 77)
        self.text_color  = (237, 246, 255)
        self.muted_text  = (157, 187, 207)
        self.gold        = (255, 210, 90)
        self.heart_color = (255, 60, 90)
        self.obstacle_color = (180, 60, 60)
        self.obstacle_border= (255, 100, 80)

        # Pre-render gradient background once
        self.bg_surface = self._make_bg_surface()

        self._load_assets()

        self.state = GameState.HOME
        self.best_score = 0
        self.buttons: list[Button] = []
        self.resume_available = False
        self.respawn_timer = 0.0
        self.invincible_timer = 0.0  # brief flash after respawn

        self._init_game_state()
        self.reset_game(full=True)

    # ------------------------------------------------------------------ assets

    def _load_assets(self) -> None:
        asset_dir = Path(__file__).parent

        def load_img(name, size):
            p = asset_dir / name
            if p.exists():
                img = pygame.image.load(str(p)).convert_alpha()
                return pygame.transform.smoothscale(img, size)
            return None

        # snake.png is 512x512 — scale to fit one grid cell head (24x24)
        self.snake_head_img = load_img("snake.png", (GRID_SIZE - 2, GRID_SIZE - 2))
        self.rat_img_base   = load_img("rat.png",   (25, 25))
        self.frog_img_base  = load_img("frog.png",  (25, 25))

    # ------------------------------------------------------------------ bg

    def _make_bg_surface(self) -> pygame.Surface:
        surf = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        for y in range(WINDOW_HEIGHT):
            mix = y / WINDOW_HEIGHT
            color = (
                int(self.bg_top[0] * (1 - mix) + self.bg_bottom[0] * mix),
                int(self.bg_top[1] * (1 - mix) + self.bg_bottom[1] * mix),
                int(self.bg_top[2] * (1 - mix) + self.bg_bottom[2] * mix),
            )
            pygame.draw.line(surf, color, (0, y), (WINDOW_WIDTH, y))
        return surf

    # ------------------------------------------------------------------ init

    def _init_game_state(self) -> None:
        self.snake: list[tuple] = []
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.score = 0
        self.level = 1
        self.hearts = MAX_HEARTS
        self.move_delay = 0.12
        self.move_timer = 0.0
        self.food_items: list[FoodItem] = []
        self.obstacles: set[tuple] = set()
        self.snake_color, self.snake_head_color = LEVEL_COLORS[0]

    def reset_game(self, full: bool = False) -> None:
        """full=True resets score/level/hearts. full=False keeps them (respawn)."""
        if full:
            self._init_game_state()
        cx, cy = GRID_COLS // 2, GRID_ROWS // 2
        self.snake = [(cx - i, cy) for i in range(4)]
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.move_timer = 0.0
        if full:
            self.move_delay = 0.12
            self.obstacles = self._generate_obstacles(self.level)
            self.food_items = []
            self._spawn_food()
            self._spawn_food()
        self.resume_available = True

    def _level_color(self) -> tuple:
        idx = min(self.level - 1, len(LEVEL_COLORS) - 1)
        return LEVEL_COLORS[idx]

    # ------------------------------------------------------------------ obstacles

    def _generate_obstacles(self, level: int) -> set:
        """Level 1 = 0 obstacles. Each level adds 3 more random blocks."""
        count = (level - 1) * 3
        obs = set()
        center_safe = {(GRID_COLS // 2 + dx, GRID_ROWS // 2 + dy)
                       for dx in range(-4, 5) for dy in range(-4, 5)}
        attempts = 0
        while len(obs) < count and attempts < 2000:
            cell = (random.randint(1, GRID_COLS - 2), random.randint(1, GRID_ROWS - 2))
            if cell not in center_safe:
                obs.add(cell)
            attempts += 1
        return obs

    # ------------------------------------------------------------------ food

    def _free_cells(self) -> list:
        occupied = set(self.snake) | self.obstacles | {f.cell for f in self.food_items}
        return [(x, y) for x in range(GRID_COLS) for y in range(GRID_ROWS)
                if (x, y) not in occupied]

    def _spawn_food(self) -> None:
        free = self._free_cells()
        if not free:
            return
        cell = random.choice(free)
        food_type = random.choice(["rat", "frog"])
        points = RAT_POINTS if food_type == "rat" else FROG_POINTS
        self.food_items.append(FoodItem(cell=cell, food_type=food_type, points=points))

    # ------------------------------------------------------------------ run loop

    def run(self) -> None:
        while True:
            delta = min(self.clock.tick(FPS) / 1000.0, 0.05)
            self.handle_events()
            if self.state == GameState.PLAYING:
                self.update_game(delta)
            elif self.state == GameState.RESPAWNING:
                self.update_respawn(delta)
            self.draw()
            pygame.display.flip()

    # ------------------------------------------------------------------ events

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit_game()
            if event.type == pygame.KEYDOWN:
                self.handle_keydown(event.key)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.handle_click(event.pos)

    def handle_keydown(self, key: int) -> None:
        if key == pygame.K_ESCAPE:
            if self.state == GameState.PLAYING:
                self.state = GameState.PAUSED
            elif self.state == GameState.PAUSED:
                self.state = GameState.PLAYING
            elif self.state == GameState.GAME_OVER:
                self.state = GameState.HOME
            return

        if self.state == GameState.HOME:
            if key in (pygame.K_RETURN, pygame.K_SPACE):
                self.start_new_game()
            elif key == pygame.K_r and self.resume_available:
                self.state = GameState.PLAYING
            return

        if self.state == GameState.GAME_OVER:
            if key == pygame.K_RETURN:
                self.start_new_game()
            elif key == pygame.K_h:
                self.state = GameState.HOME
            return

        if self.state == GameState.PAUSED:
            if key == pygame.K_r:
                self.state = GameState.PLAYING
            elif key == pygame.K_h:
                self.state = GameState.HOME
            elif key == pygame.K_n:
                self.start_new_game()
            return

        if self.state != GameState.PLAYING:
            return

        direction_map = {
            pygame.K_UP: (0, -1), pygame.K_w: (0, -1),
            pygame.K_DOWN: (0, 1), pygame.K_s: (0, 1),
            pygame.K_LEFT: (-1, 0), pygame.K_a: (-1, 0),
            pygame.K_RIGHT: (1, 0), pygame.K_d: (1, 0),
        }
        if key == pygame.K_p:
            self.state = GameState.PAUSED
            return
        if key in direction_map:
            proposed = direction_map[key]
            if proposed != (-self.direction[0], -self.direction[1]):
                self.next_direction = proposed

    def handle_click(self, pos: tuple) -> None:
        for btn in self.buttons:
            if btn.rect.collidepoint(pos):
                self.trigger_action(btn.action)
                break

    def trigger_action(self, action: str) -> None:
        actions = {
            "start":  self.start_new_game,
            "replay": self.start_new_game,
            "home":   lambda: setattr(self, "state", GameState.HOME),
            "quit":   self.quit_game,
            "resume": self._resume_if_available,
            "pause":  lambda: setattr(self, "state", GameState.PAUSED),
        }
        if action in actions:
            actions[action]()

    def _resume_if_available(self) -> None:
        if self.resume_available:
            self.state = GameState.PLAYING

    def start_new_game(self) -> None:
        self.reset_game(full=True)
        self.state = GameState.PLAYING

    # ------------------------------------------------------------------ update

    def update_game(self, delta: float) -> None:
        # animate food breathing
        for food in self.food_items:
            food.anim_timer += delta
            food.scale = 1.0 + 0.18 * math.sin(food.anim_timer * 3.5)

        self.move_timer += delta
        if self.move_timer < self.move_delay:
            return
        self.move_timer = 0.0
        self.direction = self.next_direction

        new_head = (
            self.snake[0][0] + self.direction[0],
            self.snake[0][1] + self.direction[1],
        )

        hit_wall = not (0 <= new_head[0] < GRID_COLS and 0 <= new_head[1] < GRID_ROWS)
        hit_self = new_head in self.snake[:-1]
        hit_obs  = new_head in self.obstacles

        if (hit_wall or hit_self or hit_obs) and self.invincible_timer <= 0:
            self.hearts -= 1
            self.best_score = max(self.best_score, self.score)
            if self.hearts <= 0:
                self.state = GameState.GAME_OVER
            else:
                self.state = GameState.RESPAWNING
                self.respawn_timer = 1.5
            return

        self.snake.insert(0, new_head)

        eaten = next((f for f in self.food_items if f.cell == new_head), None)
        if eaten:
            self.food_items.remove(eaten)
            self.score += eaten.points
            self.best_score = max(self.best_score, self.score)
            self.move_delay = max(0.055, self.move_delay - 0.002)
            self._spawn_food()
            # keep 2 food items on board
            if len(self.food_items) < 2:
                self._spawn_food()
            # level up check
            new_level = self.score // POINTS_PER_LEVEL + 1
            if new_level > self.level:
                self.level = new_level
                self.snake_color, self.snake_head_color = self._level_color()
                self.obstacles = self._generate_obstacles(self.level)
                # make sure food not on new obstacles
                self.food_items = [f for f in self.food_items if f.cell not in self.obstacles]
                while len(self.food_items) < 2:
                    self._spawn_food()
        else:
            self.snake.pop()

        if self.invincible_timer > 0:
            self.invincible_timer -= delta

    def update_respawn(self, delta: float) -> None:
        self.respawn_timer -= delta
        if self.respawn_timer <= 0:
            cx, cy = GRID_COLS // 2, GRID_ROWS // 2
            self.snake = [(cx - i, cy) for i in range(4)]
            self.direction = (1, 0)
            self.next_direction = (1, 0)
            self.move_timer = 0.0
            self.invincible_timer = 2.0  # 2s invincibility after respawn
            self.state = GameState.PLAYING

    # ------------------------------------------------------------------ draw

    def draw(self) -> None:
        self.screen.blit(self.bg_surface, (0, 0))
        self.draw_header()
        self.draw_playfield()

        if self.state == GameState.HOME:
            self.draw_home_screen()
        elif self.state == GameState.PAUSED:
            self.draw_pause_overlay()
        elif self.state == GameState.GAME_OVER:
            self.draw_game_over_overlay()
        elif self.state == GameState.RESPAWNING:
            self.draw_respawn_overlay()

    def draw_header(self) -> None:
        title = self.title_font.render("NEON SNAKE", True, self.text_color)
        self.screen.blit(title, (PLAY_LEFT, 24))

        sub = self.small_font.render(
            "Arrow keys / WASD to move  |  P or Esc to pause",
            True, self.muted_text)
        self.screen.blit(sub, (PLAY_LEFT + 4, 80))

        # HUD panel
        hud = pygame.Rect(PLAY_LEFT + PLAY_WIDTH - 340, 20, 340, 70)
        pygame.draw.rect(self.screen, self.panel_color, hud, border_radius=18)
        pygame.draw.rect(self.screen, self.panel_border, hud, 2, border_radius=18)

        score_txt = self.medium_font.render(f"Score: {self.score}", True, self.text_color)
        best_txt  = self.small_font.render(f"Best: {self.best_score}", True, self.gold)
        lvl_txt   = self.medium_font.render(f"Lvl {self.level}", True, self.snake_color)
        self.screen.blit(score_txt, (hud.x + 14, hud.y + 8))
        self.screen.blit(best_txt,  (hud.x + 14, hud.y + 36))
        self.screen.blit(lvl_txt,   (hud.x + 200, hud.y + 8))

        # Hearts
        hx = hud.x + 200
        hy = hud.y + 38
        for i in range(MAX_HEARTS):
            color = self.heart_color if i < self.hearts else (60, 60, 80)
            self._draw_heart(hx + i * 36, hy, 14, color)

    def _draw_heart(self, cx: int, cy: int, size: int, color: tuple) -> None:
        """Draw a filled heart at pixel (cx, cy)."""
        s = size
        points = []
        for angle in range(0, 360, 5):
            t = math.radians(angle)
            # heart parametric
            x = s * 16 * (math.sin(t) ** 3)
            y = -s * (13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t))
            points.append((cx + x / 16, cy + y / 16))
        if len(points) >= 3:
            pygame.draw.polygon(self.screen, color, points)

    def draw_playfield(self) -> None:
        board = pygame.Rect(PLAY_LEFT, PLAY_TOP, PLAY_WIDTH, PLAY_HEIGHT)
        pygame.draw.rect(self.screen, self.panel_color, board, border_radius=24)
        pygame.draw.rect(self.screen, self.panel_border, board, 3, border_radius=24)

        # grid lines
        for col in range(GRID_COLS + 1):
            x = PLAY_LEFT + col * GRID_SIZE
            pygame.draw.line(self.screen, self.grid_color, (x, PLAY_TOP), (x, PLAY_TOP + PLAY_HEIGHT))
        for row in range(GRID_ROWS + 1):
            y = PLAY_TOP + row * GRID_SIZE
            pygame.draw.line(self.screen, self.grid_color, (PLAY_LEFT, y), (PLAY_LEFT + PLAY_WIDTH, y))

        # obstacles
        for obs in self.obstacles:
            r = self.grid_rect(obs).inflate(-2, -2)
            pygame.draw.rect(self.screen, self.obstacle_color, r, border_radius=4)
            pygame.draw.rect(self.screen, self.obstacle_border, r, 2, border_radius=4)

        # food items with breathing scale
        for food in self.food_items:
            self._draw_food(food)

        # snake body (invincible flash every 0.15s)
        flash_hide = (self.invincible_timer > 0 and int(self.invincible_timer / 0.15) % 2 == 0)
        if not flash_hide:
            for idx, seg in enumerate(self.snake):
                r = self.grid_rect(seg).inflate(-4, -4)
                if idx == 0:
                    # head: use image if loaded, else colored rect with eyes
                    if self.snake_head_img:
                        # tint the head image with level color
                        tinted = self.snake_head_img.copy()
                        tinted.fill((*self.snake_head_color, 120), special_flags=pygame.BLEND_RGBA_MULT)
                        self.screen.blit(tinted, r.topleft)
                    else:
                        pygame.draw.rect(self.screen, self.snake_head_color, r, border_radius=8)
                        ey = r.y + 7
                        pygame.draw.circle(self.screen, self.panel_color, (r.x + 8, ey), 2)
                        pygame.draw.circle(self.screen, self.panel_color, (r.right - 8, ey), 2)
                else:
                    pygame.draw.rect(self.screen, self.snake_color, r, border_radius=6)

    def _draw_food(self, food: FoodItem) -> None:
        base_img = self.rat_img_base if food.food_type == "rat" else self.frog_img_base
        r = self.grid_rect(food.cell)
        cx = r.x + GRID_SIZE // 2
        cy = r.y + GRID_SIZE // 2

        if base_img:
            scaled_size = int(25 * food.scale)
            scaled_size = max(10, scaled_size)
            scaled = pygame.transform.smoothscale(base_img, (scaled_size, scaled_size))
            draw_r = scaled.get_rect(center=(cx, cy))
            self.screen.blit(scaled, draw_r)
        else:
            # fallback colored ellipse
            color = (255, 160, 60) if food.food_type == "rat" else (80, 220, 80)
            rx = int(10 * food.scale)
            ry = int(8 * food.scale)
            pygame.draw.ellipse(self.screen, color, (cx - rx, cy - ry, rx * 2, ry * 2))

    # ------------------------------------------------------------------ overlays

    def draw_home_screen(self) -> None:
        panel = pygame.Rect(170, 155, 620, 400)
        self.draw_overlay_panel(panel)

        heading = self.large_font.render("Classic snake, arcade glow.", True, self.text_color)
        body = self.small_font.render(
            "Eat rats (10pts) & frogs (5pts)  |  3 hearts  |  Level up every 100pts",
            True, self.muted_text)
        stats = self.small_font.render(f"Best score so far: {self.best_score}", True, self.gold)
        self.screen.blit(heading, heading.get_rect(center=(WINDOW_WIDTH // 2, 210)))
        self.screen.blit(body,    body.get_rect(center=(WINDOW_WIDTH // 2, 248)))
        self.screen.blit(stats,   stats.get_rect(center=(WINDOW_WIDTH // 2, 278)))

        actions = [("Play", "start")]
        if self.resume_available and self.score > 0:
            actions.append(("Resume", "resume"))
        actions.append(("Quit", "quit"))
        self.buttons = self.build_buttons(panel.centerx, 320, actions)
        self.draw_buttons()

        tips = ["Enter / Space: Play", "R: Resume saved run", "Esc: Pause or go back"]
        for i, tip in enumerate(tips):
            lbl = self.small_font.render(tip, True, self.muted_text)
            self.screen.blit(lbl, lbl.get_rect(center=(WINDOW_WIDTH // 2, 460 + i * 28)))

    def draw_pause_overlay(self) -> None:
        panel = pygame.Rect(210, 190, 540, 320)
        self.draw_overlay_panel(panel)

        title = self.large_font.render("Game Paused", True, self.text_color)
        info  = self.small_font.render("Catch your breath. Your run is still here.", True, self.muted_text)
        self.screen.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, 245)))
        self.screen.blit(info,  info.get_rect(center=(WINDOW_WIDTH // 2, 280)))

        self.buttons = self.build_buttons(
            panel.centerx, 330,
            [("Resume", "resume"), ("Replay", "replay"), ("Home", "home"), ("Quit", "quit")],
            per_row=2)
        self.draw_buttons()

    def draw_game_over_overlay(self) -> None:
        panel = pygame.Rect(205, 165, 550, 370)
        self.draw_overlay_panel(panel)

        title = self.large_font.render("Game Over", True, (255, 80, 80))
        score = self.medium_font.render(f"Final score: {self.score}  |  Level {self.level}", True, self.text_color)
        best  = self.small_font.render(f"Best score: {self.best_score}", True, self.gold)
        self.screen.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, 225)))
        self.screen.blit(score, score.get_rect(center=(WINDOW_WIDTH // 2, 270)))
        self.screen.blit(best,  best.get_rect(center=(WINDOW_WIDTH // 2, 303)))

        self.buttons = self.build_buttons(
            panel.centerx, 360,
            [("Replay", "replay"), ("Home", "home"), ("Quit", "quit")])
        self.draw_buttons()

        hint = self.small_font.render("Enter to replay  |  H for home", True, self.muted_text)
        self.screen.blit(hint, hint.get_rect(center=(WINDOW_WIDTH // 2, 470)))

    def draw_respawn_overlay(self) -> None:
        shade = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 80))
        self.screen.blit(shade, (0, 0))

        msg = self.large_font.render(
            f"💔  {self.hearts} heart{'s' if self.hearts != 1 else ''} left — respawning…",
            True, self.heart_color)
        self.screen.blit(msg, msg.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)))

    def draw_overlay_panel(self, rect: pygame.Rect) -> None:
        shade = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 110))
        self.screen.blit(shade, (0, 0))
        pygame.draw.rect(self.screen, self.panel_color, rect, border_radius=24)
        pygame.draw.rect(self.screen, self.panel_border, rect, 2, border_radius=24)

    # ------------------------------------------------------------------ buttons

    def build_buttons(self, cx, start_y, actions, per_row=1) -> list[Button]:
        buttons = []
        w, h, gap = 180, 52, 20
        for idx, (label, action) in enumerate(actions):
            row, col = idx // per_row, idx % per_row
            total_w = per_row * w + (per_row - 1) * gap
            x = cx - total_w // 2 + col * (w + gap)
            y = start_y + row * (h + 16)
            buttons.append(Button(label, pygame.Rect(x, y, w, h), action))
        return buttons

    def draw_buttons(self) -> None:
        mouse_pos = pygame.mouse.get_pos()
        for btn in self.buttons:
            hovered = btn.rect.collidepoint(mouse_pos)
            fill    = (33, 68, 92) if hovered else (22, 40, 57)
            outline = self.gold if hovered else self.panel_border
            pygame.draw.rect(self.screen, fill,    btn.rect, border_radius=16)
            pygame.draw.rect(self.screen, outline, btn.rect, 2, border_radius=16)
            txt = self.medium_font.render(btn.label, True, self.text_color)
            self.screen.blit(txt, txt.get_rect(center=btn.rect.center))

    # ------------------------------------------------------------------ utils

    def grid_rect(self, cell: tuple) -> pygame.Rect:
        return pygame.Rect(
            PLAY_LEFT + cell[0] * GRID_SIZE,
            PLAY_TOP  + cell[1] * GRID_SIZE,
            GRID_SIZE, GRID_SIZE)

    def quit_game(self) -> None:
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    SnakeGame().run()