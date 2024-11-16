'''
This file is responsible for saving the information of the state of a a chess game and enforce its rules by making a list of legal moves
It contains the board class which stores the game state and manipulation regarding move making
'''

import sys
from modules.move import Move
import logging
try:
    logging.basicConfig(level=logging.INFO, filename='logs/chess_project_log.txt')  # Set logging level to INFO
except FileNotFoundError:
    pass

# all items in this file will use coordinates as array indexes
class Board:
    """
    Represents a chess board.

    Attributes:
        board_array (list[list[str]]): A 2D list representing the current state of the chess board.
        white_to_move (bool): True if it's white's turn to move, False if it's black's turn.
        castling_rights (Castling_Rights): An object representing the castling rights for both players.
        en_passant_square (tuple): The target square for en passant capture, represented as a tuple (row, column).
        halfmove_clock (int): The number of halfmoves since the last capture or pawn advance.
        fullmove_number (int): The number of the full move. It starts at 1 and is incremented after black's move.
        moveFunctions (dict): A dictionary mapping piece type to legal move generating function.
        move_log (list): A list of moves made in the game.
        fen_log (list): A list of FEN strings representing the board state at different positions.
        white_king_pos (tuple): The position of the white king on the board.
        black_king_pos (tuple): The position of the black king on the board.
        is_checkmate (bool): True if the game is in checkmate, False otherwise.
        is_draw (bool): True if the game is a draw, False otherwise.
        legal_moves (list): A list of legal moves for the current position.

    Methods:
        __repr__() -> str:
            Returns a string representation of the board.

        __eq__(other) -> bool:
            Compare two Board objects for equality.

        __init__(fen: str='rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1') -> None:
            Initializes a Board object.

        log_board_state(*args: str) -> None:
            Logs the board state and selected attributes and their values.

        fen_to_board(fen: str) -> tuple[list[str], bool, Castling_Rights, tuple, int, int]:
            Converts a FEN (Forsyth-Edwards Notation) string to a chess board representation.

        board_to_fen() -> str:
            Converts the current board state to a FEN (Forsyth-Edwards Notation) string.
    """

    def __repr__(self) -> str:
        """
        Returns a string representation of the board.

        The string representation consists of the current state of the chess board,
        with each piece represented by a single character. The board is represented
        as a grid of characters, with each row separated by a newline character.

        Returns:
            str: A string representation of the board.
        """
        board_str = '\n'.join(' '.join(piece for piece in row) for row in self.board_array)
        return board_str

    def __eq__(self, other) -> bool:
        """
        Compare two Board objects for equality.

        Args:
            other (Board): The other Board object to compare with.

        Returns:
            bool: True if the two Board objects are equal, False otherwise.
        """
        return self.board_to_fen() == other.board_to_fen()

    def __init__(self, fen: str='rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1') -> None:
        '''
        will store the game state and all of the information in the board regarding a chess position

        Args:
            fen (str, optional): Forsyth-Edwards Notation for the position. Defaults to 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'.
        '''
        # extracting details of the position from the fen string
        result = self.fen_to_board(fen)
        self.board_array = result[0]
        self.white_to_move = result[1]
        self.castling_rights = result[2]
        self.en_passant_square = result[3]
        self.halfmove_clock = result[4]
        self.fullmove_number = result[5]

        # a dictionary mapping piece type to legal move generating function
        self.moveFunctions = {'p': self.get_pawn_moves, 'R': self.get_rook_moves, 'N': self.get_knight_moves,
                              'B': self.get_bishop_moves, 'Q': self.get_queen_moves, 'K': self.get_king_moves}

        self.move_log = []   # for undo and exporting/importing games
        self.fen_log = [self.board_to_fen()[:self.board_to_fen().rfind(' ', 0, self.board_to_fen().rfind(' '))]]   # a list of fens to detect draw by repetition
        self.white_king_pos, self.black_king_pos = self.get_king_locations()
        self.is_checkmate = False
        self.is_draw = False
        self.legal_moves = self.get_legal_moves()   # the legal moves for the current position

    class Castling_Rights:
        """
        Represents the castling rights for a chess game.

        Attributes:
            castling_rights_string (str): A string representing the current castling rights.
            castling_rights_log (list): A list of strings representing the castling rights history.

        Methods:
            has_rights(side: str) -> bool:
                Check if the given side has castling rights.

            remove_rights(*sides: str) -> None:
                Remove castling rights for the specified sides.

            update(move: Move) -> None:
                Update castling rights based on the move made.

            undo_castling_rights() -> None:
                Restore the castling rights for the last position.

            __str__() -> str:
                Return a string representation of the castling rights.

            __eq__(other) -> bool:
                Check if two `Castling_Rights` objects are equal.

            __repr__() -> str:
                Return a string representation of the castling rights.
        """

        def __init__(self, castling_rights_string: str) -> None:
            """
            Initialize the ChessEngine object.

            Parameters:
            - castling_rights_string (str): A string representing the castling rights.

            Returns:
            - None
            """
            self.castling_rights_string = castling_rights_string
            self.castling_rights_log = [castling_rights_string]

        def has_rights(self, side: str) -> bool:
            """Check if the given side has castling rights."""
            return side in self.castling_rights_string

        def remove_rights(self, *sides: str) -> None:
            """Remove castling rights for the specified sides."""
            for side in sides:
                self.castling_rights_string = self.castling_rights_string.replace(side, '')

        def update(self, move: Move) -> None:
            """Update castling rights based on the move made."""
            if move.piece_moved == 'wK':
                self.remove_rights('K', 'Q')
            elif move.piece_moved == 'bK':
                self.remove_rights('k', 'q')
            elif move.piece_moved == 'wR':
                if move.start_col == 7:
                    self.remove_rights('K')
                elif move.start_col == 0:
                    self.remove_rights('Q')
            elif move.piece_moved == 'bR':
                if move.start_col == 7:
                    self.remove_rights('k')
                elif move.start_col == 0:
                    self.remove_rights('q')

            self.castling_rights_log.append(self.castling_rights_string)

        def undo_castling_rights(self) -> None:
            '''Will restore the castling rights for the last position'''
            if len(self.castling_rights_log) != 0:
                self.castling_rights_log.pop()
                if len(self.castling_rights_log) != 0:
                    self.castling_rights_string = self.castling_rights_log[-1]

        def __str__(self) -> str:
            return self.castling_rights_string if self.castling_rights_string else "-"

        def __eq__(self, other) -> bool:
            return self.castling_rights_string == other.castling_rights_string

        def __repr__(self) -> str:
            return self.castling_rights_string

    def log_board_state(self, *args: str) -> None:
        """
        Logs the board state and selected attributes and their values.

        Args:
            *args: Variable number of attribute names to log. If no arguments are provided,
                all attributes of the object will be logged.

        Returns:
            None
        """
        try:
            # Create a string to log selected attributes and their values
            state_str = 'Board state:\n'
            if args:
                for attr_name in args:
                    if hasattr(self, attr_name):
                        attr_value = getattr(self, attr_name)
                        if attr_name == 'board_array':
                            state_str += f'{attr_name}:\n'
                            for row in attr_value:
                                state_str += ' '.join(row) + '\n'
                        else:
                            state_str += f'{attr_name}: {attr_value}\n'
                    else:
                        state_str += f'{attr_name}: Not found\n'
            else:
                for attr_name in vars(self):
                    attr_value = getattr(self, attr_name)
                    if attr_name == 'board_array':  # Handle board_array separately
                        state_str += f'{attr_name}:\n'
                        for row in attr_value:
                            state_str += ' '.join(row) + '\n'
                    else:
                        state_str += f'{attr_name}: {attr_value}\n'
            logging.info(state_str)
        except Exception as e:
            pass

    def fen_to_board(self, fen: str) -> tuple[list[str], bool, Castling_Rights, tuple, int, int]:
        """
        Converts a FEN (Forsyth-Edwards Notation) string to a chess board representation.

        Args:
            fen (str): The FEN string representing the chess position.

        Returns:
            tuple[list[str], bool, Castling_Rights, tuple, int, int]: A tuple containing the following:
                - board (list[str]): The chess board represented as a list of lists, where each element represents a square on the board.
                - active_color (bool): True if it's white's turn to move, False if it's black's turn.
                - castling_rights (Castling_Rights): An enum representing the castling rights for both players.
                - en_passant_target (tuple): The target square for en passant capture, represented as a tuple (row, column).
                - halfmove_clock (int): The number of halfmoves since the last capture or pawn advance.
                - fullmove_number (int): The number of the full move. It starts at 1 and is incremented after black's move.
        """
        
        # Split the FEN string into sections
        sections = fen.split()

        # Extract piece placement section and split it into rows
        piece_placement = sections[0]
        rows = piece_placement.split('/')

        # Map FEN characters to piece symbols
        fen_symbols = {
            'r': 'bR', 'n': 'bN', 'b': 'bB', 'q': 'bQ', 'k': 'bK', 'p': 'bp',
            'R': 'wR', 'N': 'wN', 'B': 'wB', 'Q': 'wQ', 'K': 'wK', 'P': 'wp'
        }

        # Create the board by converting FEN characters to piece symbols
        board = []
        for row in rows:
            board_row = []
            for char in row:
                if char.isdigit():  # Handle empty squares
                    board_row.extend(['--'] * int(char))
                else:
                    board_row.append(fen_symbols.get(char, '--'))
            board.append(board_row)

        # Extract other details from the FEN string
        active_color = sections[1] == 'w'
        castling_rights = self.Castling_Rights(sections[2])
        en_passant_target = None if sections[3] == '-' else ((8 - int(sections[3][1])), ord(sections[3][0]) - ord('a'))
        halfmove_clock = int(sections[4])
        fullmove_number = int(sections[5])

        return board, active_color, castling_rights, en_passant_target, halfmove_clock, fullmove_number

    def board_to_fen(self) -> str:
        """
        Converts the current board state to FEN (Forsyth-Edwards Notation) notation.

        Returns:
            str: The FEN notation representing the current board state.
        """
        # Dictionary to map piece symbols to FEN characters
        piece_to_fen = {
            'bR': 'r', 'bN': 'n', 'bB': 'b', 'bQ': 'q', 'bK': 'k', 'bp': 'p',
            'wR': 'R', 'wN': 'N', 'wB': 'B', 'wQ': 'Q', 'wK': 'K', 'wp': 'P',
            '--': ''
        }

        # Convert the board state to FEN notation
        fen_pieces = []
        for row in self.board_array:
            fen_row = ''
            empty_count = 0
            for square in row:
                if square == '--':
                    empty_count += 1
                else:
                    if empty_count > 0:
                        fen_row += str(empty_count)
                        empty_count = 0
                    fen_row += piece_to_fen[square]
            if empty_count > 0:
                fen_row += str(empty_count)
            fen_pieces.append(fen_row)

        # Join rows with slashes to form the piece placement section
        piece_placement = '/'.join(fen_pieces)
        # Determine the active color
        active_color = 'w' if self.white_to_move else 'b'
        # Convert castling rights to a string
        castling_rights = str(self.castling_rights)
        # Determine the en passant target square
        if self.en_passant_square is not None:
            en_passant_target = Move.file_map[self.en_passant_square[1]] + Move.rank_map[self.en_passant_square[0]]
        else:
            en_passant_target = '-'
            
        # Combine all parts into FEN notation
        fen = ' '.join([piece_placement, active_color, castling_rights, en_passant_target, str(self.halfmove_clock // 1), str(self.fullmove_number)])

        return fen

    ##########     make/undo moves     ##########

    def _make_psuedo_legal_move(self, move: Move) -> None:
        '''
        This function is is used to update the state of the board. It only makes any move legal or not
        and has the primary purpose of move validation

        Warning: Do not use this to make move as it will result in errors

        Args:
            move (move object): The move object will update the board
            is_legal (Bool): An optional parameter to ask if we are making a legal move or psuedo legal
        '''
        try:
            self.move_log.append(move)
            self.white_to_move = not self.white_to_move

            # updating the move counters
            self.fullmove_number += 1 if self.white_to_move else 0

            # remove en passanted pawn
            if move.piece_moved[1] == 'p' and move.start_col != move.end_col and move.piece_captured == '--':
                self.board_array[move.end_row + (1 if move.piece_moved[0] == 'w' else -1)][move.end_col] = '--'

            # updating the board
            self.board_array[move.start_row][move.start_col] = '--'
            self.board_array[move.end_row][move.end_col] = move.piece_moved
            self.white_king_pos, self.black_king_pos = self.get_king_locations()   # updating the king positions

            # if promotion happens change the piece type
            if move.promoted_piece is not None:
                self.board_array[move.end_row][move.end_col] = move.piece_moved[0] + move.promoted_piece
            self.castling_rights.update(move)

            if move.is_castling:   #  moving rook if we castle
                if move.end_col > move.start_col:   # kingside castling
                    self.board_array[move.end_row][move.end_col-1] = self.board_array[move.end_row][move.end_col+1]   # moving the rook
                    self.board_array[move.end_row][move.end_col+1] = '--'
                elif move.end_col < move.start_col:   # queenside castling
                    self.board_array[move.end_row][move.end_col+1] = self.board_array[move.end_row][move.end_col-2]   # moving the rook
                    self.board_array[move.end_row][move.end_col-2] = '--'
        except Exception as e:
            print(f'The function make _psuedo_legal_move is not for use outside of the class ,{e}')

    def make_legal_move(self, move: Move) -> None:
        '''
        This function is is used to update the state of the board. It only makes a move if it is legal

        Args:
            move (move object): The move object will update the board
        '''
        def update_en_passant_square(move: Move):
            '''
            Will check  if any potential en passant square was made by the current move, otherwise if will make it none

            Args:
                move (Move): the current legal move that is played
            '''
            if (move.piece_moved[1] == 'p' and abs(move.start_row - move.end_row) == 2 and   # if an en passant square was made
                any(0 <= move.end_row < len(self.board_array) and 0 <= col < len(self.board_array[0]) and
                self.board_array[move.end_row][col][0] != move.piece_moved[0] and
                self.board_array[move.end_row][col][1] == 'p'
                for col in (move.end_col + 1, move.end_col - 1))):
                self.en_passant_square = (move.end_row + ( 1 if move.piece_moved[0] == 'w' else -1), move.start_col)
            else:
                self.en_passant_square = None

        def remove_extra_details(fen):
            """
            Removes extra details from the given FEN (Forsyth-Edwards Notation) string.

            Args:
                fen (str): The FEN string to remove extra details from.

            Returns:
                str: The modified FEN string with extra details removed, except for castling details.
            """
            parts = fen.split()
            if len(parts) >= 6:
                parts = parts[:4]  # Keep the first four elements (up to castling details)
            return ' '.join(parts)
        
        if move in self.legal_moves and not self.is_checkmate and self.is_draw == False:
            move = self.legal_moves[self.legal_moves.index(move)]
            self._make_psuedo_legal_move(move)
            self.fen_log.append(remove_extra_details(self.board_to_fen()))
            # this function is here instead of the _make_psuedo_legal_moves function because we only change the en passant move when
            # we actually make a move not when validating moves as it makes all possible moves so the en passant move
            # will always be the last checked 2 square pawn move
            update_en_passant_square(move)
            self.halfmove_clock = (self.halfmove_clock + 0.5) if move.piece_moved[1] != 'p' and move.piece_captured == '--' and (move.piece_moved == 'p' and move.start_col == move.end_col) else 0

            self.legal_moves = self.get_legal_moves()
            
            if not self.legal_moves:   # checking for the end of the game
                if self.in_check():
                    self.is_checkmate = True
                    self.move_log[-1].san = self.move_log[-1].san[: -1] + '#'   # easier way than changing the move class as it is a single case
                else:
                    self.is_draw = True
            elif self.halfmove_clock == 50 or any(self.fen_log.count(x) >= 3 for x in set(self.fen_log)):
                self.is_draw = True

    def undo_move(self, in_engine=False) -> None:
        '''
        Will return the game state on the previous move and will loose the details of the current one

        Args:
            is_engine (Bool): An optional parameter to check if the undo is part of GUI (False) or board module (True)
        '''
        if len(self.move_log) != 0:
            move = self.move_log.pop()
            self.fullmove_number -= 1 if self.white_to_move else 0
            self.halfmove_clock -= 0.5 if self.halfmove_clock != 0 and not in_engine else 0
            self.board_array[move.start_row][move.start_col] = move.piece_moved
            self.board_array[move.end_row][move.end_col] = move.piece_captured
            self.white_to_move = not self.white_to_move
            self.is_checkmate = False
            self.is_draw = False
            self.white_king_pos, self.black_king_pos = self.get_king_locations()
            self.castling_rights.undo_castling_rights()
            if move.piece_moved[1] == 'p' and abs(move.start_row - move.end_row) == 2:
                self.en_passant_square = (move.end_row, move.end_col)
                if move.start_col != move.end_col and move.piece_captured == '--':   # restore en passanted pawn
                    self.board_array[move.end_row + (1 if move.piece_moved[0] == 'w' else -1)][move.end_col] = ('w' if move.piece_moved[0] == 'b' else 'b') + 'p'
            else:
                self.en_passant_square = None
            if move.is_castling:
                if move.end_col > move.start_col:   # kingside castling
                    self.board_array[move.end_row][move.end_col+1] = self.board_array[move.end_row][move.end_col-1]   # moving the rook
                    self.board_array[move.end_row][move.end_col-1] = '--'
                elif move.end_col < move.start_col:   # queenside castling
                    self.board_array[move.end_row][move.end_col-2] = self.board_array[move.end_row][move.end_col+1]   # moving the rook
                    self.board_array[move.end_row][move.end_col+1] = '--'
            if not in_engine:
                self.fen_log.pop()
                self.legal_moves = self.get_legal_moves()

    ##########     move validation by considering checks     ##########

    def get_king_locations(self) -> tuple[tuple, tuple]:
        """
        A function to help with the board class

        Returns:
            tuple: 2 tuples representing index coordinates of white then black king
        """
        king_positions = {'wK': None, 'bK': None}
        for row_idx, row in enumerate(self.board_array):
            for col_idx, piece in enumerate(row):
                if piece in king_positions:
                    king_positions[piece] = (row_idx, col_idx)
                    if all(king_positions.values()):
                        return king_positions['wK'], king_positions['bK']
        print('ERROR: Both kings were not found on the board. Please use a valid FEN.')
        sys.exit()

    def in_check(self) -> bool:
        '''
        Checks if the current position in in check by using square_under_attack function

        Returns:
            Bool: True if a check is present False otherwise
        '''
        if self.white_to_move:
            return self.square_under_attack(self.white_king_pos[0], self.white_king_pos[1])
        else:
            return self.square_under_attack(self.black_king_pos[0], self.black_king_pos[1])

    def square_under_attack(self, row: int, col: int) -> bool:
        '''
        Checks if a square is under attack from an opponent piece by calculating all opponent moves

        Args:
            row (int): row of the board array
            col (int): column of the board array

        Returns:
            Bool: True if yes otherwise False
        '''
        self.white_to_move = not self.white_to_move   # switch turn to get opponent moves
        opponent_moves = self.get_psuedo_legal_moves()
        self.white_to_move = not self.white_to_move   # restore turn

        for move in opponent_moves:
            if move.end_row == row and move.end_col == col:
                return True
        return False

    def get_psuedo_legal_moves(self) -> list[Move]:
        '''
        Generates a list of psuedo-legal moves which are moves that are legal without considering checks

        Returns:
            list: a list containing move objects
        '''
        moves = []
        for row in range(8):
            for col in range(8):
                piece = self.board_array[row][col]
                if piece != '--':
                    color = piece[0]
                    piece_type = piece[1]
                    if (color == 'w' and self.white_to_move) or (color == 'b' and not self.white_to_move):
                        self.moveFunctions[piece_type](row ,col, moves)  # calls appropriate move function based on piece type
        return moves

    def get_legal_moves(self) -> list[Move]:
        '''
        Filters out the moves list into those moves only which dont leave the player's king hanging in check

        Returns:
            list[Move]: a list of move objects only which are legal moves
        '''
        def update_is_check(moves: list) -> list[Move]:
            '''
            This function fills in the is_check parameter of the move class for the san  function`

            Args:
                moves (list[Moves]): The list of legal moves

            Returns:
                list[Moves]: The move elements updated
            '''
            for move in moves:
                self._make_psuedo_legal_move(move)
                move.is_check = self.in_check()
                move.san = move.get_san()
                self.undo_move(True)
            return moves

        moves = self.get_psuedo_legal_moves()
        # this is done separately to prevent infinite recursion, see the function for more details
        active_king_pos = self.white_king_pos if self.white_to_move else self.black_king_pos
        moves = self.get_castling_moves(active_king_pos[0], active_king_pos[1], moves)

        for i in range(len(moves) - 1, -1, -1):
            self._make_psuedo_legal_move(moves[i])  # Make the move
            self.white_to_move = not self.white_to_move  # Switch turns
            if self.in_check():  # If in check after making the move
                moves.pop(i)  # Remove the move from the list
            self.white_to_move = not self.white_to_move
            self.undo_move(True)  # Undo the move

        moves = update_is_check(moves)
        return moves

    ##########     piece move validation     ##########

    def get_pawn_moves(self, row: int, col: int, moves: list) -> list[Move]:
        '''
        Creates a list of move objects that are associated with pawns which means:
            1. One square advance
            2. Two square advance from starting rank
            3. One square diagonal capture
            4. Promotion on last rank
            4. En-Passant captures

        Args:
            row (int): row index of board array
            col (int): column index of board array
            moves (list[Move]): a list of existing moves

        Returns:
            list[Move]: A list of move objects with pawn moves combined
        '''
        color = self.board_array[row][col][0]  # Get the color of the pawn
        direction = -1 if color == 'w' else 1  # Set direction based on color

        # Check one or two squares ahead from the starting position
        if 1 <= row + direction < 8:
            # moving one square forward
            if self.board_array[row + direction][col] == '--':
                if (color == 'w' and row-1 == 0) or (color == 'b' and row+1 == 7):   # if we have a promotion case
                    for piece in ['Q', 'N', 'R', 'B']:
                        moves.append(Move(self, (row, col, row + direction, col), promoted_piece=piece))
                else:   # regular non-promotion moves
                    moves.append(Move(self, (row, col, row + direction, col)))

                # moving 2 squares forward
                if ((row == 6 and color == 'w') or (row == 1 and color == 'b')) and self.board_array[row + 2 * direction][col] == '--':
                    moves.append(Move(self, (row, col, row + 2 * direction, col)))

        # Check diagonal captures
        for d_col in (-1, 1):
            if 0 <= col + d_col < 8 and 0 <= row + direction < 8:
                if self.board_array[row + direction][col + d_col][0] == ('b' if color == 'w' else 'w'):
                    if (color == 'w' and row-1 == 0) or (color == 'b' and row+1 == 7):   # if we have a promotion case with capturing
                        for piece in ['Q', 'N', 'R', 'B']:
                            moves.append(Move(self, (row, col, row + direction, col + d_col), promoted_piece=piece))
                    else:   # regular capture
                        moves.append(Move(self, (row, col, row + direction, col + d_col)))

                elif (row + direction, col + d_col) == self.en_passant_square:   # if we can en passant capture
                    moves.append(Move(self, (row, col, row + direction, col + d_col)))

        return moves

    def get_rook_moves(self, row: int, col: int, moves: list) -> list[Move]:
        '''
        Creates a list of move objects that are associated with rooks which means:
            1. Vertical movement
            2. Horizontal movement

        Args:
            row (int): row index of board array
            col (int): column index of board array
            moves (list[Move]): a list of existing moves

        Returns:
            list[Move]: A list of move objects with rook moves combined
        '''
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]  # Define all possible directions for rook moves

        for dr, dc in directions:
            r, c = row + dr, col + dc
            while 0 <= r < 8 and 0 <= c < 8:
                if self.board_array[r][c] == '--':  # If the square is empty, add the move
                    moves.append(Move(self, (row, col, r, c)))
                elif self.board_array[r][c][0] != self.board_array[row][col][0]:  # If the square has an opponent's piece, add the move and stop
                    moves.append(Move(self, (row, col, r, c)))
                    break
                else:  # If the square has own piece, stop
                    break
                r, c = r + dr, c + dc

        return moves

    def get_bishop_moves(self, row: int, col: int, moves: list) -> list[Move]:
        '''
        Creates a list of move objects that are associated with bishops which means:
            1. diagonal right movement
            2. diagonal left movement

        Args:
            row (int): row index of board array
            col (int): column index of board array
            moves (list[Move]): a list of existing moves

        Returns:
            list[Move]: A list of move objects with bishop moves combined
        '''
        directions = [(1, 1), (-1, 1), (1, -1), (-1, -1)]  # Define all possible diagonal directions for bishop moves

        for dr, dc in directions:
            r, c = row + dr, col + dc
            while 0 <= r < 8 and 0 <= c < 8:
                if self.board_array[r][c] == '--':  # If the square is empty, add the move
                    moves.append(Move(self, (row, col, r, c)))
                elif self.board_array[r][c][0] != self.board_array[row][col][0]:  # If the square has an opponent's piece, add the move and stop
                    moves.append(Move(self, (row, col, r, c)))
                    break
                else:  # If the square has own piece, stop
                    break
                r, c = r + dr, c + dc

        return moves

    def get_queen_moves(self, row: int, col: int, moves: list) -> list[Move]:
        '''
        Creates a list of move objects that are associated with queens which means:
            1. Vertical movement
            2. Horizontal movement
            3. diagonal movement

        Args:
            row (int): row index of board array
            col (int): column index of board array
            moves (list[Move]): a list of existing moves

        Returns:
            list[Move]: A list of move objects with queen moves combined
        '''
        # simple way to do this is just treat it as both a rook and a bishop
        self.get_rook_moves(row, col, moves)
        self.get_bishop_moves(row, col, moves)
        return moves

    def get_knight_moves(self, row: int, col: int, moves: list) -> list[Move]:
        '''
        Creates a list of move objects that are associated with knights which means:
            L-Shape moves or 2 squares forward and one sideways(or the other way around)

        Args:
            row (int): row index of board array
            col (int): column index of board array
            moves (list[Move]): a list of existing moves

        Returns:
            list[Move]: A list of move objects with knight moves combined
        '''
        # Define all possible knight move directions
        knight_moves = [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)]

        for dr, dc in knight_moves:
            r, c = row + dr, col + dc
            if 0 <= r < 8 and 0 <= c < 8:
                if self.board_array[r][c] == '--' or self.board_array[r][c][0] != self.board_array[row][col][0]:
                    moves.append(Move(self, (row, col, r, c)))

        return moves

    def get_king_moves(self, row: int, col: int, moves: list) -> list[Move]:
        '''
        Creates a list of move objects that are associated with kings which means:
            1. Moving to adjacent squares
            2. Kingside and Queenside castling

        Args:
            row (int): row index of board array
            col (int): column index of board array
            moves (list[Move]): a list of existing moves

        Returns:
            list[Move]: A list of move objects with king moves combined
        '''
        # Define all possible king move directions
        king_moves = [(1, 0), (-1, 0), (0, 1), (0, -1),
                    (1, 1), (1, -1), (-1, 1), (-1, -1)]

        for dr, dc in king_moves:
            r, c = row + dr, col + dc
            if 0 <= r < 8 and 0 <= c < 8:
                if self.board_array[r][c] == '--' or self.board_array[r][c][0] != self.board_array[row][col][0]:
                    moves.append(Move(self, (row, col, r, c)))

        return moves

    def get_castling_moves(self, row: int, col: int, moves: list) -> list[Move]:
        '''
        this function will update the moves list by adding castling moves in it, there are 3 conditions for that
            1. The king should have the specific castling rights(see castling rights class for details)
            2. The king shouldn't be in check
            3. The 2 adjacent squares towards the side of castling shouldn't be under attack and should be empty

        Args:
            row (int): position of the king
            col (int): position of the king
            moves (list[Move]): The existing list with all the moves in it

        Returns:
            list[Move]: The updated list with castling moves
        '''
        # one possible approach was to add this function in the get king moves function but that lead to infinite recursion:
        # in_check -> square_under_attack -> get_psuedo_legal_moves -> get_king_moves -> get_king_moves -> get_castling_moves -> back to start
        # therefore this is a separate function called before validating legal moves

        if self.in_check():
            return moves   # cannot castle if the king is in check

        if (self.white_to_move and self.castling_rights.has_rights('K')) or \
            (not self.white_to_move and self.castling_rights.has_rights('k')):   # kingside castling
            if self.board_array[row][col+1] == self.board_array[row][col+2] == '--' and \
                not self.square_under_attack(row, col+1) and not self.square_under_attack(row, col+2):   # if 2 right squares are empty and not under attack
                moves.append(Move(self, (row, col, row, col+2), is_castling=True))

        if (self.white_to_move and self.castling_rights.has_rights('Q')) or \
            (not self.white_to_move and self.castling_rights.has_rights('q')):   # queenside castling
            if self.board_array[row][col-1] == self.board_array[row][col-2] == '--' and \
                not self.square_under_attack(row, col-1) and  not self.square_under_attack(row, col-2):   # if 2 left are empty and not under attack
                moves.append(Move(self, (row, col, row, col-2), is_castling=True))

        return moves