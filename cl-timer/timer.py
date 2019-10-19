import curses
import logging
import signal
import time
import os
import getpass

import art
import graphics
import scramble


HOME = f'/Users/{getpass.getuser()}'

try:
    os.mkdir(f'{HOME}/.cl-timer')
except FileExistsError:
    pass


logging.basicConfig(filename='cl-timer.log', level=logging.INFO)


class ExitException(Exception):
    """Tells the program when to exit"""


def signal_handler(sig, frame):
    raise ExitException()


def main(stdscr):
    """
    Mainloop for the program
    """

    curses.curs_set(0)
    stdscr.nodelay(True)

    canvas = graphics.Canvas(curses.LINES - 1, curses.COLS - 1)
    cursor = graphics.Cursor(canvas)

    while True:

        key = stdscr.getch()

        if key != -1:
            break

        stdscr.clear()
        stdscr.addstr(art.TITLE_ART)
        stdscr.refresh()

        time.sleep(0.01)

    session_name_input = graphics.InputLine(canvas, "session name: ")

    frame = 0
    while True:

        key = stdscr.getch()

        if not session_name_input.submitted:

            session_name_input.type_char(key)
            cursor.move(0, session_name_input.cursor_index)
            if frame % 50 == 0:
                cursor.toggle_char()

            session_name_input.render()
            cursor.render()

        else:
            cursor.hide()
            break

        stdscr.clear()
        stdscr.addstr(canvas.display)
        stdscr.refresh()

        frame += 1
        time.sleep(0.01)

    session = session_name_input.value
    with open(f'{HOME}/.cl-timer/{session}', 'w+') as f:
        pass
    
    session_name_image = graphics.Image(canvas, 0, 0, graphics.Char.fromstring(session))
    scramble_image = graphics.Image(canvas, 0, 2, graphics.Char.fromstring(scramble.generate_scramble()))
    number_display = graphics.NumberDisplay(canvas, 15, 5)
    timer_background_char_array = graphics.Char.fromstring(art.TIMER_BACKGROUND)
    timer_background = graphics.Image(canvas, 0, 3, timer_background_char_array)
    timer_running = False

    while True:

        key = stdscr.getch()

        if key == 32:  # spacebar
            if timer_running:
                timer_running = False
                with open(f'{HOME}/.cl-timer/{session}', 'a') as f:
                    f.write(''.join([d for d in str(round(number_display.time, 2))]) + '\n')
                new_scramble = scramble.generate_scramble()
                for x, char in enumerate(new_scramble):
                    scramble_image.change(x, 0, char)
            else:
                timer_running = True
                number_display.reset()

        session_name_image.render()
        scramble_image.render()
        timer_background.render()
        number_display.render()
        stdscr.clear()
        stdscr.addstr(canvas.display)
        stdscr.refresh()

        if timer_running:
            number_display.increment()
        time.sleep(0.01)


if __name__ == "__main__":

    signal.signal(signal.SIGINT, signal_handler)

    try:
        curses.wrapper(main)
    except ExitException:
        pass