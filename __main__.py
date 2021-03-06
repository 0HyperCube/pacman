import pygame
from pygame.locals import *
import time
import math

from dataclasses import dataclass
from typing import Tuple, List


# This struct represents a simple 2d vector
@dataclass
class Vec2:
    x: int = 0
    y: int = 0


# The distance between two vectors
def vec_dist(a: Vec2, b: Vec2) -> Vec2:
    return math.sqrt(abs(a.x - b.x) ** 2 + abs(a.y - b.y) ** 2)


# The inverse of a vector
def invert_vec(dir: Vec2):
    return Vec2(-dir.x, -dir.y)


# Add two vectors
def add_vec(pos: Vec2, dir: Vec2):
    return Vec2(pos.x + dir.x, pos.y + dir.y)


# This struct represents either pacman or a ghost
@dataclass
class Sprite:
    position: Vec2 = Vec2(1, 1)
    direction: Vec2 = Vec2(1, 0)
    target_dir: Vec2 = Vec2()
    stopped: bool = False
    speed: float = 200
    updated: float = time.time()
    updated_evaluated: float = time.time()


# Constants

TILE_SIZE: int = 24
TILES_OFFSET: Vec2 = Vec2(0, 50)
POWER_UP_TIME: float = 2

BLOCK = 1

BOARD: str = """
    █████████████████████████
    █***********************█
    █*████*█████*█████*████*█
    █*████*█████*█████*████*█
    █*████*█████*█████*████*█
    █*████*█████*█████*████*█
    █***********************█
    █*████*██*█████*██*████*█
    █*████*██*█████*██*████*█
    █*████*██*█████*██*████*█
    █***********************█
    ██████*█*███████*█*██████
    ██████*█*█     █*█*██████
    ██████*█*█     █*█*██████
    ██████*█*█     █*█*██████
    █******█*███████*█******█
    █*████*█*********█*████*█
    █O████*███*███*███*████O█
    █*████*███*███*███*████*█
    █**********███**********█
    █*████████*███*████████*█
    █*████████*███*████████*█
    █*████████*███*████████*█
    █***********************█
    █████████████████████████
    """

# Parses the maze from ascii art
def parse_board(board):
    rows = board.strip().split("\n")
    return [[[" ", "█", "*", "O"].index(c) for c in r.strip()] for r in rows]


def count_points(board):
    return board.count("*") * 10 + board.count("O") * 50


DOTS_PER_LEVEL: int = count_points(BOARD)

# Get the board at a vector
def board_at(board: List[List[int]], pos: Vec2):
    return board[pos.y][pos.x]


# Converts a Tile position to a board position
# Returns the board pos
def get_board_pos(sprite: Sprite) -> Tuple[int, int]:
    board_pos = Vec2(
        sprite.position.x * TILE_SIZE + TILES_OFFSET.x,
        sprite.position.y * TILE_SIZE + TILES_OFFSET.y,
    )
    t = time.time()
    if sprite.stopped:
        sprite.updated = t - (sprite.updated_evaluated - sprite.updated)
        sprite.updated_evaluated = t
    delta = (sprite.updated_evaluated - sprite.updated) * sprite.speed
    board_pos = Vec2(
        board_pos.x + sprite.direction.x * delta,
        board_pos.y + sprite.direction.y * delta,
    )
    return (board_pos.x, board_pos.y)


# Blits the board from the nested list every frame
def render_board(board: List[List[int]], displaysurface: pygame.Surface):
    for row in range(len(board)):
        for col in range(len(board[0])):
            # Wall / Block
            if board[row][col] == 1:
                # Calculate position
                pos = (
                    TILE_SIZE * col + TILES_OFFSET.x,
                    TILE_SIZE * row + TILES_OFFSET.y,
                )

                # Blit rect
                pygame.draw.rect(
                    displaysurface,
                    (33, 33, 222),
                    Rect(pos, (TILE_SIZE - 1, TILE_SIZE - 1)),
                )

            # Normal dot or power up dot
            elif board[row][col] == 2 or board[row][col] == 3:
                # Calculate position
                pos = (
                    int(TILE_SIZE * col + TILE_SIZE / 2 + TILES_OFFSET.x),
                    int(TILE_SIZE * row + TILE_SIZE / 2 + TILES_OFFSET.y),
                )

                # Get dot radius based on dot type
                if board[row][col] == 2:
                    radius = 3
                else:
                    radius = 5

                # Blit circle
                pygame.draw.circle(displaysurface, (255, 255, 255), pos, radius, 0)


# Renders either pacman or a ghost. Handles converting to pixel coordinates
def render_sprite(
    displaysurface: pygame.Surface, img: pygame.Surface, sprite: Sprite, flip: bool
):
    if flip:
        rotated_sprite = pygame.transform.flip(img, sprite.direction.x == -1, 0)
    else:
        angles = {(1, 0): 0, (0, 1): -90, (0, -1): 90, (-1, 0): 180, (0, 0): 0}
        rotated_sprite = pygame.transform.rotate(
            img, angles[(sprite.direction.x, sprite.direction.y)]
        )
    displaysurface.blit(rotated_sprite, get_board_pos(sprite))


# Checks if on new tile
# returns (result, pos, updated)
def is_new_tile(sprite: Sprite) -> bool:
    t = time.time()
    if sprite.stopped:
        sprite.updated = t - (sprite.updated_evaluated - sprite.updated)
        sprite.updated_evaluated = t
        return True
    delta = t - sprite.updated
    sprite.updated_evaluated = t
    tiles_per_sec = sprite.speed / TILE_SIZE
    complete_tiles = math.floor(delta * tiles_per_sec)
    if complete_tiles:
        sprite.position = add_vec(sprite.position, sprite.direction)
        sprite.updated += complete_tiles / tiles_per_sec
        return True
    return False


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


# Reverses a sprite's direction
def invert_direction(sprite: Sprite):
    sprite.direction = invert_vec(sprite.direction)
    delta = time.time() - sprite.updated
    tiles_per_sec = sprite.speed / TILE_SIZE
    sprite.updated += delta
    sprite.updated -= 1 / tiles_per_sec - delta


# Handle inverting the direction of ghosts
# This happens when you get powered up and stopp being powered up
def invert_ghost_direction(ghosts: List[Sprite]):
    for ghost in ghosts:
        ghost.target_dir = invert_vec(ghost.direction)


# Handle inverting direction.
def handle_opposite_direction(
    board, player: Sprite, score: int, ghosts, dead: bool, power_time: float
):
    if player.target_dir == invert_vec(player.direction):
        player.position = add_vec(player.position, player.direction)
        if board_at(board, player.position) == 2:
            board[player.position.y][player.position.x] = 0
            score += 10
        elif board_at(board, player.position) == 3:
            board[player.position.y][player.position.x] = 0
            score += 50
            power_time = time.time()
            invert_ghost_direction(ghosts)

        invert_direction(player)
        (dead, ghost) = check_dead(player, ghosts)
    return (dead, score, power_time)


# Poll pygame events including arrow keys
# Returns true if quit
def handle_events(player):
    for event in pygame.event.get():
        # Close button exits
        if event.type == QUIT:
            pygame.quit()
            return True
        elif event.type == KEYDOWN:
            if event.key == K_ESCAPE:  # Escape key to exit
                pygame.quit()
                return True
            else:
                # Handle arrow keys
                player.target_dir = handle_direction_input(event) or player.target_dir
    return False


def best_ghost_direction(player, ghost, board, power_time):
    if power_time:
        best_dist = 0
    else:
        best_dist = 9999999
    best_dir = Vec2(0, 0)

    for new_dir in (Vec2(0, 1), Vec2(0, -1), Vec2(-1, 0), Vec2(1, 0)):
        next_pos = add_vec(ghost.position, new_dir)
        dist = vec_dist(next_pos, add_vec(player.position, player.direction))
        if (dist < best_dist and not power_time) or (dist > best_dist and power_time):
            # Ghosts can't go backwards
            if new_dir == invert_vec(ghost.direction):
                continue

            # Ghosts can't go in walls
            if board_at(board, next_pos) == BLOCK:
                continue

            best_dist = dist
            best_dir = new_dir
    return best_dir


# Display and update ghost positions
def update_ghosts(
    player, ghosts, displaysurface, board, ghost_imgs, started, dead, power_time
):
    for ghost_index in range(len(ghosts)):
        ghost: Sprite = ghosts[ghost_index]
        if not started or ghost.stopped:
            t = time.time()
            ghost.updated = t - (ghost.updated_evaluated - ghost.updated)
            ghost.updated_evaluated = t
            render_sprite(displaysurface, ghost_imgs[ghost_index], ghost, True)
            continue

        ghost_tile_update = is_new_tile(ghost)
        if ghost_tile_update:
            if ghost.target_dir != Vec2():
                new_dir = ghost.target_dir
                ghost.target_dir = Vec2()
            else:
                new_dir = best_ghost_direction(player, ghost, board, power_time)
            if ghost.position == player.position:
                if power_time:
                    ghost.stopped = True
                else:
                    dead = True
            ghost.direction = new_dir

        render_sprite(displaysurface, ghost_imgs[ghost_index], ghost, True)
    return dead


# Check if pacman is on the same tile as a ghost
def check_dead(player, ghosts) -> Tuple[bool, Sprite]:
    for ghost in ghosts:
        if player.position == ghost.position:
            return True, ghost
    return False, None


# Handles running a specific level
def run_level(
    lvl: int,
    lives: int,
    font: pygame.font.Font,
    pacman1_img: pygame.Surface,
    pacman2_img: pygame.Surface,
    ghost_imgs: List[pygame.Surface],
    displaysurface: pygame.Surface,
    timer,
    board=None,
    score=0,
):
    player: Sprite = Sprite(
        position=Vec2(1, 1), direction=Vec2(0, 0), speed=200 + lvl * 20, stopped=True
    )
    ghosts = [
        Sprite(position=Vec2(18, 10), direction=Vec2(-1, 0), speed=90 + lvl * 20),
        Sprite(position=Vec2(1, 18), direction=Vec2(0, 0), speed=100 + lvl * 25),
    ]
    player.target_dir = Vec2(0, 0)
    frame = 0
    if board == None:
        board = parse_board(BOARD)
    dead = False
    started = False
    time_dead = False
    power_time = False
    while score < DOTS_PER_LEVEL and (not time_dead or (time.time() - time_dead < 2)):

        # Poll pygame events
        if handle_events(player):
            # Application quit
            return False, 0

        # Start the ghosts moving
        if not started and player.direction != Vec2(0, 0):
            started = True

        # Handle death
        if dead and not time_dead:
            time_dead = time.time()
            player.stopped = True

        # Clear screen
        displaysurface.fill((0, 0, 0))

        # Display the text
        displaysurface.blit(
            font.render(f"Level: {str(lvl)}", False, (255, 255, 255)), (10, 10)
        )
        displaysurface.blit(
            font.render(
                f"Score: {str(score + DOTS_PER_LEVEL * (lvl-1))}",
                False,
                (255, 255, 255),
            ),
            (240, 10),
        )
        displaysurface.blit(
            font.render(f"Lives: {str(lives)}", False, (255, 255, 255)), (510, 10)
        )

        # Blit the maze
        render_board(board, displaysurface)

        # Handle deactivating the power up
        if power_time and time.time() - power_time > POWER_UP_TIME:
            power_time = False
            invert_ghost_direction(ghosts)

        # Find if player is on a new tile
        if not dead:
            player_tile_update = is_new_tile(player)
            (dead, score, power_time) = handle_opposite_direction(
                board, player, score, ghosts, dead, power_time
            )

        # Handle player on new tile
        if not dead and player_tile_update:
            if board_at(board, player.position) == 2:
                board[player.position.y][player.position.x] = 0
                score += 10
            elif board_at(board, player.position) == 3:
                board[player.position.y][player.position.x] = 0
                score += 50
                power_time = time.time()
                invert_ghost_direction(ghosts)
            if player.target_dir == Vec2(0, 0):
                pass
            elif board_at(board, add_vec(player.position, player.target_dir)) != 1:
                player.direction = player.target_dir
                player.stopped = False
            elif board_at(board, add_vec(player.position, player.direction)) != 1:
                player.stopped = False
            else:
                player.stopped = True
            (dead, ghost) = check_dead(player, ghosts)
            if power_time and dead:
                ghost.stopped = True
                dead = False

        # Update animation
        if (frame // 9) % 2 == 0:
            s = pacman1_img
        else:
            s = pacman2_img

        # Render pacman
        render_sprite(displaysurface, s, player, False)

        # Render ghosts
        dead = update_ghosts(
            player, ghosts, displaysurface, board, ghost_imgs, started, dead, power_time
        )

        # Display game over message
        if dead and lives == 1:
            displaysurface.blit(
                font.render(f"Game Over", False, (255, 255, 255)), (250, 270)
            )
        elif dead:
            displaysurface.blit(
                font.render(f"Death hast befolen on thee", False, (255, 255, 255)),
                (170, 270),
            )

        # Update
        pygame.display.update()
        timer.tick(60)
        if not player.stopped:
            frame += 1

    if not dead:
        return None, 0
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
    for col in [(20, 160, 130), (250, 220, 10)]:
        r = ghost_img.convert_alpha()  # Also copies
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
                lives -= 1
            if lives == 0:
                game_over = True


run()
pygame.quit()
