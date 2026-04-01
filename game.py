import tkinter
import random

ROWS = 25
COLS = 25
TILE_SIZE = 25

WINDOW_WIDTH = TILE_SIZE * ROWS
WINDOW_HEIGHT = TILE_SIZE * COLS

class Tile:
    def __init__(self, x, y):
        self.x = x
        self.y = y

# game window
window = tkinter.Tk()
window.title("Snake Game")
window.resizable(False, False)

canvas = tkinter.Canvas(window, bg='black', width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
canvas.pack()
window.update()

# center the window
window_width = window.winfo_width()
window_height = window.winfo_height()
screen_width = window.winfo_screenwidth()
screen_height = window.winfo_screenheight()

window_x = int((screen_width/2) - (window_width/2))
window_y = int((screen_height/2) - (window_height/2))

window.geometry(f"{window_width}x{window_height}+{window_x}+{window_y}")

# initialize game variables
snake = Tile(5*TILE_SIZE, 5*TILE_SIZE)
food = Tile(10*TILE_SIZE, 10*TILE_SIZE)
snake_body = []
velocityX = 0
velocityY = 0
game_over = False
score = 0

def change_direction(e):
    global velocityX, velocityY, game_over

    if game_over:
        return

    if e.keysym == "Up" and velocityY != 1:
        velocityX = 0
        velocityY = -1
    elif e.keysym == "Down" and velocityY != -1:
        velocityX = 0
        velocityY = 1
    elif e.keysym == "Left" and velocityX != 1:
        velocityX = -1
        velocityY = 0
    elif e.keysym == "Right" and velocityX != -1:
        velocityX = 1
        velocityY = 0


def move():
    global snake, game_over, food, snake_body, score

    if game_over:
        return

    # wall collision
    if snake.x < 0 or snake.x >= WINDOW_WIDTH or snake.y < 0 or snake.y >= WINDOW_HEIGHT:
        game_over = True

    # self collision
    for tile in snake_body:
        if snake.x == tile.x and snake.y == tile.y:
            game_over = True
            return

    # food collision
    if snake.x == food.x and snake.y == food.y:
        snake_body.append(Tile(food.x, food.y))

        food.x = random.randint(0, COLS-1) * TILE_SIZE
        food.y = random.randint(0, ROWS-1) * TILE_SIZE

        score += 1

    # update body
    for i in range(len(snake_body)-1, -1, -1):
        tile = snake_body[i]

        if i == 0:
            tile.x = snake.x
            tile.y = snake.y
        else:
            prev_tile = snake_body[i-1]
            tile.x = prev_tile.x
            tile.y = prev_tile.y

    snake.x += velocityX * TILE_SIZE
    snake.y += velocityY * TILE_SIZE


def draw():
    global snake, food, snake_body, game_over, score

    move()

    canvas.delete("all")

    # draw food
    canvas.create_rectangle(food.x, food.y,
                            food.x + TILE_SIZE, food.y + TILE_SIZE,
                            fill="red")

    # draw snake head
    canvas.create_rectangle(snake.x, snake.y,
                            snake.x + TILE_SIZE, snake.y + TILE_SIZE,
                            fill="lime green")

    # draw snake body
    for tile in snake_body:
        canvas.create_rectangle(tile.x, tile.y,
                                tile.x + TILE_SIZE, tile.y + TILE_SIZE,
                                fill="lime green")

    if game_over:
        canvas.create_text(WINDOW_WIDTH/2, WINDOW_HEIGHT/2,
                           font=("Arial", 20),
                           text=f"Game Over: {score}",
                           fill="white")
    else:
        canvas.create_text(40, 20,
                           font=("Arial", 12),
                           text=f"Score: {score}",
                           fill="white")

    window.after(100, draw)


# -------------------
# START MENU
# -------------------

def start_game():
    start_frame.destroy()
    draw()

start_frame = tkinter.Frame(window, bg="black")
start_frame.place(relwidth=1, relheight=1)

title = tkinter.Label(start_frame,
                      text="SNAKE GAME",
                      font=("Arial", 30),
                      fg="white",
                      bg="black")

title.pack(pady=120)

play_button = tkinter.Button(start_frame,
                             text="PLAY",
                             font=("Arial", 20),
                             width=10,
                             command=start_game)

play_button.pack()

window.bind("<KeyRelease>", change_direction)

window.mainloop()