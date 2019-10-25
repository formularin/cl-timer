import curses
import getpass
import os
import signal
import time

from art import DISCLAIMER, TIMER_BACKGROUND, TITLE_ART
from graphics import (Canvas, Char, Cursor, Image,
                      InputLine, NumberDisplay, Scramble)
from scramble import generate_scramble


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


def display_text(stdscr, string):
    """
    A simple loop that diplays text until key is pressed
    """

    while True:

        key = stdscr.getch()

        if key != -1:
            break

        stdscr.clear()
        stdscr.addstr(string)
        stdscr.refresh()

        time.sleep(0.01)


def add_zero(number):
    """
    Add a zero if the value doesn't have
    2 digits behind it's decimal point
    """
    if number == '':
        return ''
    else:
        list_number = list(str(number))
        if len(list_number[list_number.index('.') + 1:]) < 2:
            list_number.append('0')
        return ''.join(list_number)


def main(stdscr):
    """
    Includes all mainloops for the app.
    """

    times = []
    ao5s = []
    ao12s = []
    session_file = ""
    def signal_handler(sig, frame):
        """
        What to do in case of KeyboardInterrupt

        Writes times to session file
        (saving file interaction to the end saves time during frames.)
        """
        if times != [] and session_file != "":
            lines = ['\t'.join([t, a5, a12]) for t, a5, a12 in zip(
                *[[add_zero(i) for i in lst] for lst in [times, ao5s, ao12s]])]
            with open(session_file, 'w') as f:
                f.write('\n'.join(lines))
        raise ExitException()

    signal.signal(signal.SIGINT, signal_handler)

    curses.curs_set(0)  # hide cursor (I have my own)
    stdscr.nodelay(True)  # makes stdscr.getch() non-blocking

    canvas = Canvas(curses.LINES - 1, curses.COLS - 1)
    cursor = Cursor(canvas)

    display_text(stdscr, TITLE_ART)

    # sessions are groups of solves, stored in files in ~/.cl-timer
    # if this is a new session, create a new file, if not, use an existing one.

    session_name_input = InputLine(canvas, 'session name: ')
    session = ask_for_input(stdscr, canvas, session_name_input, cursor)
    
    if not os.path.isfile(f'{HOME}/.cl-timer/{session}'):
        with open(f'{HOME}/.cl-timer/{session}', 'w+') as f:
            pass
    session_file = f'{HOME}/.cl-timer/{session}'
    
    with open(session_file, 'r') as f:
        time_lines = [line.split('\t') for line in f.read().split('\n')[:-1]]

    for line in time_lines:
        times.append(line[0])
        ao5s.append(line[1])
        ao12s.append(line[2])

    display_text(stdscr, DISCLAIMER)

    def calculate_average(solve, length):
        """
        Returns average of `length` during `solve`

        Looks through times list and finds last `length` solves before `solve`
        Excludes best and worst times, and returns average of the rest.
        """
        if len(times) < length:
            # `length` solves haven't been done yet.
            return ''
        else:
            latest_average = times[solve - length:]  # list of last `length` solves
            latest_average = [float(i) for i in latest_average]
            latest_average.remove(max(latest_average))
            latest_average.remove(min(latest_average))

            # calculate average and add zero if it doesn't go to 100ths place.
            
            # list of chars of the string version of average rounded to nearest hundredth
            average_chars = list(str(round(sum(latest_average) / (length - 2), 2)))
            if len(average_chars[average_chars.index('.'):]) < 2:
                average_chars.append('0')
            
            return ''.join(average_chars)

    def get_best_average(length):
        """
        Returns best average of `length` in session
        """
        try:
            if length == 5:
                best = add_zero(min([i for i in ao5s if i != '']))
            elif length == 12:
                best = add_zero(min([i for i in ao12s if i != '']))
        except ValueError:
            return ""
        return best

    def get_best_time():
        try:
            best = add_zero(min([float(i) for i in times]))
        except ValueError:
            return ""
        return best

    def get_worst_time():
        try:
            worst = add_zero(max([float(i) for i in times]))
        except ValueError:
            return ""
        return worst

    session_name_image = Image(canvas, 0, 0, char(session))
    scramble_image = Scramble(canvas, 0, 2, char(generate_scramble()))

    number_display = NumberDisplay(canvas, 15, 5)
    timer_background = Image(canvas, 0, 3, char(TIMER_BACKGROUND))

    ao5_image = Image(canvas, 51, 4, char(f'AO5: {calculate_average(len(times), 5)}'))
    ao12_image = Image(canvas, 51, 5, char(f'AO12: {calculate_average(len(times), 12)}'))
    best_ao5_image = Image(canvas, 51, 6, char(f'Best AO5: {get_best_average(5)}'))
    best_ao12_image = Image(canvas, 51, 7, char(f'Best AO12: {get_best_average(12)}'))
    best_time_image = Image(canvas, 51, 8, char(f'Best time: {get_best_time()}'))
    worst_time_image = Image(canvas, 51, 9, char(f'Worst time: {get_worst_time()}'))
    number_of_times_image = Image(canvas, 51, 10, char(f'Number of Times: {len(times)}'))

    timer_running = False
    delay = 0  # how far behind the program is

    solve_start_time = 0
    frame = 0
    while True:
        
        # to make sure each frame is exactly 0.01 secs
        start_time = time.time()

        key = stdscr.getch()

        if key == 32:  # spacebar
            if timer_running:
                
                frame = 0
                timer_running = False

                t = round(time.time() - solve_start_time, 2)
                times.append(t)

                # update number display to show real time
                number_display.time = t
                number_display.update()

                # generate new scramble and update scramble_image
                new_scramble = generate_scramble()
                scramble_image.chars = char(new_scramble)

                # calculate stats and update images on screen
                ao5 = calculate_average(len(times), 5)
                ao5s.append(ao5)
                ao5_image.chars = char(f'AO5: {ao5}')
                ao12 = calculate_average(len(times), 12)
                ao12s.append(ao12)
                ao12_image.chars = char(f'AO12: {ao12}')
                best_ao5 = get_best_average(5)
                best_ao5_image.chars = char(f'Best AO5: {best_ao5}')
                best_ao12 = get_best_average(12)
                best_ao12_image.chars = char(f'Best AO12: {best_ao12}')
                best_time = get_best_time()
                best_time_image.chars = char(f'Best time: {best_time}')
                worst_time = get_worst_time()
                worst_time_image.chars = char(f'Worst time: {worst_time}')
                number_of_times_image.chars = char(f'Number of Times: {len(times)}')

            else:
                timer_running = True
                number_display.reset()
                solve_start_time = time.time()

        session_name_image.render()
        scramble_image.render()
        
        timer_background.render()
        number_display.render()

        ao5_image.render()
        ao12_image.render()
        best_ao5_image.render()
        best_ao12_image.render()
        best_time_image.render()
        worst_time_image.render()
        number_of_times_image.render()

        stdscr.clear()
        stdscr.addstr(canvas.display)
        stdscr.refresh()

        if timer_running:
            # update time to actual time every 0.5 seconds
            if frame % 50 == 0:
                number_display.time = time.time() - solve_start_time
            else:
                number_display.increment()
            
            number_display.update()

        # take away from sleep time the amount that will get us back on track
        duration = time.time() - start_time
        if (duration + delay) > 0.01:
            # can't make it back to on-time right now
            # by not sleeping, we have saved (0.01 - duration) seconds
            delay -= 0.01 - duration
        else:
            time.sleep(0.01 - (duration + delay))
        
        frame += 1

if __name__ == '__main__':

    try:
        curses.wrapper(main)
    except ExitException:
        pass