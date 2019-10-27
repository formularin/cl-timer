import random


MOVES = [
    ['R', "R'", 'R2', 'U', "U'", 'U2', 'F', "F'", "F2"],
    ['R', "R'", 'R2', 'L', "L'", 'L2', 'U', "U'", 'U2',
     'D', "D'", 'D2', 'F', "F'", 'F2', 'B', "B'", 'B2']
    ]

AXES = [
    [size[i:i + (3 * (s + 1))] for i in range(0, len(size), (3 * (s + 1)))]
    for s, size in enumerate(MOVES)
    ]

SIDES = [[size[i:i + 3] for i in range(0, len(size), 3)] for size in MOVES]

SCRAMBLE_LENGTHS = {
    2:11,
    3:20,
}


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


def generate_scramble(size):
    """
    Returns a list of random moves 
    to scramble a rubik's cube in WCA notation
    """
    scramble_moves = []
    for i in range(SCRAMBLE_LENGTHS[size]):
        scramble_moves.append(choose_move(scramble_moves, size))
    return ' '.join(scramble_moves)

