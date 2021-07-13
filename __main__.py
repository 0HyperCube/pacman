from xmlrpc.client import Boolean
import pygame
from pygame.locals import *
import time
import math
from copy import deepcopy

from dataclasses import dataclass
from typing import Tuple, List


@dataclass
class Vec2:
    x: int = 0
    y: int = 0


@dataclass
class Sprite:
    position: Vec2 = Vec2(1, 1)
    direction: Vec2 = Vec2(1, 0)
    stopped: bool = False
    speed: float = 200
    updated: float = time.time()


TILE_SIZE: int = 30
TILES_OFFSET: Vec2 = Vec2(0, 50)

BLOCK = 1


def new_ghost_direction(board, pos, direction, target_pos):
    # Returns new direction
    # Cannot go in opposite of current direction
    # Chooses path with least distance (x^2 + y^2) to target
    pass


def grid():
    rows = """
    ████████████████████
    █ *****************█
    █*████████████████*█
    █******************█
    █*██████*██*██████*█
    █*██████*██*██████*█
    █*██████*██*██████*█
    █******************█
    █*███*████████*███*█
    █*███*██    ██*███*█
    █*███*██    ██*███*█
    █*███*████████*███*█
    █******************█
    █*██████*██*██████*█
    █*██████*██*██████*█
    █*██████*██*██████*█
    █******************█
    █*████████████████*█
    █******************█
    ████████████████████
    """.strip().split(
        "\n"
    )
    return [[[" ", "█", "*"].index(c) for c in r.strip()] for r in rows]


def render_board(board: List[List[int]], displaysurface: pygame.Surface):
    for row in range(len(board)):
        for col in range(len(board[0])):
            if board[row][col] == 1:
                pos = (
                    TILE_SIZE * col + TILES_OFFSET.x,
                    TILE_SIZE * row + TILES_OFFSET.y,
                )
                pygame.draw.rect(
                    displaysurface,
                    (33, 33, 222),
                    Rect(pos, (TILE_SIZE - 1, TILE_SIZE - 1)),
                )
            elif board[row][col] == 2:
                pos = (
                    TILE_SIZE * col + TILE_SIZE / 2 + TILES_OFFSET.x,
                    TILE_SIZE * row + TILE_SIZE / 2 + TILES_OFFSET.y,
                )
                pygame.draw.circle(displaysurface, (255, 255, 255), pos, 3, 0)


def render_sprite(
    displaysurface: pygame.Surface, img: pygame.Surface, sprite: Sprite, flip: Boolean
):
    if flip:
        rotated_sprite = pygame.transform.flip(img, sprite.direction.x == -1, 0)
    else:
        angles = {(1, 0): 0, (0, 1): -90, (0, -1): 90, (-1, 0): 180, (0,0):0}
        rotated_sprite = pygame.transform.rotate(
            img, angles[(sprite.direction.x, sprite.direction.y)]
        )
    displaysurface.blit(rotated_sprite, get_board_pos(sprite))


# Converts a Tile position to a board position
# Returns the board pos
def get_board_pos(sprite: Sprite) -> Tuple[int, int]:
    board_pos = Vec2(
        sprite.position.x * TILE_SIZE + TILES_OFFSET.x,
        sprite.position.y * TILE_SIZE + TILES_OFFSET.y,
    )
    if not sprite.stopped:
        delta = (time.time() - sprite.updated) * sprite.speed
        board_pos = Vec2(
            board_pos.x + sprite.direction.x * delta,
            board_pos.y + sprite.direction.y * delta,
        )
    return (board_pos.x, board_pos.y)


# Checks if on new tile
# returns (result, pos, updated)
def is_new_tile(sprite: Sprite) -> bool:
    if sprite.stopped:
        sprite.updated = time.time()
        return True
    delta = time.time() - sprite.updated
    tiles_per_sec = sprite.speed / TILE_SIZE
    complete_tiles = math.floor(delta * tiles_per_sec)
    if complete_tiles:
        sprite.position = add_dir(sprite.position, sprite.direction)
        sprite.updated += complete_tiles / tiles_per_sec
        return True
    return False

def vec_dist(a: Vec2, b:Vec2) -> Vec2:
    return math.sqrt(abs(a.x - b.x)**2 + abs(a.y - b.y)**2)

def inverse_dir(dir: Vec2):
    return Vec2(-dir.x, -dir.y)


def add_dir(pos: Vec2, dir: Vec2):
    return Vec2(pos.x + dir.x, pos.y + dir.y)


def board_at(board: List[List[int]], pos: Vec2):
    return board[pos.y][pos.x]


# Handle input from the arrow keys
# Returns new target direction or `None`
def handle_direction_input(event):
    if event.key == K_UP:
        return Vec2(0, -1)
    elif event.key == K_DOWN:
        return Vec2(0, 1)
    elif event.key == K_LEFT:
        return Vec2(-1, 0)
    elif event.key == K_RIGHT:
        return Vec2(1, 0)


# Handle inverting direction.
def handle_opposite_direction(board, player_target_dir, player: Sprite, score: int, ghosts, dead:bool):
    if player_target_dir == inverse_dir(player.direction):
        player.position = add_dir(player.position, player.direction)
        if board_at(board, player.position) == 2:
            board[player.position.y][player.position.x] = 0
            score += 10
        player.direction = player_target_dir
        delta = time.time() - player.updated
        tiles_per_sec = player.speed / TILE_SIZE
        player.updated += delta
        player.updated -= 1 / tiles_per_sec - delta
        dead = check_dead(player, ghosts)
    return (dead,score)


def handle_events(player_target_dir):
    for event in pygame.event.get():
        # Close button exits
        if event.type == QUIT:
            pygame.quit()
            return False
        elif event.type == KEYDOWN:
            if event.key == K_ESCAPE:  # Escape key to exit
                pygame.quit()
                return False
            else:
                # Handle arrow keys
                player_target_dir = handle_direction_input(event) or player_target_dir
    return player_target_dir

def update_ghosts(player, ghosts, displaysurface, board, ghost_imgs):
    for ghost_index in range(len(ghosts)):
            ghost = ghosts[ghost_index]
            ghost_tile_update = is_new_tile(ghost)
            if ghost_tile_update:
                min_dist = 99999
                min_dir = (0,0)
                for new_dir in (Vec2(0,1),Vec2(0,-1),Vec2(-1,0),Vec2(1,0)):
                    next_pos = add_dir(ghost.position, new_dir)
                    dist = vec_dist(next_pos, add_dir(player.position, player.direction))
                    if dist < min_dist:
                        # Ghosts can't go backwards
                        if new_dir == inverse_dir(ghost.direction):
                            continue

                        # Ghosts can't go in walls
                        if board_at(board, next_pos) == BLOCK:
                            continue
                            
                        min_dist = dist
                        min_dir = new_dir
                if ghost.position == player.position or ghost.position == add_dir(player.position, player.direction):
                    return True
                ghost.direction = min_dir

            render_sprite(displaysurface, ghost_imgs[ghost_index], ghost, True)

def check_dead(player, ghosts):
    for ghost in ghosts:
        if player.position == ghost.position:
            return True
    return False

def run_level(
    lvl: int,
    lives: int,
    font: pygame.font.Font,
    pacman1_img: pygame.Surface,
    pacman2_img: pygame.Surface,
    ghost_imgs: List[pygame.Surface],
    displaysurface: pygame.Surface,
    timer,
    board = None,
    score = 0,
):
    player: Sprite = Sprite(position=Vec2(1, 1), direction=Vec2(0, 0), speed=200+lvl*20, stopped=True)
    ghosts = [Sprite(position=Vec2(19, 10), direction=Vec2(-1, 0), speed=90+lvl*20),
              Sprite(position=Vec2(1, 18), direction=Vec2(0, 0), speed=100+lvl*25)]
    player_target_dir = Vec2(0, 0)
    frame = 0
    if board==None:
        board = grid()
    dead = False
    started = False
    while score < 1510 and not dead:
        player_target_dir = handle_events(player_target_dir)
        
        if not player_target_dir:
            return False, 0

        # Clear screen
        displaysurface.fill((0, 0, 0))

        # Display the text
        displaysurface.blit(
            font.render(f"Level: {str(lvl)}", False, (255, 255, 255)), (10, 10)
        )
        displaysurface.blit(
            font.render(f"Score: {str(score)}", False, (255, 255, 255)), (240, 10)
        )
        displaysurface.blit(
            font.render(f"Lives: {str(lives)}", False, (255, 255, 255)), (510, 10)
        )

        # Blit the maze
        render_board(board, displaysurface)

        # Find if player is on a new tile
        player_tile_update = is_new_tile(player)

        (dead, score) = handle_opposite_direction(board, player_target_dir, player, score, ghosts, dead)
        
        # Handle player on new tile
        if player_tile_update:
            if board_at(board, player.position) == 2:
                board[player.position.y][player.position.x] = 0
                score += 10
            if board_at(board, add_dir(player.position, player_target_dir)) != 1:
                player.direction = player_target_dir
                player.stopped = False
            elif board_at(board, add_dir(player.position, player.direction)) != 1:
                player.stopped = False
            else:
                player.stopped = True
            dead = check_dead(player, ghosts)
        
        if (frame // 9) % 2 == 0:
            s = pacman1_img
        else:
            s = pacman2_img
        render_sprite(displaysurface, s, player, False)

        if not dead:
            dead = update_ghosts(player, ghosts, displaysurface, board, ghost_imgs)

        pygame.display.update()
        timer.tick(60)
        frame += 1
    if not dead:
        return None,0
    else:
        return board, score


# Runs the game
def run():

    pygame.display.set_caption("Pacman")
    FramePerSec = pygame.time.Clock()

    # Initiate pygame
    pygame.init()
    displaysurface: pygame.Surface = pygame.display.set_mode((600, 650))

    # Initiate font
    pygame.font.init()
    myfont = pygame.font.SysFont("Font.ttf", 30)

    # Load ghost images
    ghost_img: pygame.Surface = pygame.image.load("ghost.png")

    ghost_imgs = []
    for col in [(20,160,130),(250,220,10)]:
        r = ghost_img.convert_alpha() # Also copies
        r.fill(col, None, pygame.BLEND_RGB_MIN)
        ghost_imgs.append(r)

    # Load pacman images
    pacman1_img: pygame.Surface = pygame.image.load("pacman1.png").convert_alpha()
    pacman2_img: pygame.Surface = pygame.image.load("pacman2.png").convert_alpha()
    pacman_col: pygame.Surface = (255, 255, 0)
    pacman1_img.fill(pacman_col, None, pygame.BLEND_RGB_MIN)
    pacman2_img.fill(pacman_col, None, pygame.BLEND_RGB_MIN)

    while True:
        level = 1
        lives = 3
        game_over = False
        board = None
        score = 0
        while not game_over:
            board, score = run_level(
                level,
                lives,
                myfont,
                pacman1_img,
                pacman2_img,
                ghost_imgs,
                displaysurface,
                FramePerSec,
                board,
                score,
            )
            if board == None:
                level += 1
            elif board == False:
                return
            else:
                lives-=1
            if lives==0:
                game_over = True


run()
pygame.quit()
