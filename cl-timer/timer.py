import curses
import signal
import time

import art
import graphics


class ExitException(Exception):
    """Tells the program when to exit"""


def signal_handler(sig, frame):
    raise ExitException()


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


    t = 0
    timer_running = False
    while True:

        key = stdscr.getch()

        if key == 32:  # spacebar
            if timer_running:
                timer_running = False
            else:
                timer_running = True

        stdscr.clear()
        stdscr.addstr(str(round(t, 2)))
        stdscr.refresh()

        if timer_running:
            t += 0.01
        time.sleep(0.01)


if __name__ == "__main__":

    signal.signal(signal.SIGINT, signal_handler)

    try:
        curses.wrapper(main)
    except ExitException:
        pass