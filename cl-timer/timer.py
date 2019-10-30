import curses
import os
from pathlib import Path
import signal
import subprocess
import time

from art import (DISCLAIMER, TIMER_BACKGROUND,
                 TITLE_ART, STATS)
from graphics import (Canvas, Char, Cursor, Image,
                      InputLine, NumberDisplay,
                      Scramble, CommandInput)
from scramble import generate_scramble


char = lambda string: Char.fromstring(string)

HOME = str(Path.home())

try:
    os.mkdir(f'{HOME}/.cl-timer')
except FileExistsError:
    pass


class MutableString:
    def __init__(self, string):
        self._string = string

    @property
    def string(self):
        return self._string

    @string.setter
    def string(self, new_string):
        self._string = new_string


class ExitException(Exception):
    """
    Tells the program when to exit
    """

class ExitCommandLine(Exception):
    pass


settings = {
    'puzzle': '3',
    'scramble-length': '20'
}


def ask_for_input(stdscr, canvas, input_line, cursor, command_line=False):
    """
    Uses graphics.InputLine object to get input from user.
    """
    frame = 0
    while True:

        key = stdscr.getch()

        if command_line == True:
            if key == 27:  # escape
                raise ExitCommandLine()

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


def display_stats(stdscr, solve, times, ao5s, ao12s, scrambles):
    """
    Displays to screen stats about the solve with index `solve` - 1
    """
    i = solve - 1
    string = STATS % (solve, times[i], ao5s[i], ao12s[i], scrambles[i])
    display_text(stdscr, string)


def main(stdscr):
    """
    Includes all mainloops for the app.
    """
    def signal_handler(sig, frame):
        """
        What to do in case of KeyboardInterrupt

        Writes times to session file
        (saving file interaction to the end saves time during frames.)
        """
        raise ExitException()

    signal.signal(signal.SIGINT, signal_handler)

    try:
        curses.curs_set(0)  # hide cursor (I have my own)
    except Exception:
        pass
    stdscr.nodelay(True)  # makes stdscr.getch() non-blocking

    canvas = Canvas(curses.LINES - 1, curses.COLS - 1)
    cursor = Cursor(canvas)

    display_text(stdscr, TITLE_ART)

    # sessions are groups of solves, stored in files in ~/.cl-timer
    # if this is a new session, create a new file, if not, use an existing one.

    session_name_input = InputLine(canvas, 'session name: ')
    session = MutableString(ask_for_input(stdscr, canvas, session_name_input, cursor))
    
    times = []
    ao5s = []
    ao12s = []
    scrambles = []
    session_file = ""

    if not os.path.isfile(f'{HOME}/.cl-timer/{session.string}'):
        with open(f'{HOME}/.cl-timer/{session.string}', 'w+') as f:
            pass
    session_file = MutableString(f'{HOME}/.cl-timer/{session.string}')
    
    with open(session_file.string, 'r') as f:
        time_lines = [line.split('\t') for line in f.read().split('\n')][:-1]

    for line in time_lines:
        times.append(line[0])
        ao5s.append(line[1])
        ao12s.append(line[2])
        scrambles.append(line[3])

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

    def update_stats():
        ao5 = calculate_average(len(times), 5)
        ao5s.append(ao5)
        ao5_image.displayed_chars = char(f'AO5: {ao5}')
        ao12 = calculate_average(len(times), 12)
        ao12s.append(ao12)
        ao12_image.displayed_chars = char(f'AO12: {ao12}')
        best_ao5 = get_best_average(5)
        best_ao5_image.displayed_chars = char(f'Best AO5: {best_ao5}')
        best_ao12 = get_best_average(12)
        best_ao12_image.displayed_chars = char(f'Best AO12: {best_ao12}')
        best_time = get_best_time()
        best_time_image.displayed_chars = char(f'Best time: {best_time}')
        worst_time = get_worst_time()
        worst_time_image.displayed_chars = char(f'Worst time: {worst_time}')
        number_of_times_image.displayed_chars = char(f'Number of Times: {len(times)}')

        return ao5, ao12

    def command_line():
        """
        Inspired by vim...
        """

        bg = Image(canvas, 0, 0, char(canvas.display))
        command_inputs = []

        while True:
            try:
                cmd_ipt = CommandInput(canvas)
                command_inputs.append(cmd_ipt)
                command = ask_for_input(
                    stdscr, canvas, cmd_ipt, Cursor(canvas), True)
            except ExitCommandLine:
                for c in command_inputs:
                    c.hide()
                return

            words = command.split(' ')
            if words[0] == 'set':
                settings[words[1]] = words[2]

                if words[1] in ['puzzle', 'scramble-length']:
                    new_scramble = generate_scramble(int(settings['puzzle']),
                                                int(settings['scramble-length']))
                    scramble_image.displayed_chars = char(new_scramble)
                    scramble_image.render()
            elif words[0] == 'info':
                try:
                    display_stats(stdscr, int(words[1]), times, ao5s, ao12s, scrambles)
                except IndexError:
                    subprocess.call(['vim', session_file.string])
            elif words[0] == 'session':

                session.string = words[1]
                session_file.string = f"{HOME}/.cl-timer/{words[1]}"
                session_name_image.displayed_chars = char(words[1])
                session_name_image.render()

                if not os.path.isfile(session_file.string):
                    with open(session_file.string, 'w+') as f:
                        pass

                with open(session_file.string, 'r') as f:
                    time_lines = [line.split('\t') for line in f.read().split('\n')][:-1]

                s = len(times)

                for lst in [times, ao5s, ao12s, scrambles]:
                    for _ in range(s):
                        lst.pop(0)

                for line in time_lines:
                    times.append(line[0])
                    ao5s.append(line[1])
                    ao12s.append(line[2])
                    scrambles.append(line[3])

                ao5, ao12 = update_stats()

                ao5_image.render()
                ao12_image.render()
                best_ao5_image.render()
                best_ao12_image.render()
                best_time_image.render()
                worst_time_image.render()
                number_of_times_image.render()
                
                
    session_name_image = Image(canvas, 0, 0, char(session.string))
    scramble_image = Scramble(canvas, 0, 2, char(
        generate_scramble(int(settings['puzzle']),
        int(settings['scramble-length']))))

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
    spacebar_pressed = False
    last_25_keys = [-1 for _ in range(25)]

    solve_start_time = 0
    frame = 0
    while True:

        # to make sure each frame is exactly 0.01 secs
        start_time = time.time()

        key = stdscr.getch()

        if key == 58:  # :
            command_line()
            continue

        if not timer_running:
            if key == 32:
                solve_start_time = time.time()
        last_25_keys.append(key)
        last_25_keys.pop(0)

        if not timer_running:

            if spacebar_pressed:
                if 32 in last_25_keys:
                    time.sleep(0.01)
                    continue
                else:
                    spacebar_pressed = False

                    timer_running = True
                    number_display.reset()

            else:
                if key == 32:  # spacebar
                    spacebar_pressed = True

        else:
            if key == 32:
                frame = 0
                timer_running = False

                t = round(time.time() - solve_start_time, 2)
                times.append(t)

                # update number display to show real time
                number_display.time = t
                number_display.update()

                # generate new scramble and update scramble_image
                new_scramble = generate_scramble(int(settings['puzzle']),
                                            int(settings['scramble-length']))
                scrambles.append(new_scramble)
                scramble_image.displayed_chars = char(new_scramble)

                ao5, ao12 = update_stats()

                with open(session_file.string, 'a') as f:
                    if len(times) == 1:
                        f.write(f'{add_zero(t)}\t{ao5}\t{ao12}\t{new_scramble}')
                    else:
                        f.write(f'\n{add_zero(t)}\t{ao5}\t{ao12}\t{new_scramble}')

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
            number_display.time = time.time() - solve_start_time
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
