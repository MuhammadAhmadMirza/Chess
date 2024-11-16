'''
This class, named "Move", represents a chess move and provides functionalities to handle moves in a chess game.
It includes methods to convert coordinates to Universal Chess Interface (UCI) notation and generate 
Standard Algebraic Notation (SAN) for moves.

Key Features:
- Initialization: Initializes a Move object with necessary details such as the chess board, start and end coordinates, promoted piece, castling indication, and check indication.
- Representation: Provides a string representation of the move using SAN notation.
- Comparison: Allows comparison of moves based on their UCI notation.
- UCI Conversion: Converts coordinates to UCI notation for convenient understanding and communication.
- SAN Generation: Generates SAN notation for the move based on the piece moved, captured piece, castling, promotion, and check.
- Handling Different Move Types: Handles different types of moves including pawn moves, castling, and other piece moves.
'''

from typing import Union

class Move:
    '''
    This will take coordinates in  the form python indexing coordinates as rows and columns and make a move which contains the follow info:
        1. start and destination coordinates according to indexes in a 2d array
        2. moved and captured piece(the extra details are necessary for undo purposes) + promotion(extra case)
        3. the move in uci notation
    '''
    file_map = {0: 'a', 1: 'b', 2: 'c', 3: 'd', 4: 'e', 5: 'f', 6: 'g', 7: 'h'}
    rank_map = {7: '1', 6: '2', 5: '3', 4: '4', 3: '5', 2: '6', 1: '7', 0: '8'}

    def __init__(self, board, coordinates: Union[tuple, list], promoted_piece: str = None, is_castling: bool = False \
                 , is_check: bool = False) -> None:
        """
        Initializes a Move object.

        Args:
            board (Board): The chess board object.
            coordinates (tuple or list): The coordinates of the move in the format (start_row, start_col, end_row, end_col).
            promoted_piece (str, optional): The piece to which a pawn is promoted. Defaults to None.
            is_castling (bool, optional): Indicates if the move is a castling move. Defaults to False.
            is_check (bool, optional): Indicates if the move results in a check. Defaults to False.
        """
        
        # abstraction to make dealing with making move classes and other stuff easier
        self.board = board

        self.start_row = coordinates[0]
        self.start_col = coordinates[1]
        self.end_row = coordinates[2]
        self.end_col = coordinates[3]

        self.piece_moved = board.board_array[self.start_row][self.start_col]
        self.piece_captured = board.board_array[self.end_row][self.end_col]
        self.is_check = is_check

        self.is_castling = is_castling
        self.promoted_piece = promoted_piece
        self.uci = self.coordinates_to_uci(coordinates)
        self.san = self.get_san()

    def __repr__(self) -> str:
            """
            Returns a string representation of the Move object.
            
            The string representation is the Standard Algebraic Notation (SAN) of the move.
            
            Returns:
                str: The SAN representation of the move.
            """
            return self.san

    def __eq__(self, other) -> bool:
        """
        Check if two Move objects are equal.

        Args:
            other (Move): The other Move object to compare with.

        Returns:
            bool: True if the two Move objects are equal, False otherwise.
        """
        return self.uci == other.uci

    def __str__(self) -> str:
        """
        Returns a string representation of the Move object.
        
        Returns:
            str: The string representation of the Move object.
        """
        return self.san

    def coordinates_to_uci(self, coordinates: Union[list, tuple]) -> str:
        '''
        This will make a uci sting(universal chess interface) for each move for convenient understanding and communication

        Args:
            coordinates (list or tuple): A list of index coordinates of starting and destination squares

        Returns:
            str: The uci string
        '''
        if self.promoted_piece is not None:   # promotion has different uci notation
            uci = self.file_map[self.start_col] + self.file_map[self.end_col] + self.rank_map[self.end_row] + '=' + self.promoted_piece
            return uci

        # the swapping of order is necessary here as the input is in y, x order so that we can deal with indexing more easily
        uci = self.file_map[coordinates[1]] + self.rank_map[coordinates[0]] + self.file_map[coordinates[3]] + self.rank_map[coordinates[2]]
        return uci

    def get_san(self) -> str:
        '''
        This function will use the details of the current move and make the san(standard algebraic notation) for it

        Returns:
            str: The move in san
        '''
        if self.piece_moved[1] == 'p':   # pawn moves
            san = self.uci[2:] if self.promoted_piece is None else self.uci[1:]
            if self.piece_captured != '--' or self.start_col != self.end_col:   #  add x for captures including en passants
                san = self.uci[0] + 'x' + san

        elif self.is_castling:   # castling cases
            san = 'O-O' if self.start_col < self.end_col else 'O-O-O'

        else:   # all other piece moves
            san = self.piece_moved[1] + self.uci[2:]
            if self.piece_captured != '--':
                san = san[0] + 'x' + san[1:]

        if self.is_check:
            san += '+'

        return san