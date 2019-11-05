import random


def groups(lst, division):
    if isinstance(division, int):
        return [lst[i:i + division] for i in range(0, len(lst), division)]
    elif isinstance(division, list):
        i = 0
        new_lst = []
        for k in division:
            new_lst.append(lst[i:i + k])
            i += k
        return new_lst


MOVES = [
    ['R', "R'", 'R2',  # 2x2
     'U', "U'", 'U2',  #
     'F', "F'", "F2"], #
    ['R', "R'", 'R2', 'L', "L'", 'L2',  # 3x3
     'U', "U'", 'U2', 'D', "D'", 'D2',  #
     'F', "F'", 'F2', 'B', "B'", 'B2'], #
    ['R', "R'", 'R2', 'Rw', "Rw'", 'Rw2', 'L', "L'", 'L2',  # 4x4
     'U', "U'", 'U2', 'Uw', "Uw'", 'Uw2', 'D', "D'", 'D2',  #
     'F', "F'", 'F2', 'Fw', "Fw'", 'Fw2', 'B', "B'", 'B2'], #
    ['R', "R'", 'R2', 'Rw', "Rw'", 'Rw2', 'L', "L'", 'L2', 'Lw', "Lw'", 'Lw2',  # 5x5
     'U', "U'", 'U2', 'Uw', "Uw'", 'Uw2', 'D', "D'", 'D2', 'Dw', "Dw'", 'Dw2',  #
     'F', "F'", 'F2', 'Fw', "Fw'", 'Fw2', 'B', "B'", 'B2', 'Bw', "Bw'", 'Bw2'], #
    ['R', "R'", 'R2', 'Rw', "Rw'", 'Rw2', '3Rw', "3Rw'", '3Rw2', 'L', "L'", 'L2', 'Lw', "Lw'", 'Lw2',  # 6x6
     'U', "U'", 'U2', 'Uw', "Uw'", 'Uw2', '3Uw', "3Uw'", '3Uw2', 'D', "D'", 'D2', 'Dw', "Dw'", 'Dw2',  #
     'F', "F'", 'F2', 'Fw', "Fw'", 'Fw2', '3Fw', "3Fw'", '3Fw2', 'B', "B'", 'B2', 'Bw', "Bw'", 'Bw2'], #
    ['R', "R'", 'R2', 'Rw', "Rw'", 'Rw2', '3Rw', "3Rw'", '3Rw2', 'L', "L'", 'L2', 'Lw', "Lw'", 'Lw2', '3Lw', "3Lw'", '3Lw2',  # 7x7
     'U', "U'", 'U2', 'Uw', "Uw'", 'Uw2', '3Uw', "3Uw'", '3Uw2', 'D', "D'", 'D2', 'Dw', "Dw'", 'Dw2', '3Dw', "3Dw'", '3Dw2',  #
     'F', "F'", 'F2', 'Fw', "Fw'", 'Fw2', '3Fw', "3Fw'", '3Fw2', 'B', "B'", 'B2', 'Bw', "Bw'", 'Bw2', '3Bw', "3Bw'", '3Bw2']  #
    ]

AXES = [groups(lst, (i + 1) * 3) for i, lst in enumerate(MOVES)]

SIDE_LENTHS = [
    [3 for _ in range(3)],  # 2x2
    [3 for _ in range(6)],  # 3x3
    [6 if i % 2 == 0 else 3 for i in range(6)],  # 4x4
    [6 for _ in range(6)],  # 5x5
    [9 if i % 2 == 0 else 6 for i in range(6)],  # 6x6
    [9 for _ in range(6)]
]

SIDES = [groups(lst, side_lengths) for side_lengths, lst in zip(SIDE_LENTHS, MOVES)]


def choose_move(scramble_moves, size):
    """
    Looks for a move that won't be redundant.

    Takes `scramble_moves` as the list of already listed moves.

    Chooses a random move.

    Since the last move of a different axis,
    if there has been a turn of the same side, 
    this move is redundant.

    If that is the case, it calls itself again
    until it finds a move that isn't redundant.
    """

    move = random.choice(MOVES[size - 2])
    axis = [axis for axis in AXES[size - 2] if move in axis][0]
    side = [side for side in SIDES[size - 2] if move in side][0]

    try:
        last_move_of_different_axis = [i for i, move in enumerate(scramble_moves)
                                       if move not in axis][-1]
    except IndexError:
        # there has only been moves of the same axis so far.
        last_move_of_different_axis = -1

    moves_since_then = scramble_moves[last_move_of_different_axis + 1:]
    if [move for move in moves_since_then if move in side] != []:
        return choose_move(scramble_moves, size)
    return move


def generate_scramble(size, length):
    """
    Returns a list of random moves 
    to scramble a rubik's cube in WCA notation
    """
    scramble_moves = []
    for i in range(length):
        scramble_moves.append(choose_move(scramble_moves, size))
    return ' '.join(scramble_moves)