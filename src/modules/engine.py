'''this is a connector to the stockfish engine, it is used to get the best moves from the engine and return them to the main program'''

import chess
import chess.engine
import subprocess
import os
from utilities.resource_path import resource_path
from modules.engine_lines import EngineLine

path = resource_path("assets/stockfish/stockfish.exe")
number_of_lines = 5
initial_depth = 10
moves_per_line = 5

def format_eval(score, is_white_to_move):
    """
    Format the evaluation score.

    Args:
        score (chess.engine.PovScore): The evaluation score in centipawns or mate score.
        is_white_to_move (bool): True if it's white's turn to move, False otherwise.

    Returns:
        str: Formatted evaluation score.
    """
    if score.is_mate():
        return f"M{score.mate()}"
    else:
        value = score.relative.cp / 100.0
        if not is_white_to_move:
            value = -value  # Reverse score if it's black's turn
        return f"{value:.2f}"

def trim_lines(lines: list, max_index: int = moves_per_line):
    """
    Trims the lines to contain at most 5 moves.

    Args:
        lines (list of EngineLine): The lines to be trimmed.
        max_index (int): The maximum number of moves per line.

    Returns:
        list of EngineLine: Trimmed lines.
    """
    for line in lines:
        while len(line) > max_index:
            line.remove_move(-1)  # Remove the last move until the length is 5 or less
    return lines

def get_top_lines(fen: str, max_depth, path=path, number_of_lines=number_of_lines):
    '''Get the top lines from the engine for a given depth.'''
    try:
        top_lines = []
        seen_lines = set()  # Set to track unique lines

        # Define creation flags for suppressing the console window on Windows
        creation_flags = 0
        if os.name == 'nt':  # Check if the system is Windows
            creation_flags = subprocess.CREATE_NO_WINDOW

        with chess.engine.SimpleEngine.popen_uci(path, creationflags=creation_flags) as engine:
            board = chess.Board(fen)

            try:
                result = engine.analyse(board, chess.engine.Limit(depth=max_depth), multipv=number_of_lines)

                lines_seen = 0
                for info in result:
                    line = []
                    board_copy = board.copy()
                    for move in info['pv']:
                        if not board_copy.is_legal(move):
                            print(f"Illegal move detected: {move} in {board_copy.fen()}")
                            break
                        line.append(board_copy.san(move))
                        board_copy.push(move)

                    else:
                        # Check if the line is unique using tuple representation (san moves in tuple format)
                        line_tuple = tuple(line)
                        if line_tuple not in seen_lines:
                            eval_score = format_eval(info['score'], board.turn)
                            top_lines.append(EngineLine(lines_seen + 1, line, eval_score))
                            seen_lines.add(line_tuple)  # Add tuple to set of seen lines
                            lines_seen += 1
                            if lines_seen == number_of_lines:
                                break

            finally:
                engine.quit()

    except Exception as e:
        pass
    finally:
        return trim_lines(top_lines)
