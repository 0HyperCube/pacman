import pygame
from pygame.locals import *
import time
import math


vec = pygame.math.Vector2

# Initiate pygame
pygame.init()
displaysurface = pygame.display.set_mode((600, 650))
TILE_SIZE = 30
TILES_OFFSET = (0, 20)


# Load ghost images
ghost_img = pygame.image.load("ghost.png").convert_alpha()


# Load pacman images
pacman1_img = pygame.image.load("pacman1.png").convert_alpha()
pacman2_img = pygame.image.load("pacman2.png").convert_alpha()
pacman_col = (255, 255, 0)
pacman1_img.fill(pacman_col, None, pygame.BLEND_RGB_MIN)
pacman2_img.fill(pacman_col, None, pygame.BLEND_RGB_MIN)


def new_ghost_direction(board, pos, direction, target_pos):
    # Returns new direction
    # Cannot go in opposite of current direction
    # Chooses path with least distance (x^2 + y^2) to target
    pass


def new_player_direction(board, pos, direction, target_direction):
    # Returns new direction
    # If target_direction possible, returns target direction
    # Otherwise returns direction if still possible
    # Finally returns False
    pass


def grid():
    rows = """
    ████████████████████
    █******************█
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


def render_board(board, displaysurface):
    for row in range(len(board)):
        for col in range(len(board[0])):
            if board[row][col] == 1:
                pos = (
                    TILE_SIZE * col + TILES_OFFSET[0],
                    TILE_SIZE * row + TILES_OFFSET[1],
                )
                pygame.draw.rect(
                    displaysurface,
                    (33, 33, 222),
                    Rect(pos, (TILE_SIZE - 1, TILE_SIZE - 1)),
                )
            elif board[row][col] == 2:
                pos = (
                    TILE_SIZE * col + TILE_SIZE / 2 + TILES_OFFSET[0],
                    TILE_SIZE * row + TILE_SIZE / 2 + TILES_OFFSET[1],
                )
                pygame.draw.circle(displaysurface, (255, 255, 255), pos, 3, 0)


def render_sprite(pos, displaysurface, direction, sprite):
    angles = {(1, 0): 0, (0, 1): -90, (0, -1): 90, (-1, 0): 180}
    rotated_sprite = pygame.transform.rotate(sprite, angles[direction])
    displaysurface.blit(rotated_sprite, pos)


# Converts a Tile position to a board position
# Returns the board pos
def get_board_pos(pos, dir, last_updated, speed=70, stuck=False):
    board_pos = (
        pos[0] * TILE_SIZE + TILES_OFFSET[0],
        pos[1] * TILE_SIZE + TILES_OFFSET[1],
    )
    if not stuck:
        delta = (time.time() - last_updated) * speed
        board_pos = (board_pos[0] + dir[0] * delta, board_pos[1] + dir[1] * delta)
    return board_pos


# Checks if on new tile
# returns (result, pos, updated)
def is_new_tile(pos, dir, last_updated, speed=70, stuck=False):
    if stuck:
        return (True, pos, time.time())
    delta = time.time() - last_updated
    tiles_per_sec = speed / TILE_SIZE
    complete_tiles = math.floor(delta * tiles_per_sec)
    if complete_tiles:
        new_pos = (pos[0] + dir[0], pos[1] + dir[1])
        return (True, new_pos, last_updated + complete_tiles / tiles_per_sec)
    return (False, pos, last_updated)
def inverse_dir(dir):
    return (-dir[0], -dir[1])
def add_dir(pos,dir):
    return (pos[0]+dir[0], pos[1]+dir[1])
def board_at(board, pos):
    return board[pos[1]][pos[0]]

# Handle input from the arrow keys
# Returns new target direction or `None`
def handle_direction_input(event):
    if event.key == K_UP:
        return (0,-1)
    elif event.key == K_DOWN:
        return (0,1)
    elif event.key == K_LEFT:
        return (-1,0)
    elif event.key == K_RIGHT:
        return (1,0)

# Handle inverting direction.
# Returns `player_dir`,  `player pos` and `player_updated`
def handle_opposite_direction(player_target_dir, player_dir, player_pos, player_updated, player_speed):
    if player_target_dir == inverse_dir(player_dir):
        player_pos = add_dir(player_pos, player_dir)
        player_dir = player_target_dir
        delta = time.time() - player_updated
        tiles_per_sec = player_speed / TILE_SIZE
        player_updated += delta
        player_updated-=1/tiles_per_sec - delta
    return (player_dir, player_pos, player_updated)

# Runs the game
def run():
    board = grid()
    FramePerSec = pygame.time.Clock()
    pygame.display.set_caption("Pacman")

    player_pos = (1, 1)
    player_dir = (1, 0)
    player_target_dir = (1,0)
    player_stuck = False
    player_speed = 200
    player_updated = time.time()

    while True:
        for event in pygame.event.get():
            # Close button exits
            if event.type == QUIT:
                pygame.quit()
                return
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:   # Escape key to exit
                    pygame.quit()
                    return
                else:
                    # Handle arrow keys
                    player_target_dir = handle_direction_input(event) or player_target_dir

        # Clear screen
        displaysurface.fill((0, 0, 0))

        # Blit the maze
        render_board(board, displaysurface)

        # Find if player is on a new tile
        (player_tile_update, player_pos, player_updated) = is_new_tile(
            player_pos, player_dir, player_updated, player_speed, player_stuck
        )

        (player_dir, player_pos, player_updated) = handle_opposite_direction(player_target_dir, player_dir, player_pos, player_updated, player_speed)

        # Handle player on new tile
        if player_tile_update:
            if board_at(board, player_pos) == 2:
                board[player_pos[1]][player_pos[0]] = 0
            if board_at(board, add_dir(player_pos, player_target_dir)) !=1:
                player_dir = player_target_dir
                player_stuck = False
            elif board_at(board, add_dir(player_pos, player_dir)) !=1:
                player_stuck = False
            else:
                player_stuck = True
        pos = get_board_pos(
            player_pos, player_dir, player_updated, player_speed, player_stuck
        )
        render_sprite(pos, displaysurface, player_dir, pacman1_img)



        pygame.display.update()
        FramePerSec.tick(60)


run()
pygame.quit()
