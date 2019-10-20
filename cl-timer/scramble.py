import random


MOVES = ['R', "R'", 'R2', 'L', "L'", 'L2', 'U', "U'", 'U2',
         'D', "D'", 'D2', 'F', "F'", 'F2', 'B', "B'", 'B2']

AXES = [MOVES[i:i + 6] for i in range(0, len(MOVES), 6)]

SIDES = [MOVES[i:i + 3] for i in range(0, len(MOVES), 3)]


def choose_move(scramble_moves):
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

    move = random.choice(MOVES)
    axis = [axis for axis in AXES if move in axis][0]
    side = [side for side in SIDES if move in side][0]

    try:
        last_move_of_different_axis = [i for i, move in enumerate(scramble_moves)
                                       if move not in axis][-1]
    except IndexError:
        # there has only been moves of the same axis so far.
        last_move_of_different_axis = -1

    moves_since_then = scramble_moves[last_move_of_different_axis + 1:]
    if [move for move in moves_since_then if move in side] != []:
        return choose_move(scramble_moves)
    return move


def generate_scramble():
    """
    Returns a list of 20 random moves 
    to scramble a rubik's cube in WCA notation
    """
    scramble_moves = []
    for i in range(20):
        scramble_moves.append(choose_move(scramble_moves))
    return ' '.join(scramble_moves)