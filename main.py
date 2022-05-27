import asyncio
import curses
import os
import random
import time
from glob import glob
from itertools import cycle

from curses_tools import draw_frame, read_controls, get_frame_size
from fire_animation import fire

TIC_TIMEOUT = 0.1
FRAMES_PATH = 'frames/'
BORDER_SIZE = 1


def get_frames(path):
    os.chdir(path)
    frames_names = glob('*.txt')
    frames = []
    for name in frames_names:
        frame = get_frame_from_file(name)
        frames.append(frame)
    return(frames)


def get_frame_from_file(path):
    with open(path, "r") as file:
        frame = file.read()
    return frame


def change_coordinates(canvas, pos_row_y, pos_col_x, frame_col_x_min, 
                       frame_col_x_max, frame_row_y_min, frame_row_y_max):
    cols_y_dir, rows_x_dir, _ = read_controls(canvas)
    pos_col_x += rows_x_dir
    pos_row_y += cols_y_dir
    pos_col_x = min(pos_col_x, frame_col_x_max)
    pos_col_x = max(pos_col_x, frame_col_x_min)
    pos_row_y = min(pos_row_y, frame_row_y_max)
    pos_row_y = max(pos_row_y, frame_row_y_min)

    return pos_row_y, pos_col_x


async def animate_spaceship(canvas, frames, start_row, start_column):
    frames_cycle = cycle(frames)
    border_size = BORDER_SIZE
    height, width = canvas.getmaxyx()
    current_frame = next(frames_cycle)
    
    frame_size_y, frame_size_x = get_frame_size(current_frame)

    frames_center_limits = {
        "frame_col_x_min": border_size,
        "frame_col_x_max": width - frame_size_x - border_size,
        "frame_row_y_min": border_size,
        "frame_row_y_max": height - frame_size_y - border_size
    }

    col_x_frame = start_column - round(frame_size_x / 2)
    row_y_frame = start_row - round(frame_size_y / 2)
    for frame in frames_cycle:
        row_y_frame, col_x_frame = change_coordinates(canvas, row_y_frame, col_x_frame,
                                                      **frames_center_limits)
        draw_frame(canvas, row_y_frame, col_x_frame, frame)
        await go_to_sleep(0.2)
        draw_frame(canvas, row_y_frame, col_x_frame, frame, negative=True)


def stars_generator(height, width, amount_stars=250):
    all_coords_in_string = []
    for _ in range(amount_stars):
        y_pos = random.randint(1, height - 2)
        x_pos = random.randint(1, width - 2)
        symbol = random.choice(['+', '*', '.', ':'])
        # пишем координаты всех звезд, чтобы не было повторов, иначе будут артефакты
        coords_in_string = ",".join([str(y_pos), str(x_pos)])
        if  coords_in_string in all_coords_in_string:
            amount_stars += 1
            continue
        else:
            all_coords_in_string.append(coords_in_string)
        yield y_pos, x_pos, symbol 


async def go_to_sleep(seconds):
    iteration_count = int(seconds * 10)
    for _ in range(iteration_count):
        await asyncio.sleep(0)


async def blink(canvas, row, column, symbol='*', phase=0):
    while True:
        if phase == 0:
            canvas.addstr(row, column, symbol, curses.A_DIM)
            await go_to_sleep(2)
            phase += 1

        if phase == 1:
            canvas.addstr(row, column, symbol)
            await go_to_sleep(0.3)
            phase += 1

        if phase == 2:
            canvas.addstr(row, column, symbol, curses.A_BOLD)
            await go_to_sleep(0.5)
            phase += 1

        if phase == 3:
            canvas.addstr(row, column, symbol)
            await go_to_sleep(0.3)
            phase = 0


def draw(canvas):
    curses.initscr()
    curses.curs_set(False)
    canvas.border()
    canvas.nodelay(True)
    height, width = canvas.getmaxyx()
    
    coroutines = [blink(canvas, row, column, symbol, phase=random.randint(0, 3))
                  for row, column, symbol in stars_generator(height, width)]
    start_row = round(height / 2)
    start_column = round(width / 2)
    frames = get_frames(path=FRAMES_PATH)
    coroutines.append(animate_spaceship(canvas, frames, start_row, start_column))
    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
                canvas.refresh()
            except StopIteration:
                coroutines.remove(coroutine)
        if len(coroutines) == 0:
            break
        time.sleep(TIC_TIMEOUT)

    
if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
