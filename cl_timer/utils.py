import time
from os.path import dirname
import sys

OUTER_PACKAGE_DIR = dirname(dirname(__file__))
if OUTER_PACKAGE_DIR not in sys.path:
    sys.path.append(OUTER_PACKAGE_DIR)

from cl_timer.art import STATS

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


def display_stats(stdscr, solve, times, ao5s, ao12s, scrambles):
    """
    Displays to screen stats about the solve with index `solve` - 1
    """
    i = solve - 1
    string = STATS % (solve, times[i], ao5s[i], ao12s[i], scrambles[i])
    display_text(stdscr, string)