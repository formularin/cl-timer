import art
import logging


logger = logging.getLogger(__name__)


class Canvas:
    """
    Represents string that is displayed to the screen with each frame
    """

    def __init__(self, height, width):
        self.grid = [[" " for _ in range(width)] for _ in range(height)]

    def replace(self, x, y, char):
        """
        Replaces char in certain location of self.grid
        (0, 0) is bottom-left corner.
        Y increases in upward direction, X to the right.
        """
        row_index = (len(self.grid) - 1) - y
        self.grid[row_index][x] = char

    @property
    def display(self):
        rows = ["".join(row) for row in self.grid][::-1]
        return '\n'.join(rows)


class Char:
    """
    A single character that is part of an Image
    """

    def __init__(self, x, y, char):

        self.x = x
        self.y = y
        if len(char) == 1:
            self.char = char
        else:
            raise ValueError("Char object can only represent one char.")

    def change_char(self, char):
        """
        Changes self.char attribute to `char`
        """
        self.char = char

    def change_coords(self, x, y):
        """
        Changes self.x and self.y to given args
        """
        self.x = x
        self.y = y

    @classmethod
    def fromstring(cls, string):
        chars = []
        for y, line in enumerate(string.split('\n')):
            for x, char in enumerate(line):
                chars.append(Char(x, y, char))
        return chars


class Image:
    """Something displayed on the canvas"""

    def __init__(self, canvas, x, y, chars):
        
        self.canvas = canvas
        self.x = x
        self.y = y
        self.chars = chars

    def render(self):
        """Alter canvas display to update current state of self."""
        # canvas_x means location of char on the canvas

        for char in self.chars:

            canvas_x = self.x + char.x
            canvas_y = self.y + char.y

            self.canvas.replace(canvas_x, canvas_y, char.char)

    def change(self, x, y, char):
        """Changes the character of a Char in a certain position to `char`"""
        for char in self.chars:
            if char.x == x and char.y == y:
                char.change_char(char)

    def __str__(self):
        max_x = max([char.x for char in self.chars]) + 1
        max_y = max([char.y for char in self.chars]) + 1

        chars = [[[] for _ in range(max_y)] for _ in range(max_x)]

        for char in self.chars:
            chars[char.x][char.y] = char.char

        return '\n'.join([''.join(line) for line in chars])


class CommandInput(Image):
    """
    Represents a line where if you type, it will record what was typed
    """

    def __init__(self, canvas):
        
        prompt = ": "
        self.prompt_length = len(prompt)
        self.cursor_index = self.prompt_length
        self.submitted = False
        self.inputted_chars = []

        y = len(canvas.grid) - 1
        prompt_chars = [Char(i, 0, char) for i, char in enumerate(prompt)]
        input_chars = [Char(i, 0, " ") for i in range(self.prompt_length, len(canvas.grid[-1]))]
        chars = prompt_chars + input_chars

        Image.__init__(self, canvas, 0, y, chars)

    @property
    def value(self):
        return ''.join(self.inputted_chars)

    def _del_char(self):
        """Removes last char from input field"""
        if self.cursor_index > self.prompt_length:
            self.chars[self.cursor_index] = Char(self.cursor_index, 0, " ")
            self.cursor_index -= 1
            self.inputted_chars = self.inputted_chars[:-1]

    def type_char(self, char):
        """Adds char to value of input field"""
        if not (char in [-1, 127, 10]):
            try:
                new_char = chr(char)
                self.chars[self.cursor_index] = Char(self.cursor_index, 0, new_char)
                self.cursor_index += 1
                self.inputted_chars.append(chr(char))
            except Exception:
                pass
        elif char == 127:
            self._del_char()
        elif char == 10:
            self.submitted = True
            len_chars = len(self.chars)
            self.chars = [Char(i, 0, " ") for i in range(len_chars)]
            self.render()


class NumberDisplay(Image):
    """
    The Image that shows the time
    """
    def __init__(self, canvas, x, y):
        self.digit_char_arrays = []
        self.time = 0
        self.digits = []
        self.chars = Char.fromstring(art.STARTING_TIME)
        Image.__init__(self, canvas, x, y, self.chars)

    def increment(self):
        """
        Increases displayed value by 0.01
        """

        self.time += 0.01
        len_digits = len(self.digits)
        self.digits = [int(d) if d != '.' else d for d in 
                       str(round(self.time, 2))]

        # logging.info(''.join([str(i) for i in self.digits[0:self.decimal_point_index]] + ['.'] + [str(i) for i in self.digits[self.decimal_point_index:]]))
        if len(self.digits[self.digits.index('.') + 1:]) != 2:
            self.digits.append(0)
        # logging.info(f'{repr(self.digits)}')

        digit_strings = []
        for digit in self.digits:
            if digit != '.':
                digit_strings.append(art.DIGITS[digit])
            else:
                digit_strings.append(art.DECIMAL_POINT)

        # logger.info(repr(digit_strings))

        full_string_lines = [[] for i in range(4)]
        for i in range(4):
            for digit_string in digit_strings:
                full_string_lines[i].append(digit_string.split('\n')[i])
        full_string = '\n'.join([' '.join(line) for line in full_string_lines])

        self.chars = Char.fromstring(full_string)
        # logger.info('\n' + str(self))

    def reset(self):
        self.time = 0
        self.chars = Char.fromstring(art.STARTING_TIME)