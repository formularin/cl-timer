# cl-timer

*A Cubing Timer for the terminal*

## OS Support

This currently only works on macos, though once a level of functionality on par with popular web-based timers such as cs-timer or qq-timer (the latter likely more feasible) is reached, I will consider working first on ubuntu support, and later windows.

## Installation

### Install with Git

`git clone 'https://github.com/lol-cubes/cl-timer'`

Run timer.py to start program.

### Install with Pip

`pip install cl-timer`

The command cl-timer will be added to a bin directory in you PATH.

Make sure you are not in a virtual environment.

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

#### `s`

*changes settings*

##### Arg 1: setting to change

current list of changeable settings:

- `p` --- the order of rubik's cube you want the scramble notation for. As of right now that is only 3x3 and 2x2

- `sl` --- the length of the scramble.

##### Arg 2: new value of setting

corresponding possilbe values to each setting:

- `p` --- the number of layers in the puzzle, e. g. `2` meaning 2x2

- `sl` --- the number of moves in the scramble

#### `i`

*shows information about solves*

Specifically shows: index, time, ao5, ao12, and scramble

##### Arg 1 *(optional)*: solve

e. g. `2` means second solve in session

When called without an argument, opens file (read-only) containing all times, averages, and scrambles

#### `c`

*changes to different session*

##### Arg 1: session name

Switches to session name. Same functionality as session input on startup.

#### `rm`

*deletes time*

**After a solve is delete with this command, it is gone forever**

##### Arg 1: solve

e. g. `2` means second solve in session

Removes all traces of solve at index `solve`

#### `d`

*marks most recent solve as DNF*

Treats solve as DNFs are treated by other timers and by WCA regulations.
Solve is now represented as f"DNF({time})"

#### `p`

*marks most recent solve as "plus two"*

Treats solve as plus twos are treated by other timers and by WCA regulations.
Solve is now represented as f"{time + 2}+"

#### `q`

*exits the program*

Just an alternative to quiting using ^c. I found myself typing this familiar vim command in cl-timer numerous times, and it does no harm to have it here.

## System Requirements and Dependencies

Once that aforementioned work is done on adapting this to other OSes, I will have exact instructions on how to make this work on each system.

As of right now, any modern version of python3 should be good for this, but it is being developed on python3.8.0, so I may use some features that will throw syntax errors in any other versions.