import curses
import json
import os
from pathlib import Path
import signal
import string
import subprocess
import time

from cl_timer.art import (
    DISCLAIMER,
    TIMER_BACKGROUND,
    TITLE_ART,
    STATS
)
from cl_timer.graphics import (
    Canvas, Char, Cursor, CoverUpImage,
    Image, InputLine, Scramble,
    CommandInput, NumberDisplay
)
from cl_timer.scramble import generate_scramble


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


class CommandSyntaxError(Exception):
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


def convert_to_float(lst, purpose):
    """
    Returns list of all float-convertable values of `lst`,
    along with length of new list
    """
    float_times = []
    len_times = 0
    for t in lst:
        if (str(t)[:3] != 'DNF') and (t != '') and (str(t)[-1] != '+'):
            float_times.append(float(t))
            len_times += 1
        elif str(t)[-1] == '+':
            if purpose == 'average':
                float_times.append(float(t[:-1]))
                len_times += 1
            elif purpose == 'single':
                float_times.append(t)
                len_times += 1
    return float_times, len_times


def display_stats(stdscr, solve, times, ao5s, ao12s, scrambles):
    """
    Displays to screen stats about the solve with index `solve` - 1
    """
    i = solve - 1
    string = STATS % (solve, times[i], ao5s[i], ao12s[i], scrambles[i])
    display_text(stdscr, string)


def mainloops(stdscr):
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

    session_file = MutableString(f'{HOME}/.cl-timer/{session.string}')
    if not os.path.isfile(session_file.string):
        with open(session_file.string, 'w+') as f:
            pass
    
    with open(session_file.string, 'r') as f:
        time_lines = [line.split('\t') for line in f.read().split('\n')]

    if [''] in time_lines:
        time_lines.remove([''])

    for line in time_lines:
        times.append(line[0])
        ao5s.append(line[1])
        ao12s.append(line[2])
        scrambles.append(line[3])

    settings_file = MutableString(f'{session_file.string}-settings.json')
    if not os.path.isfile(settings_file.string):
        with open(settings_file.string, 'w+') as f:
            json.dump(settings, f)
    
    with open(settings_file.string, 'r') as f:
        for key, value in json.load(f).items():
            settings[key] = value

    display_text(stdscr, DISCLAIMER)

    def delete(solve):
        """
        Removes all records of solve at index `solve`
        """
        # remove from lists of data
        times.pop(solve - 1)
        ao5s.pop(solve - 1)
        ao12s.pop(solve - 1)
        scrambles.pop(solve - 1)

        # remove from session file
        with open(session_file.string, 'r') as f:
            lines = f.read().split('\n')
        lines.pop(solve - 1)
        with open(session_file.string, 'w') as f:
            f.write('\n'.join(lines))

    def dnf():
        """
        Flags latest solve as DNF
        """
        # update `times`
        solve_time = times[-1]
        times[-1] = f'DNF({solve_time})'
        ao5s.pop(-1)
        ao12s.pop(-1)

        # update session file
        with open(session_file.string, 'r') as f:
            lines = [line.split('\t') for line in f.read().split('\n')]
        if [''] in lines:
            lines.remove([''])
        lines[-1][0] = f'DNF({solve_time})'
        with open(session_file.string, 'w') as f:
            f.write('\n'.join(['\t'.join(line) for line in lines]))

    def plus_two():
        """
        Adds two to the value of the latest solves,
        while also marking it as a plus two
        """
        # udpate `times`
        solve_time = times[-1]
        times[-1] = add_zero(round(float(solve_time) + 2, 2)) + '+'
        ao5s.pop(-1)
        ao12s.pop(-1)

        # update session file
        with open(session_file.string, 'r') as f:
            lines = [line.split('\t') for line in f.read().split('\n')]
        if [''] in lines:
            lines.remove([''])
        lines[-1][0] = add_zero(round(float(solve_time) + 2, 2)) + '+'
        with open(session_file.string, 'w') as f:
            f.write('\n'.join(['\t'.join(line) for line in lines]))
        
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
            latest_average, _ = convert_to_float(latest_average, "average")
            if len(latest_average) < 4:
                return 'DNF'
            if len(latest_average) == 4:
                latest_average.remove(max(latest_average))
            latest_average.remove(min(latest_average))

            # calculate average and add zero if it doesn't go to 100ths place.
            
            return add_zero(round(sum(latest_average) / len(latest_average), 2))

    def get_session_mean():
        """
        Returns mean of all solves in session
        """
        try:
            float_times, len_times = convert_to_float(times, 'average')
            return add_zero(round(sum(float_times) / len_times, 2))
        except ZeroDivisionError:
            return ""

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
            converted_times, _ = convert_to_float(times, 'single')
            float_times = [float(t[:-1]) if isinstance(t, str) else t for t in converted_times]
            best = converted_times[float_times.index(min(float_times))]
            if isinstance(best, float):
                return add_zero(best)
        except ValueError as e:
            return ""
        return best

    def get_worst_time():
        try:
            converted_times, _ = convert_to_float(times, 'single')
            float_times = [float(t[:-1]) if isinstance(t, str) else t for t in converted_times]
            worst = converted_times[float_times.index(max(float_times))]
            if isinstance(worst, float):
                return add_zero(worst)
        except ValueError as e:
            return ""
        return worst

    def update_stats():
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

        len_successes = 0
        for t in times:
            if not ((isinstance(t, str)) and (t[:3] == 'DNF')):
                len_successes += 1

        number_of_times_image.chars = char(f'Number of Times: {len_successes}/{len(times)}')
        session_mean = get_session_mean()
        session_mean_image.chars = char(f'Session Mean: {session_mean}')

        return ao5, ao12

    def command_line():
        """
        Inspired by vim...
        """

        def show_error_message(string):
            Image(canvas, 0, len(canvas.grid) - 1, char(string)).render()
            raise CommandSyntaxError

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
            if words[0] == 's':
                
                if len(words) != 3:
                    if len(words) == 1:
                        show_error_message('`s` takes exactly 2 arguments - 0 were given')
                    else:
                        if words[1] in ['p', 'sl']:
                            show_error_message(f'`s {words[1]}` takes 1 argument - {len(words) - 1} were given')
                
                if words[1] in ['p', 'sl']:
                    if words[1] == 'p':
                        try:
                            if not (int(words[2]) in [i for i in range(2, 8)]):
                                show_error_message('`s p` takes an integer between 2 and 7 (inclusive) as an argument')
                        except ValueError:
                            show_error_message('`s p` takes an integer between 2 and 7 (inclusive) as an argument')
                    if words[1] == 'sl':
                        try:
                            int(words[2])
                        except ValueError:
                            show_error_message(f'invalid integer value: {words[2]}')
                else:
                    show_error_message(f'`s` - invalid argument: "{words[1]}"')

                if words[1] == 'sl':
                    settings['scramble-length'] = words[2]
                elif words[1] == 'p':
                    settings['puzzle'] = words[2]

                new_scramble = generate_scramble(int(settings['puzzle']),
                                                int(settings['scramble-length']))
                scramble_image.chars = char(new_scramble)

                with open(settings_file.string, 'w') as f:
                    json.dump(settings, f)
                    
            elif words[0] == 'i':
                if len(words) == 1:
                    subprocess.call(['vim', session_file.string])
                elif len(words) == 2:
                    try:
                        if not (int(words[1]) in range(1, len(times) + 1)):
                            show_error_message(f'invalid integer value: `{int(words[1])}`')
                    except ValueError:
                        show_error_message('`i` takes an integer as an argument')
                    display_stats(stdscr, int(words[1]), times, ao5s, ao12s, scrambles)
                else:
                    show_error_message(f'`i` takes either 0 or 1 argument(s) - {len(words) - 1} were given')

            elif words[0] == 'c':

                if len(words) != 2:
                    show_error_message(f'`c` takes exactly 1 argument - {len(words) - 1} were given')

                for c in words[1]:
                    if c not in string.printable[:-5]:
                        show_error_message(f'invalid file name: {words[1]}')
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

                update_stats()
            
            elif words[0] == 'rm':

                if len(words) != 2:
                    show_error_message(f'`rm` takes exactly 1 argument - {len(words) - 1} were given')

                try:
                    if int(words[1]) not in range(1, len(times) + 1):
                        show_error_message(f'invalid integer value: {words[1]}')
                except ValueError:
                    if words[1] == 'all':
                        ip = InputLine(canvas, "Are you sure you want to delete all the times in this session? (y/n) ")
                        answer = ask_for_input(
                            stdscr, canvas, ip, Cursor(canvas), True)
                        if answer == 'y':
                            for _ in range(1, len(times[:]) + 1):
                                delete(1)
                            update_stats()
                            continue
                        else:
                            continue
                    else:
                        show_error_message(f'invalid integer value: {words[1]}')

                delete(int(words[1]))
                update_stats()
                
            elif words[0] == 'd':

                if len(words) != 1:
                    show_error_message(f'`d` takes exactly 0 arguements - {len(words) - 1} were given')

                dnf()
                update_stats()        

            elif words[0] == 'p':

                if len(words) != 1:
                    show_error_message(f'`p` takes exactly 0 arguements - {len(words) - 1} were given')

                plus_two()
                update_stats()
                
            elif words[0] == 'q':

                if len(words) != 1:
                    show_error_message(f'`q` takes exactly 0 arguements - {len(words) - 1} were given')

                raise ExitException()

            else:  # command was not recognized
                show_error_message(f'{words[0]}: Invalid command')
                
    session_name_image = Image(canvas, 0, 0, char(session.string))
    scramble_image = Scramble(canvas, 0, 2, char(
        generate_scramble(int(settings['puzzle']),
        int(settings['scramble-length']))))
    scramble_image.render()

    number_display = NumberDisplay(canvas, 15, 7)
    timer_background = Image(canvas, 0, 5, char(TIMER_BACKGROUND))

    ao5_image = CoverUpImage(canvas, 51, 6, char(f'AO5: {calculate_average(len(times), 5)}'))
    ao12_image = CoverUpImage(canvas, 51, 7, char(f'AO12: {calculate_average(len(times), 12)}'))
    best_ao5_image = CoverUpImage(canvas, 51, 8, char(f'Best AO5: {get_best_average(5)}'))
    best_ao12_image = CoverUpImage(canvas, 51, 9, char(f'Best AO12: {get_best_average(12)}'))
    best_time_image = CoverUpImage(canvas, 51, 10, char(f'Best time: {get_best_time()}'))
    worst_time_image = CoverUpImage(canvas, 51, 11, char(f'Worst time: {get_worst_time()}'))

    len_successes = 0
    for t in times:
        if not ((isinstance(t, str)) and (t[:3] == 'DNF')):
            len_successes += 1
    number_of_times_image = CoverUpImage(canvas, 51, 12, char(f'Number of Times: {len_successes}/{len(times)}'))
    
    session_mean_image = CoverUpImage(canvas, 51, 13, char(f'Session Mean: {get_session_mean()}'))
    
    ao5_image.render()
    ao12_image.render()
    best_ao5_image.render()
    best_ao12_image.render()
    best_time_image.render()
    worst_time_image.render()
    number_of_times_image.render()
    session_mean_image.render()

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
            try:
                command_line()
            except CommandSyntaxError:
                pass
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
                scramble_image.chars = char(new_scramble)

                ao5, ao12 = update_stats()

                with open(session_file.string, 'a') as f:
                    if len(times) == 1:
                        f.write(f'{add_zero(t)}\t{ao5}\t{ao12}\t{new_scramble}')
                    else:
                        f.write(f'\n{add_zero(t)}\t{ao5}\t{ao12}\t{new_scramble}')

        session_name_image.render()
        
        timer_background.render()
        number_display.render()

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

def main():
    try:
        curses.wrapper(mainloops)
    except ExitException:
        subprocess.call(['clear'])