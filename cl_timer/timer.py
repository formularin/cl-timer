import curses
import json
from os import mkdir
from os.path import isfile, dirname
from pathlib import Path
import signal
import subprocess
import sys
import time

OUTER_PACKAGE_DIR = dirname(dirname(__file__))
if OUTER_PACKAGE_DIR not in sys.path:
    sys.path.append(OUTER_PACKAGE_DIR)

from cl_timer.art import (
    DISCLAIMER,
    TIMER_BACKGROUND,
    TITLE_ART,
)
from cl_timer.graphics import (
    Canvas, Char, Cursor, CoverUpImage,
    Image, InputLine, Scramble,
    CommandInput, NumberDisplay
)
from cl_timer.interpreter import command_line
from cl_timer.scramble import generate_scramble
from cl_timer.utils import (
    add_zero, ask_for_input,
    CommandSyntaxError, display_stats,
    display_text, ExitCommandLine,
    ExitException, MutableString
)

HOME = str(Path.home())

try:
    mkdir(f'{HOME}/.cl-timer')
except FileExistsError:
    pass

settings = {
    'puzzle': '3',
    'scramble-length': '20'
}

aliases = {}

char = lambda string: Char.fromstring(string)


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
    if not isfile(session_file.string):
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
    if not isfile(settings_file.string):
        with open(settings_file.string, 'w+') as f:
            json.dump(settings, f)
    
    with open(settings_file.string, 'r') as f:
        for key, value in json.load(f).items():
            settings[key] = value

    display_text(stdscr, DISCLAIMER)

    def add_time(t):
        """
        Add new solve with time of `t`
        """

        times.append(t)

        # update number display to show real time
        number_display.time = t
        number_display.update()

        # generate new scramble and update scramble_image
        new_scramble = generate_scramble(int(settings['puzzle']),
                                    int(settings['scramble-length']))
        scrambles.append(new_scramble)
        scramble_image.clear()
        scramble_image.chars = char(new_scramble)

        ao5, ao12 = update_stats()

        with open(session_file.string, 'a') as f:
            if len(times) == 1:
                f.write(f'{add_zero(t)}\t{ao5}\t{ao12}\t{new_scramble}')
            else:
                f.write(f'\n{add_zero(t)}\t{ao5}\t{ao12}\t{new_scramble}')
        
    def calculate_average(solve, length):
        """
        Returns average of `length` during `solve`

        Looks through times list and finds last `length` solves before `solve`
        Excludes best and worst times, and returns average of the rest.
        """
        if len(times[:solve]) < length:
            # `length` solves haven't been done yet.
            return ''
        else:
            latest_average = times[solve - length:]  # list of last `length` solves
            latest_average, _ = convert_to_float(latest_average, "average")
            if len(latest_average) < (length - 1):
                return 'DNF'
            if len(latest_average) == length:
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

    if isfile(f'{HOME}/.cl-timer_rc'):
        with open(f'{HOME}/.cl-timer_rc', 'r') as f:
            rc_commands = f.read().strip().split('\n')
            rc_commands.remove('')
        for command in rc_commands:
            try:
                command_line(canvas, stdscr, settings, scramble_image, settings_file, session_file, times, ao5s, ao12s,
                            scrambles, session, session_name_image, update_stats, add_time, calculate_average, aliases,
                            True, command)
            except CommandSyntaxError:
                pass
    else:
        with open(f'{HOME}/.cl-timer_rc', 'w+') as f:
            pass
    
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
                command_line(canvas, stdscr, settings, scramble_image,
                             settings_file, session_file, times, ao5s,
                             ao12s, scrambles, session, session_name_image,
                             update_stats, add_time, calculate_average, aliases)
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

                add_time(t)
                

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

if __name__ == '__main__':
    main()