import json
from os.path import dirname, isfile
from pathlib import Path
import string
import subprocess
import sys

OUTER_PACKAGE_DIR = dirname(dirname(__file__))
if OUTER_PACKAGE_DIR not in sys.path:
    sys.path.append(OUTER_PACKAGE_DIR)

from cl_timer.graphics import (
    Char, CommandInput,
    Cursor, Image, InputLine
)
from cl_timer.scramble import generate_scramble
from cl_timer.utils import (
    add_zero, ask_for_input, display_stats,
    CommandSyntaxError, ExitCommandLine,
    ExitException, MutableString
)

HOME = str(Path.home())

char = lambda string: Char.fromstring(string)


def command_line(
        canvas, stdscr, settings, scramble_image, settings_file, session_file,
        times, ao5s, ao12s, scrambles, session, session_name_image, update_stats,
        add_time, calculate_average, aliases, silent=False, command=False):
    """
    Inspired by vim...
    """

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
        ao5s[-1] = calculate_average(len(ao5s), 5)
        ao12s[-1] = calculate_average(len(ao12s), 12)

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
        ao5s[-1] = calculate_average(len(ao5s), 5)
        ao12s[-1] = calculate_average(len(ao12s), 12)

        # update session file
        with open(session_file.string, 'r') as f:
            lines = [line.split('\t') for line in f.read().split('\n')]
        if [''] in lines:
            lines.remove([''])
        lines[-1][0] = add_zero(round(float(solve_time) + 2, 2)) + '+'
        with open(session_file.string, 'w') as f:
            f.write('\n'.join(['\t'.join(line) for line in lines]))

    def show_error_message(string):
        if not silent:
            Image(canvas, 0, len(canvas.grid) - 1, char(string)).render()
        raise CommandSyntaxError

    def interpret(command):
        """
        Performs tasks according to what the command tells it
        """

        if ';' in command:
            for subcommand in command.split(';'):
                interpret(subcommand.strip())
            return

        if command.count('"') % 2 != 0:
            show_error_message('syntax error: odd number of quotes (")')

        if '  ' in command:
            show_error_message('syntax error: command parts separated by more than one space ( )')
        
        words = []
        current_chars = []
        in_quotes = False
        skip = False
        for i, c in enumerate(command):

            if skip:
                skip = False
                continue

            if in_quotes:
                if c == '"':
                    in_quotes = False
                    skip = True
                    words.append(''.join(current_chars))
                    current_chars.clear()
                else:
                    current_chars.append(c)
            else:
                if c == '"':
                    in_quotes = True
                elif c == ' ':
                    words.append(''.join(current_chars))
                    current_chars.clear()
                else:
                    current_chars.append(c)

        if command[-1] != '"':
            words.append(command.split(' ')[-1])

        logging.info(words)

        if words[0] == 'alias':
            if len(words) != 3:
                show_error_message(f'`alias` takes exactly 2 arguments - {len(words) - 1} were given')
            
            if words[1] in ['s', 'i', 'c', 'rm', 'd', 'p', 'q', 'a', 'alias']:
                show_error_message(f'{words[1]} is a command. Choose a different name.')
            
            aliases[words[1]] = words[2].strip()

        elif words[0] == 's':
            
            if len(words) != 3:
                if len(words) == 1:
                    show_error_message('`s` takes exactly 2 arguments - 0 were given')
                else:
                    if words[1] in ['p', 'sl']:
                        show_error_message(f'`s {words[1]}` takes 1 argument - {len(words) - 2} were given')
            
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
            scramble_image.clear()
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
            new_file = False
            session.string = words[1]
            session_file.string = f"{HOME}/.cl-timer/{words[1]}"
            settings_file.string = f"{HOME}/.cl-timer/{words[1]}-settings.json"
            session_name_image.displayed_chars = char(words[1])
            session_name_image.render()
            
            s = len(times)

            for lst in [times, ao5s, ao12s, scrambles]:
                for _ in range(s):
                    lst.pop(0)

            if not isfile(session_file.string):
                with open(session_file.string, 'w+') as f:
                    pass
            else:
                with open(session_file.string, 'r') as f:
                    time_lines = [line.split('\t') for line in f.read().split('\n')]

                for line in time_lines:
                    times.append(line[0])
                    ao5s.append(line[1])
                    ao12s.append(line[2])
                    scrambles.append(line[3])
        
            if isfile(settings_file.string):
                with open(settings_file.string, 'r') as f:
                    for key, value in json.load(f).items():
                        settings[key] = value
            else:
                settings['puzzle'] = '3'
                settings['scramble-length'] = '20'
                with open(settings_file.string, 'w+') as f:
                    json.dump(settings, f)

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
                        return
                    else:
                        return
                else:
                    show_error_message(f'invalid integer value: {words[1]}')

            delete(int(words[1]))

            for i in range(len(ao5s)):
                ao5s[i] = calculate_average(i + 1, 5)
            for i in range(len(ao12s)):
                ao12s[i] = calculate_average(i + 1, 12)

            with open(session_file.string, 'w') as f:
                f.write(
                    '\n'.join(
                        ['\t'.join([str(thing) for thing in 
                            [time, ao5, ao12, scramble]])
                            for time, ao5, ao12, scramble in
                            zip(times, ao5s, ao12s, scrambles)]
                        )
                    )

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

        elif words[0] == 'a':

            if len(words) != 2:
                show_error_message(f'`a` takes exactly 1 arguement - {len(words) - 1} were given')

            try:
                add_time(float(words[1]))
            except ValueError:
                show_error_message(f'invalid time: {words[1]}')

        elif words[0] in aliases.keys():
            interpret(aliases[words[0]] + f' {" ".join(words[1:])}')

        else:  # command was not recognized
            show_error_message(f'{words[0]}: Invalid command')

    if not command:
        Image(canvas, 0, 0, char(canvas.display))
        command_inputs = []

        while True:
            try:
                cmd_ipt = CommandInput(canvas)
                command_inputs.append(cmd_ipt)
                cmd = ask_for_input(
                    stdscr, canvas, cmd_ipt, Cursor(canvas), True).strip()
            except ExitCommandLine:
                for c in command_inputs:
                    c.hide()
                return
            interpret(cmd)
    else:
        interpret(command)
