"""
Various classes that involve the "backend" of calculating the string to
be displayed on each frame.
"""


from cl_timer.art import STARTING_TIME, DIGITS, DECIMAL_POINT


class Canvas:
    """
    The current state of the screen.

    Constantly being edited by existence and change of Image objects.
    """

    def __init__(self, height, width):
        # List of rows. Top row when displayed is at index 0
        self.grid = [[' ' for _ in range(width)] for _ in range(height)]

    def replace(self, x, y, char):
        """
        Replaces char in certain location of self.grid
        """
        row_index = (len(self.grid) - 1) - y
        try:
            self.grid[row_index][x] = char
        except IndexError:
            pass

    @property
    def display(self):
        """
        String that is displayed onto the screen
        """
        rows = [''.join(row) for row in self.grid][::-1]
        return '\n'.join(rows)


class Char:
    """
    A single character that is part of an Image object
    """

    def __init__(self, x, y, char):

        self.x = x
        self.y = y
        self.char = char

    def change_coords(self, x, y):
        """
        Changes self.x and self.y to `x` and `y`
        """
        self.x = x
        self.y = y

    @classmethod
    def fromstring(cls, string):
        """
        Takes string and returns list of Char objects that can be used
        to create and Image object that appears as that string.
        """
        return [Char(x, y, char) for x, char in enumerate(line) for y, line
                 in enumerate(string.split('\n'))]


class Image:
    """
    Something that alters the appearance of a Canvas object.
    """

    def __init__(self, canvas, x, y, chars):

        self.canvas = canvas
        self.x = x
        self.y = y
        self.chars = chars

    @property
    def displayed_chars(self):
        """
        The list of Char obejcts that this Image consists of
        """
        return self.chars

    @displayed_chars.setter
    def displayed_chars(self, chars):
        """
        Setter method for displayed_chars

        Hides image on canvas
        """
        for char in self.chars:
            self.canvas.replace(char.x + self.x, char.y + self.y, " ")
        self.chars = chars

    def render(self):
        """
        Alter canvas display to update current state of self.
        """
        for char in self.chars:
            self.canvas.replace(char.x + self.x, char.y + self.y, char.char)

    def __str__(self):
        """
        Shows what image is supposed to render on the canvas like.

        Mainly for debugging purposes.
        """

        # create square grid exactly large enough to contain all chars
        max_x = max([char.x for char in self.chars]) + 1
        max_y = max([char.y for char in self.chars]) + 1

        chars = [[[] for _ in range(max_x)] for _ in range(max_y)]

        # replace empty grid spaces with real chars
        for char in self.chars:
            chars[char.y][char.x] = char.char

        # remove blank spaces from grid
        for i, l in enumerate(chars[:]):
            if [] in l:
                for k in range(l.count([])):
                    chars[i].remove([])

        string = '\n'.join([''.join(line) for line in chars])
        return string


class InputLine(Image):
    """
    Represents a kind of concept similar to the HTML input element.

    Will echo entered characters as typed, and store the final inputted
    string. Takes up the entire width of the canvas.
    """

    def __init__(self, canvas, prompt):

        self.prompt = prompt
        self.prompt_length = len(self.prompt)  # b/c frequent usage
        self.cursor_index = self.prompt_length  # directly right of prompt
        self.submitted = False
        self.inputted_chars = []

        Image.__init__(
            self,
            canvas,
            0,
            len(canvas.grid) - 1,
            Char.fromstring(
                self.prompt
                + ''.join([' ' for _ in self.prompt + self.canvas.grid[-1]]))
        )

    @property
    def value(self):
        """
        The text that has been inputted up to this point
        """
        return ''.join(self.inputted_chars)

    def update_chars(self):
        """
        Updates `self.chars` according to `prompt` and `inputted_chars`
        Adds spaces to fill width of `canvas.grid`
        """
        string = (
            self.prompt
            + ''.join(self.inputted_chars)
            + ''.join(
                [
                    ' ' for _ in range(
                        len(self.canvas.grid[-1])
                        - (self.prompt_length + len(self.inputted_chars))
                    )
                ]
            )
        )
        self.chars = Char.fromstring(string)

    def _del_char(self):
        """
        Removes last char from input field
        """
        if self.cursor_index > self.prompt_length:
            # change value
            self.inputted_chars.pop(
                self.cursor_index
                - self.prompt_length
                - 1)

            update_chars()

            # move cursor back one place
            # (will be put into effect when `move` method called)
            self.cursor_index -= 1

    def type_char(self, char):
        """
        Adds char to value of input field
        """

        # -1 is the code for no key pressed
        if not (char in [-1, 127, 10, 260, 261]):
            # convert int ascii code to get string for inputted char
            new_char = chr(char)

            # replace current char in cursor location with new char
            self.inputted_chars.insert(
                self.cursor_index
                - self.prompt_length, new_char)
            self.cursor_index += 1

            update_chars()

        elif char == 127:  # backspace
            self._del_char()

        elif char == 10:  # enter
            self.submitted = True

            # hides by covering with spaces
            self.chars = [Char(i, 0, ' ') for i in range(len(self.chars))]
            self.render()

        elif char == 260:  # left arrow key
            # move cursor back if it is not going to go into the prompt
            if (self.cursor_index - self.prompt_length - 1) >= 0:
                self.cursor_index -= 1

        elif char == 261:  # right arrow key
            len_inputted_chars = self.prompt_length + len(self.inputted_chars)
            last_char_index = self.cursor_index + 1
            # move cursor forward if chars have been inputted that far
            if len_inputted_chars >= last_char_index:
                self.cursor_index += 1


class CommandInput(InputLine):
    """
    Represents an InputLine that is meant for typing commands

    Like vim, it is triggered by pressing ':'.
    Commands typed here will return info about the session.
    """

    def __init__(self, canvas):
        InputLine.__init__(self, canvas, ': ')

    def hide(self):
        """
        Replaces all chars with spaces
        so that Image is no longer visible
        """
        for char in self.chars:
            self.canvas.replace(self.x + char.x, self.y + char.y, " ")


class NumberDisplay(Image):
    """
    The Image that shows the time
    """
    def __init__(self, canvas, x, y):
        self.digit_char_arrays = []
        self.time = 0
        self.digits = []
        self.chars = Char.fromstring(STARTING_TIME)
        Image.__init__(self, canvas, x, y, self.chars)

    def update(self):
        """
        Updates `self.chars` according to time value
        """

        # get complete (2 decimal place) list of digits
        # (including decimal point)
        len_digits = len(self.digits)
        self.digits = [int(d) if d != '.' else d for d in
                       str(round(self.time, 2))]
        if len(self.digits[self.digits.index('.') + 1:]) != 2:
            self.digits.append(0)

        # list of digits from above converted to strings
        # strings are the ones that will be displayed on screen
        digit_strings = [DIGITS[digit] if digit != '.' else DECIMAL_POINT
                         for digit in self.digits]

        # lines that the final string will contain
        full_string_lines = [[] for i in range(4)]
        for i in range(4):
            for digit_string in digit_strings:
                # if on 2nd iteration of outer loop and 3rd of inner
                # loop, will append 2nd line of 3rd digit string to
                # 2nd sublist of `full_string_lines`
                full_string_lines[i].append(digit_string.split('\n')[i])

        # join lines of each digit with spaces, and total lines with `\n`s
        full_string = '\n'.join([' '.join(line) for line in full_string_lines])
        self.chars = Char.fromstring(full_string)

    def reset(self):
        """
        Sets time to zero.
        """
        self.time = 0
        self.chars = Char.fromstring(STARTING_TIME)


class CoverUpImage(Image):
    """
    An image that covers up it's previous characters when it's chars are changed
    """

    def __init__(self, canvas, x, y, chars):

        self.canvas = canvas
        self.x = x
        self.y = y
        self._chars = chars

    @property
    def chars(self):
        return self._chars

    @chars.setter
    def chars(self, chars):
        """
        Replaces all former chars with spaces, and renders self
        """
        for c in self._chars:
            self.canvas.replace(self.x + c.x, self.y, " ")
        self._chars = chars
        self.render()


def break_top_line(string, line_length):
    """
    Takes a string containing a scramble and returns a string that is the same
    as the first string but with a newline in there that doesn't break any
    moves but also makes the length of the new first line less than the `line_length`
    """
    moves = string.split(' ')
    substrings = [' ' for _ in range(len(moves) - 1)]  # moves or spaces
    for i, move in enumerate(moves):
        substrings.insert(i * 2, move)
    lengths = [len(substring) for substring in substrings]

    newline_index = 0  # how many times the string has been broken so far
    # `previous_sum` is here because each iteration, the below loop
    # adds a new move to the line, and checks the length. If the length
    # is greater than `line_length`, then it goes back to the previous
    # move because that is as far as it can go without going over.
    previous_sum = 0
    for i in range(len(lengths)):
        slice_sum = sum(lengths[:i])
        if line_length == slice_sum:
            newline_index = slice_sum
            break
        if (line_length < slice_sum) and (line_length > previous_sum):
            newline_index = previous_sum
            break
        previous_sum = slice_sum

    chars = list(string)
    chars.insert(newline_index, '\n')
    return ''.join(chars)


class Scramble(CoverUpImage):
    """
    Optimized for showing a scramble
    """

    def __init__(self, canvas, x, y, chars):
        CoverUpImage.__init__(self, canvas, x, y, chars)

    def clear(self):
        """
        Replaces all chars on canvas with spaces
        """
        ys = []
        for x, y in ([(c.x, c.y) for c in self._chars]):
            self.canvas.replace(self.x + x, self.y + y, " ")
            if y not in ys:
                ys.append(y)

    def render(self):
        """
        This exists because scrambles can be longer than the length of the screen
        """
        if len(self._chars) > len(self.canvas.grid[0]):

            lines = []
            bottom_line = str(self)
            while True:
                # add line of appropriate length to lines
                scramble_with_newline = break_top_line(
                    bottom_line, len(self.canvas.grid[0]) - 1)
                lines.append(scramble_with_newline.split('\n')[0])

                # if the remaining string after removing the top line
                # is the same as that of lasts time, you are done
                # because no more lines can be taken away from the top
                if (new_bottom_line := scramble_with_newline.split('\n')[1]
                        == bottom_line):
                    break
                bottom_line = new_bottom_line
            string = '\n'.join([l.strip() for l in lines])
            self._chars = Char.fromstring(string)
            Image.render(self)
        else:
            Image.render(self)


class Cursor(Image):
    """
    Represents the block character used to represent cursor
    """

    def __init__(self, canvas):

        # u'\u2588' is the unicode full-block character

        Image.__init__(self, canvas, 0, 0, [Char(0, 0, u'\u2588')])

        self.previous_x = self.x
        self.previous_y = self.y

    def render(self):
        """
        Override inherited render method because
        this Image can move and has only one char
        """

        # cover previous location
        self.canvas.replace(
            self.previous_y,
            (len(self.canvas.grid) - 1) - self.previous_x,
            ' ')

        # show self in current location
        self.canvas.replace(
            self.y,
            (len(self.canvas.grid) - 1) - self.x,
            self.chars[0].char)

    def move(self, x, y):
        """
        Moves cursor to (x, y) on the canvas
        """

        self.previous_x = self.x
        self.previous_y = self.y

        self.x = x
        self.y = y

    def hide(self):
        """
        Temporarily hides self.
        """

        self.chars[0] = Char(0, 0, ' ')
        self.render()