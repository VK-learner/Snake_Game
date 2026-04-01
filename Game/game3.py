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


window = tkinter.Tk()
window.title("Snake Game")
window.resizable(False, False)

canvas = tkinter.Canvas(window, bg="black", width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
canvas.pack()
window.update()


window_width = window.winfo_width()
window_height = window.winfo_height()

screen_width = window.winfo_screenwidth()
screen_height = window.winfo_screenheight()

window_x = int((screen_width / 2) - (window_width / 2))
window_y = int((screen_height / 2) - (window_height / 2))

window.geometry(f"{window_width}x{window_height}+{window_x}+{window_y}")


# load images
frog_img = tkinter.PhotoImage(file="frog.png")
rat_img = tkinter.PhotoImage(file="rat.png")


snake = Tile(5*TILE_SIZE, 5*TILE_SIZE)
food = Tile(10*TILE_SIZE, 10*TILE_SIZE)

snake_body = []

velocityX = 0
velocityY = 0

game_over = False
score = 0
lives = 3

food_type = random.choice(["rat","frog"])


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
    global snake, food, snake_body, game_over, score, lives, food_type

    if game_over:
        return

    if snake.x < 0 or snake.x >= WINDOW_WIDTH or snake.y < 0 or snake.y >= WINDOW_HEIGHT:
        lives -= 1

        snake.x = 5*TILE_SIZE
        snake.y = 5*TILE_SIZE
        snake_body.clear()

        if lives == 0:
            game_over = True

    for tile in snake_body:
        if snake.x == tile.x and snake.y == tile.y:
            lives -= 1
            snake_body.clear()

            if lives == 0:
                game_over = True

    if snake.x == food.x and snake.y == food.y:

        snake_body.append(Tile(food.x, food.y))

        if food_type == "frog":
            score += 5
        else:
            score += 2

        food.x = random.randint(0, COLS-1) * TILE_SIZE
        food.y = random.randint(0, ROWS-1) * TILE_SIZE

        food_type = random.choice(["rat","frog"])

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

    # draw food
    if food_type == "frog":
        canvas.create_image(food.x, food.y, image=frog_img, anchor="nw")
    else:
        canvas.create_image(food.x, food.y, image=rat_img, anchor="nw")

    # snake head
    canvas.create_rectangle(snake.x, snake.y,
                            snake.x+TILE_SIZE,
                            snake.y+TILE_SIZE,
                            fill="lime")

    for tile in snake_body:
        canvas.create_rectangle(tile.x, tile.y,
                                tile.x+TILE_SIZE,
                                tile.y+TILE_SIZE,
                                fill="lime")

    canvas.create_text(60,20,
                       text=f"Score: {score}",
                       fill="white",
                       font=("Arial",12))

    canvas.create_text(180,20,
                       text=f"Lives: {'❤️'*lives}",
                       fill="red",
                       font=("Arial",12))

    if game_over:

        canvas.create_text(WINDOW_WIDTH/2,
                           WINDOW_HEIGHT/2,
                           text=f"Game Over\nScore: {score}",
                           fill="white",
                           font=("Arial",20))

        canvas.create_text(WINDOW_WIDTH/2,
                           WINDOW_HEIGHT/2+40,
                           text="Press R to Restart | ESC to Exit",
                           fill="yellow",
                           font=("Arial",12))

    else:
        window.after(100, draw)


def restart_game(event=None):
    global snake, food, snake_body, velocityX, velocityY, game_over, score, lives

    snake = Tile(5*TILE_SIZE, 5*TILE_SIZE)
    food = Tile(10*TILE_SIZE, 10*TILE_SIZE)

    snake_body.clear()

    velocityX = 0
    velocityY = 0

    score = 0
    lives = 3

    game_over = False

    draw()


def exit_game(event=None):
    window.destroy()


def start_game():
    start_frame.destroy()
    draw()


start_frame = tkinter.Frame(window, bg="black")
start_frame.place(relwidth=1, relheight=1)

title = tkinter.Label(start_frame,
                      text="SNAKE GAME",
                      font=("Arial",32),
                      fg="white",
                      bg="black")

title.pack(pady=120)

play_button = tkinter.Button(start_frame,
                             text="PLAY",
                             font=("Arial",20),
                             width=10,
                             command=start_game)

play_button.pack(pady=10)

exit_button = tkinter.Button(start_frame,
                             text="EXIT",
                             font=("Arial",20),
                             width=10,
                             command=exit_game)

exit_button.pack()


window.bind("<KeyRelease>", change_direction)
window.bind("r", restart_game)
window.bind("<Escape>", exit_game)

window.mainloop()