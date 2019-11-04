# cl-timer

*A Cubing Timer for the terminal*

## OS Support

This currently only works on macos, though once a level of functionality on par with popular web-based timers such as cs-timer or qq-timer (the latter likely more feasible) is reached, I will consider working first on ubuntu support, and later windows.

## Installation

As of right now, cl-timer is only "installable" through git

`git clone 'https://github.com/lol-cubes/cl-timer'`

Run timer.py to start program.

There will most likely be pip installation once the first stable version is released

## Usage

# IMPORTANT

**The way cl-timer detects holding the spacebar down for a long time as a single keypress requires a minimum key-repeat speed. On macos, go to System Preferences -> Keyboard. Move the sliders for "Key Repeat" and "Delay Until Repeat" to the side labeled "short" as far as possible.**

### Basic Features

Type the name of the session once prompted to, and type the name of the session.
If a session with that name already exists, that session's times will be loaded.

Press the spacebar to start the timer, as you accumulate more times, the stats on the side will update accordingly.

The times are saved automatically every time a new solve is completed.

Press ^c at any time to exit the program

### Commands

Press ":", type the command, and press "enter". The effects of the command should show up immediately. Press "escape" to exit the command input.

#### `set`

*changes settings*

##### Arg 1: name of setting to change

current list of changeable settings:

- `puzzle` --- the order of rubik's cube you want the scramble notation for. As of right now that is only 3x3 and 2x2

- `scramble-length` --- the length of the scramble.

##### Arg 2: new value of setting

corresponding possilbe values to each setting:

- `puzzle` --- the number of layers in the puzzle, e. g. `2` meaning 2x2

- `scramble-length` --- the number of moves in the scramble

#### `info`

*shows information about solves*

Specifically shows: index, time, ao5, ao12, and scramble

##### Arg 1 *(optional)*: solve

e. g. `2` means second solve in session

When called without an argument, opens file (read-only) containing all times, averages, and scrambles

#### `session`

*changes to different session*

##### Arg 1: session name

Switches to session name. Same functionality as session input on startup.

#### `del`

*deletes time*

##### Arg 1: solve

e. g. `2` means second solve in session

Removes all traces of solve at index `solve`

#### `dnf`

*marks most recent solve as DNF*

Treats solve as DNFs are treated by other timers and by WCA regulations.
Solve is now represented as f"DNF({time})"

#### `plus-two`

*marks most recent solve as "plus two"*

Treats solve as plus twos are treated by other timers and by WCA regulations.
Solve is now represented as f"{time + 2}+"

## System Requirements and Dependencies

Once that aforementioned work is done on adapting this to other OSes, I will have exact instructions on how to make this work on each system.

As of right now, any modern version of python3 should be good for this, but it is being developed on python3.8.0, so I may use some features that will throw syntax errors in any other versions.