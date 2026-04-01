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


# window
window = tkinter.Tk()
window.title("Snake Game")
window.resizable(False, False)

canvas = tkinter.Canvas(window, bg="black", width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
canvas.pack()
window.update()


# center window
window_width = window.winfo_width()
window_height = window.winfo_height()

screen_width = window.winfo_screenwidth()
screen_height = window.winfo_screenheight()

window_x = int((screen_width / 2) - (window_width / 2))
window_y = int((screen_height / 2) - (window_height / 2))

window.geometry(f"{window_width}x{window_height}+{window_x}+{window_y}")


# game variables
snake = Tile(5*TILE_SIZE, 5*TILE_SIZE)
food = Tile(10*TILE_SIZE, 10*TILE_SIZE)

snake_body = []

velocityX = 0
velocityY = 0

game_over = False
score = 0


def change_direction(e):
    global velocityX, velocityY

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
    global snake, food, snake_body, game_over, score

    if game_over:
        return

    # wall collision
    if snake.x < 0 or snake.x >= WINDOW_WIDTH or snake.y < 0 or snake.y >= WINDOW_HEIGHT:
        game_over = True

    # self collision
    for tile in snake_body:
        if snake.x == tile.x and snake.y == tile.y:
            game_over = True

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
            prev = snake_body[i-1]
            tile.x = prev.x
            tile.y = prev.y

    snake.x += velocityX * TILE_SIZE
    snake.y += velocityY * TILE_SIZE


def draw():

    move()

    canvas.delete("all")

    # food
    canvas.create_rectangle(food.x, food.y,
                            food.x+TILE_SIZE,
                            food.y+TILE_SIZE,
                            fill="red")

    # snake head
    canvas.create_rectangle(snake.x, snake.y,
                            snake.x+TILE_SIZE,
                            snake.y+TILE_SIZE,
                            fill="lime")

    # snake body
    for tile in snake_body:
        canvas.create_rectangle(tile.x, tile.y,
                                tile.x+TILE_SIZE,
                                tile.y+TILE_SIZE,
                                fill="lime")

    if game_over:

        canvas.create_text(WINDOW_WIDTH/2,
                           WINDOW_HEIGHT/2 - 40,
                           text=f"Game Over\nScore: {score}",
                           fill="white",
                           font=("Arial", 20))

        canvas.create_text(WINDOW_WIDTH/2,
                           WINDOW_HEIGHT/2 + 20,
                           text="Press R to Restart | ESC to Exit",
                           fill="yellow",
                           font=("Arial", 12))

    else:

        canvas.create_text(50, 20,
                           text=f"Score: {score}",
                           fill="white",
                           font=("Arial", 12))

        window.after(100, draw)


def restart_game(event=None):
    global snake, food, snake_body, velocityX, velocityY, game_over, score

    snake = Tile(5*TILE_SIZE, 5*TILE_SIZE)
    food = Tile(10*TILE_SIZE, 10*TILE_SIZE)

    snake_body.clear()

    velocityX = 0
    velocityY = 0

    game_over = False
    score = 0

    draw()


def exit_game(event=None):
    window.destroy()


# start menu
def start_game():
    start_frame.destroy()
    draw()


start_frame = tkinter.Frame(window, bg="black")
start_frame.place(relwidth=1, relheight=1)

title = tkinter.Label(start_frame,
                      text="SNAKE GAME",
                      font=("Arial", 32),
                      fg="white",
                      bg="black")

title.pack(pady=120)

play_button = tkinter.Button(start_frame,
                             text="PLAY",
                             font=("Arial", 20),
                             width=10,
                             command=start_game)

play_button.pack(pady=10)

exit_button = tkinter.Button(start_frame,
                             text="EXIT",
                             font=("Arial", 20),
                             width=10,
                             command=exit_game)

exit_button.pack()

# key bindings
window.bind("<KeyRelease>", change_direction)
window.bind("r", restart_game)
window.bind("<Escape>", exit_game)

window.mainloop()