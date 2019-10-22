import curses
import getpass
import os
import signal
import time

from art import TIMER_BACKGROUND, TITLE_ART
from graphics import Canvas, Cursor, Image, InputLine, NumberDisplay, Char
from scramble import generate_scramble


import logging
import timeit


logging.basicConfig(filename='cl-timer.log', level=logging.INFO)


char = lambda string: Char.fromstring(string)

HOME = f'/Users/{getpass.getuser()}'

try:
    os.mkdir(f'{HOME}/.cl-timer')
except FileExistsError:
    pass


class ExitException(Exception):
    """
    Tells the program when to exit
    """


def ask_for_input(stdscr, canvas, input_line, cursor):
    """
    Uses graphics.InputLine object to get input from user.
    """
    frame = 0
    while True:

        key = stdscr.getch()

        if not input_line.submitted:

            input_line.type_char(key)
            cursor.move(0, input_line.cursor_index)
            if frame % 50 == 0:
                cursor.toggle_char()

            input_line.render()
            cursor.render()

        else:
            cursor.hide()
            break

        stdscr.clear()
        stdscr.addstr(canvas.display)
        stdscr.refresh()

        frame += 1
        time.sleep(0.01)

    return input_line.value


def main(stdscr):
    """
    Includes all mainloops for the app.
    """

    times = []
    session_file = ""
    def signal_handler(sig, frame):
        """
        What to do in case of KeyboardInterrupt

        Writes times to session file
        (saving file interaction to the end saves time during frames.)
        """
        logging.info(times)
        if times != [] and session_file != "":
            list_string_times = [list(str(time)) for time in times]
            for time in list_string_times:
                if len(time[time.index('.') + 1:]) == 1:
                    time.append('0')
            string_of_times = '\n'.join(''.join(time) for time in list_string_times)
            with open(session_file, 'w') as f:
                f.write(string_of_times)
        raise ExitException()

    signal.signal(signal.SIGINT, signal_handler)

    curses.curs_set(0)  # hide cursor (I have my own)
    stdscr.nodelay(True)  # makes stdscr.getch() non-blocking

    canvas = Canvas(curses.LINES - 1, curses.COLS - 1)
    cursor = Cursor(canvas)

    while True:

        key = stdscr.getch()

        if key != -1:
            break

        stdscr.clear()
        stdscr.addstr(TITLE_ART)
        stdscr.refresh()

        time.sleep(0.01)

    # sessions are groups of solves, stored in files in ~/.cl-timer
    # if this is a new session, create a new file, if not, use an existing one.

    session_name_input = InputLine(canvas, 'session name: ')
    session = ask_for_input(stdscr, canvas, session_name_input, cursor)
    
    if not os.path.isfile(f'{HOME}/.cl-timer/{session}'):
        with open(f'{HOME}/.cl-timer/{session}', 'w+') as f:
            pass
    session_file = f'{HOME}/.cl-timer/{session}'
    
    with open(session_file, 'r') as f:
        times = [float(i) for i in f.read().split('\n')[1:]]

    def calculate_average(length):
        """
        Returns current average of `length`

        Looks through session file and finds last `length` solves.
        Excludes best and worst times, and return average of the rest.
        """
        if len(times) < length:
            # `length` solves haven't been done yet.
            return ''
        else:
            latest_average = times[len(times) - length:]  # list of last `length` solves
            latest_average.remove(max(latest_average))
            latest_average.remove(min(latest_average))

            # calculate average and add zero if it doesn't go to 100ths place.
            average_chars = list(str(round(sum(latest_average) / (length - 2), 2)))
            if len(average_chars[average_chars.index('.'):]) < 2:
                average_chars.append('0')
            
            return ''.join(average_chars)

    def get_best_time():
        try:
            best = str(min(times))
        except ValueError:
            return ""
        return best

    def get_worst_time():
        try:
            worst = str(max(times))
        except ValueError:
            return ""
        return worst

    session_name_image = Image(canvas, 0, 0, char(session))
    scramble_image = Image(canvas, 0, 2, char(generate_scramble()))

    number_display = NumberDisplay(canvas, 15, 5)
    timer_background = Image(canvas, 0, 3, char(TIMER_BACKGROUND))

    ao5_image = Image(canvas, 51, 4, char(f'AO5: {calculate_average(5)}'))
    ao12_image = Image(canvas, 51, 5, char(f'AO12: {calculate_average(12)}'))
    best_time_image = Image(canvas, 51, 6, char(f'Best time: {get_best_time()}'))
    worst_time_image = Image(canvas, 51, 7, char(f'Worst time: {get_worst_time()}'))

    timer_running = False
    delay = 0  # how far behind the program is
    while True:
        
        # to make sure each frame is exactly 0.01 secs
        start_time = time.time()

        key = stdscr.getch()

        if key == 32:  # spacebar
            if timer_running:

                timer_running = False

                t = round(number_display.time, 2)
                times.append(t)

                new_scramble = generate_scramble()
                scramble_image.chars = char(new_scramble)

                ao5 = calculate_average(5)
                ao5_image.chars = char(f'AO5: {ao5}')

                ao12 = calculate_average(12)
                ao12_image.chars = char(f'AO12: {ao12}')

                best_time = get_best_time()
                best_time_image.chars = char(f'Best time: {best_time}')

                worst_time = get_worst_time()
                worst_time_image.chars = char(f'Worst time: {worst_time}')
            else:
                timer_running = True
                number_display.reset()

        session_name_image.render()
        scramble_image.render()
        
        timer_background.render()
        number_display.render()

        ao5_image.render()
        ao12_image.render()
        best_time_image.render()
        worst_time_image.render()

        stdscr.clear()
        stdscr.addstr(canvas.display)
        stdscr.refresh()

        if timer_running:
            number_display.increment()

        # take away from sleep time the amount that will get us back on track
        end_time = time.time()
        duration = end_time - start_time
        if duration > 0.01:
            # duration was longer than ideal sleep time.
            # no time to sleep, add to delay and keep going
            delay += duration - 0.01
        else:
            if delay != 0:
                # if there is delay
                if (delay) > (0.01 - duration):
                    # the sum of the delay and the duration is longer than ideal sleep time
                    # no time to sleep, subtract from delay and keep going
                    delay -= 0.01 - duration
                else:
                    # we have enough spare time in this frame to completely reset the delay
                    # we are back on track!
                    delay = 0
                    time.sleep((0.01 - duration) - delay)
            else:
                # there is no delay, just sleep normally, but make sure the frame is exactly 0.01 secs long!
                time.sleep(0.01 - duration)

if __name__ == '__main__':

    try:
        curses.wrapper(main)
    except ExitException:
        pass

# TODO:
# test to see if solve times are accurate, and update time every 10 frames
# at the end display the correct time