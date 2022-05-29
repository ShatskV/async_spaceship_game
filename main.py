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
STAR_PHASES_COUNT = 3


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


async def animate_spaceship(canvas, frames, start_row, start_column, border_size):
    frames_cycle = cycle(frames)
    number_of_rows_window, number_of_columns_window = canvas.getmaxyx()
    max_row_window = number_of_rows_window - 1 
    max_column_window = number_of_columns_window - 1

    current_frame = next(frames_cycle)
    
    frame_size_y, frame_size_x = get_frame_size(current_frame)
    # sub 1 because x, y coordinates of starts drawing, when frame width, frame height begin:
    #wwwwwb : w - width of frame (5), b - border (1), right side of window (number of column = 10)
    #456789 : frame must starts from column 4 -  max_column - border - width:  9 - 5 - 1 = 3, 
    # so need to sub 1 (or add 1 to whole expression) from width of frame (same for rows) 
    frames_coords_limits = {
        "frame_col_x_min": border_size,
        "frame_col_x_max": max_column_window - (frame_size_x - 1) - border_size,
        "frame_row_y_min": border_size,
        "frame_row_y_max": max_row_window - (frame_size_y - 1) - border_size
    }

    col_x_frame = start_column - round(frame_size_x / 2)
    row_y_frame = start_row - round(frame_size_y / 2)
    for frame in frames_cycle:
        row_y_frame, col_x_frame = change_coordinates(canvas, row_y_frame, col_x_frame,
                                                      **frames_coords_limits)
        draw_frame(canvas, row_y_frame, col_x_frame, frame)
        await sleep(0.1)
        draw_frame(canvas, row_y_frame, col_x_frame, frame, negative=True)


def generate_stars(max_row_window, max_column_window, border, number_of_stars=250):
    all_stars_coords = []
    for _ in range(number_of_stars):
        y_pos = random.randint(border, max_row_window - border)
        x_pos = random.randint(border, max_column_window - border)
        symbol = random.choice(['+', '*', '.', ':'])
        # save all stars coordinates to avoid coordinates collisions (number of stars will be less then set)
        star_coords = (y_pos, x_pos)
        if  star_coords in all_stars_coords:
            number_of_stars += 1
            continue
        all_stars_coords.append(star_coords)
        yield y_pos, x_pos, symbol 


async def sleep(tic_timeout):
    seconds = int(tic_timeout * 10)
    for _ in range(seconds):
        await asyncio.sleep(0)


async def blink(canvas, row, column, symbol='*', phase=0):
    while True:
        if phase == 0:
            canvas.addstr(row, column, symbol, curses.A_DIM)
            await sleep(2)
            phase += 1

        if phase == 1:
            canvas.addstr(row, column, symbol)
            await sleep(0.3)
            phase += 1

        if phase == 2:
            canvas.addstr(row, column, symbol, curses.A_BOLD)
            await sleep(0.5)
            phase += 1

        if phase == 3:
            canvas.addstr(row, column, symbol)
            await sleep(0.3)
            phase = 0


def draw(canvas):
    curses.initscr()
    curses.curs_set(False)
    # add this varables for sutiation when constans imports from .env
    border_size = BORDER_SIZE
    # phases starts count from 0
    number_of_phases = STAR_PHASES_COUNT
    canvas.border()
    # canvas.box([border_size, border_size])
    canvas.nodelay(True)
    # Return a tuple (y, x) of number of columns and number rows  of the window
    number_of_rows_window, number_of_columns_window = canvas.getmaxyx()
    # sub 1 because rows and column count starts from 0
    max_row_window = number_of_rows_window - 1 
    max_column_window = number_of_columns_window - 1
    coroutines = [blink(canvas, row, column, symbol, phase=random.randint(0, number_of_phases))
                  for row, column, symbol in generate_stars(max_row_window, max_column_window, border_size)]
    start_row = round(max_row_window / 2)
    start_column = round(max_column_window / 2)
    frames = get_frames(path=FRAMES_PATH)
    coroutines.append(animate_spaceship(canvas, frames, start_row, start_column, border_size))
    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
        canvas.refresh()
        if not coroutines:
            break
        time.sleep(TIC_TIMEOUT)

    
if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
