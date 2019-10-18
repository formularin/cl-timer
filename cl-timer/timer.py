import curses
import time

import art
import graphics


def main(stdscr):
    """
    Mainloop for the program
    """

    curses.curs_set(0)
    stdscr.nodelay(True)

    while True:

        key = stdscr.getch()

        if key != -1:
            break

        stdscr.clear()
        stdscr.addstr(art.TITLE_ART)
        stdscr.refresh()

        time.sleep(0.01)


if __name__ == "__main__":
    curses.wrapper(main)