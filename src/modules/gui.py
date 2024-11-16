'''
This file, named "main.py", is responsible for drawing the chessboard and all graphical user interface (GUI) components for a chess game
using the Pygame library. It utilizes various classes and modules, including the `Board` class, the `Move` class, and the
`coordinates_converter` module, to manage game logic, moves, and coordinate conversions.

The key functionalities and components of this file include:

1. Initialization: 
   - Initializes Pygame and sets up the display window with appropriate dimensions.
   - Defines constants and variables for board size, padding, piece size, colors, and other GUI elements.

2. Load Images and Sounds: 
   - Loads images for chess pieces and icons, as well as sounds for different game events.

3. Display Message: 
   - Defines a function to display messages on the Pygame window with a semi-transparent background.

4. Draw Text Box: 
   - Draws a text box with specified text at a given position on the screen.

5. Color Board: 
   - Draws the squares on the chessboard with alternating colors.
   - Draws coordinates (both horizontal and vertical) on the board.

6. Update Engine Panel: 
   - Updates the side panel which has top engine lines and evaluation scores.

7. Update Move Log: 
   - Updates the move log displayed on the GUI, showing the sequence of moves made in the game.
   - Renders move numbers and move text, and handles scrolling for long move logs.

8. Handle Scrolling: 
   - Handles scrolling of the move log using the mouse wheel.

9. Draw Pieces: 
   - Draws chess pieces on the board based on the current board position.

10. Highlight Squares: 
    - Highlights legal move squares with transparent overlays when a piece is selected.

11. Highlight Checks: 
    - Highlights the king's square if the king is in check, with fading color effects.

12. Get Promoted Piece: 
    - Displays a promotion menu when a pawn reaches the end of the board, allowing the player to choose a piece for promotion.

13. Play Sound: 
    - Plays appropriate sounds based on the move made in the game.

14. Update Display: 
    - Updates the entire display with the current state of the board and GUI elements.

15. Main Function: 
    - The main function initializes the game, handles the game loop, and manages user input.
    - It listens for mouse clicks, keyboard events, and window resizing, and responds accordingly.
    - Manages the interaction between GUI elements and game logic, including making moves, undoing moves, and handling various UI actions.

This file serves as the core of the graphical interface for the chess game, facilitating user interaction and providing visual feedback for game events and actions.
'''

# unfinished, stockfish integration is buggy and needs terminations management, initialization error handling and the option to play stockfish

import sys, os, pygame, pyperclip, threading, time, psutil, signal
from utilities.resource_path import resource_path
from modules.board import Board
from modules.move import Move
from modules.coordinates_converter import coordinates_converter
from modules.engine import get_top_lines
import sys, os
try:
    pass
except ImportError as e:
    print(f'Error importing modules: {e}')
    sys.exit()

pygame.init()

# Get screen size
SCREEN_WIDTH, SCREEN_HEIGHT = pygame.display.Info().current_w, pygame.display.Info().current_h
ASPECT_RATIO = SCREEN_WIDTH / SCREEN_HEIGHT
window_width, window_height = SCREEN_WIDTH * 0.8, SCREEN_HEIGHT * 0.8   # 80 percent of the screen size initially to keep some room for taskbar and close button 

# setting up board dimensions
BOARD_WIDTH = BOARD_HEIGHT = window_height * (15/16)
PADDING = BOARD_HEIGHT // 30
SIDE_PANEL_WIDTH = window_width - BOARD_WIDTH - PADDING * 3   # keeping aspect ratio same as that of the screen
SQUARE_SIZE = BOARD_HEIGHT // 8
PIECE_SIZE = SQUARE_SIZE*0.9
SQ_PIECE_DIFFERENCE = (SQUARE_SIZE - PIECE_SIZE) // 2   # to keep the pieces aligned in the centre of the squares

# other details
MAX_FPS = 60
IMAGES = {}   # a dictionary mapping all pieces to their respective images
SOUNDS = {}   # a similar dictionary for sounds

# colors
LIGHT_THEME = False
PADDING_COLOR = (0, 0, 0)
MOVE_LOG_COLOR = (40, 40, 40)
ENGINE_PANEL_COLOR = (70, 70, 70)
TEXT_COLOR = (255, 255, 255)
LIGHT_SQ, DARK_SQ = (255, 220, 170), (168, 115, 72)   # square colors

# setting up window and board
pygame.display.set_caption('Chess')
pygame.display.set_icon(pygame.image.load(resource_path('assets\images\chess_icon.png')))
clock = pygame.time.Clock()
screen = pygame.display.set_mode((BOARD_WIDTH + PADDING*3 + SIDE_PANEL_WIDTH, BOARD_HEIGHT + PADDING*2), pygame.RESIZABLE)
board = Board()
pov = True   # True for white player perspective and False for black

# program termination management
def terminate_process_tree(pid):
    """Terminate a process and all its children."""
    parent = psutil.Process(pid)
    for child in parent.children(recursive=True):
        child.terminate()
    parent.terminate()
    parent.wait()

def cleanup():
    print("Cleaning up...")
    # Terminate all processes related to Stockfish
    terminate_process_tree(os.getpid())

def signal_handler(sig, frame):
    print("Signal received, cleaning up...")
    cleanup()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def display_message(window, message: str, color:tuple = (255, 0, 0), duration: int =1000):
    """
    Display a message on the given window with a semi-transparent background.

    Args:
        window: The Pygame window surface to display the message on.
        message (str): The message to be displayed.
        color (tuple, optional): The color of the text. Defaults to (255, 0, 0) (red).
        duration (int, optional): The duration in milliseconds for which the message should be displayed. Defaults to 1000ms (1 second).
    """
    font = pygame.font.Font(None, 36)  # Smaller font size
    text = font.render(message, True, color)
    text_rect = text.get_rect(center=(window.get_width() // 2, window.get_height() // 2))

    # Create a semi-transparent background without padding and with rounded edges
    background_rect = text_rect.inflate(20, 20)  # Slightly inflate for padding
    background_surface = pygame.Surface(background_rect.size, pygame.SRCALPHA)  # SRCALPHA for per-pixel alpha
    background_surface.fill((0, 0, 0, 0))  # Fully transparent to start

    # Draw the rounded rectangle
    pygame.draw.rect(background_surface, (0, 0, 0, 128), background_surface.get_rect(), border_radius=7)  # Rounded edges

    # Draw the background and the text
    window.blit(background_surface, background_rect.topleft)
    window.blit(text, text_rect)

    pygame.display.update()
    pygame.time.wait(duration)

def draw_text_box(text: str, pos: tuple) -> None:
    """
    Draws a  text box with the given text at the specified position on the screen.

    Args:
        text (str): The text to be displayed in the text box.
        pos (tuple): The top-left position of the text box on the screen.

    Returns:
        None
    """
    pygame.font.init()
    font = pygame.font.SysFont('Arial', 13)  # Set font size to 12
    text_surface = font.render(text, True, (0, 0, 0))
    text_rect = text_surface.get_rect(bottomleft=pos)
    box_rect = text_rect.inflate(5, 2)  # Add smaller padding around the text

    # Draw the smaller text box onto the screen
    pygame.draw.rect(screen, (200, 200, 200), box_rect, border_radius=3)
    pygame.draw.rect(screen, (0, 0, 0), box_rect, 1)  # Border
    screen.blit(text_surface, text_rect)

    pygame.display.flip()

def load_images() -> None:
    '''
    Initialize a global directory of images.
    '''
    pieces = ['wp', 'wR', 'wN', 'wB', 'wK', 'wQ', 'bp', 'bR', 'bN', 'bB', 'bK', 'bQ']
    
    try:
        for piece in pieces:
            # Use os.path.join for platform-independent paths
            image_path = os.path.join('assets', 'images', 'pieces', f'{piece}.png')
            full_image_path = resource_path(image_path)  # Resolve the full path for both dev and production
            
            # Check if the file exists
            if not os.path.exists(full_image_path):
                print(f'Could not find image file: {full_image_path}')
                sys.exit()
            
            # Load the image
            IMAGES[piece] = pygame.transform.smoothscale(pygame.image.load(full_image_path), (PIECE_SIZE, PIECE_SIZE))
    
    except Exception as e:
        print(f'Error loading images: {e}')
        sys.exit()

def load_sounds() -> None:
    '''
    Initialize a global directory of sounds.
    '''
    # Using the word 'music' to avoid case sensitivity issues, but it refers to sounds
    music = ['castling', 'check', 'end', 'illegal', 'capture', 'move', 'promotion']
    
    try:
        for sound in music:
            # Use os.path.join to handle path construction across platforms
            sound_path = os.path.join('assets', 'sounds', f'{sound}.mp3')
            full_sound_path = resource_path(sound_path)  # Resolve the full path for both dev and production
            
            # Check if the file exists
            if not os.path.exists(full_sound_path):
                print(f'Could not find sound file: {full_sound_path}')
                sys.exit()
            
            # Load the sound
            SOUNDS[sound] = pygame.mixer.Sound(full_sound_path)
    
    except Exception as e:
        print(f'Error loading sound: {e}')
        sys.exit()

def color_board(pov: bool, light: tuple = LIGHT_SQ, dark: tuple = DARK_SQ) -> None:
    '''
    Draw the squares on the board.
    The top left square is always light.
    '''
    screen.fill(PADDING_COLOR)
    global colors
    colors = [pygame.Color(light), pygame.Color(dark)]
    for row in range(8):
        for column in range(8):
            color = colors[((row + column) % 2)]
            pygame.draw.rect(screen, color, pygame.Rect(column * SQUARE_SIZE + PADDING, row * SQUARE_SIZE + PADDING, SQUARE_SIZE, SQUARE_SIZE))
    draw_coordinates(pov)

engine_depth = 20
top_lines = []
def display_loading_screen():
    # Define colors
    rect_color = (179, 0, 3)  # Color for the rectangle
    text_color = TEXT_COLOR
    
    # Create the loading text
    loading_font = pygame.font.Font(None, int(BOARD_HEIGHT * 1/20))
    loading_text = loading_font.render("Loading...", True, text_color)
    
    # Define rectangle size and position
    text_rect = loading_text.get_rect(center=(BOARD_WIDTH + SIDE_PANEL_WIDTH // 2, BOARD_HEIGHT // 4))
    rect_width, rect_height = text_rect.width + 20, text_rect.height + 20
    rect_x, rect_y = text_rect.centerx - rect_width // 2, text_rect.centery - rect_height // 2
    loading_rect = pygame.Rect(rect_x, rect_y, rect_width, rect_height)
    
    pygame.draw.rect(screen, rect_color, loading_rect, border_radius=5)
    screen.blit(loading_text, text_rect)
    pygame.display.update(loading_rect)

def run_get_top_lines(board_fen, engine_depth, result_container):
    result_container['top_lines'] = get_top_lines(board_fen, engine_depth)

def update_engine_panel(re_analyze: bool, font=pygame.font.Font(None, int(BOARD_HEIGHT * 1/20)), callback=None) -> None:
    global top_lines
    pygame.draw.rect(screen, ENGINE_PANEL_COLOR, pygame.Rect(BOARD_WIDTH + 2 * PADDING, PADDING, SIDE_PANEL_WIDTH, BOARD_HEIGHT // 2))
    global engine_icon; engine_icon = pygame.transform.smoothscale(pygame.image.load(resource_path(os.path.join('assets', 'images', 'engine_icon.png'))), (PADDING * 4, PADDING * 4))

    screen.blit(engine_icon, (BOARD_WIDTH + PADDING * 2, PADDING))
    
    text_surface = font.render("Stockfish 16.1", True, TEXT_COLOR)
    icon_center_y = PADDING + engine_icon.get_height() // 2
    text_y = icon_center_y - text_surface.get_height()
    text_x = BOARD_WIDTH + PADDING * 2 + engine_icon.get_width() + PADDING
    screen.blit(text_surface, (text_x, text_y))
    screen.blit(font.render(f"Depth: {engine_depth}", True, TEXT_COLOR), (text_x, text_y + font.get_height() + PADDING // 2))
    
    if re_analyze:
        # Show loading screen while running get_top_lines in a separate thread
        result_container = {}
        thread = threading.Thread(target=run_get_top_lines, args=(board.board_to_fen(), engine_depth, result_container))
        thread.start()

        while thread.is_alive():
            display_loading_screen()

        top_lines = result_container['top_lines']
    
    # Blit top lines below the engine icon
    line_height = font.get_height() + PADDING // 2
    x = BOARD_WIDTH + PADDING * 2.5
    y = PADDING + engine_icon.get_height() + PADDING
    font = pygame.font.Font(None, int(BOARD_HEIGHT * 1/23))  # changing font size to a lower value so that long lines fit in the screen
    
    for line in top_lines:
        eval_surface = font.render(line.eval, True, TEXT_COLOR)
        eval_width, eval_height = eval_surface.get_size()
        
        # Calculate the dimensions of the rectangle
        rect_width = eval_width + PADDING // 2
        rect_height = line_height
        
        # Create the rectangle centered around the eval text
        eval_rect = pygame.Rect(0, 0, rect_width, rect_height)
        eval_rect.center = (x + PADDING * 1.5, y + line_height // 2)
        
        # Draw the rounded rectangle
        border_radius = 5
        pygame.draw.rect(screen, (200, 200, 200) if LIGHT_THEME else (20, 20, 20), eval_rect, border_radius=border_radius)
        
        # Blit the eval text surface
        screen.blit(eval_surface, (eval_rect.centerx - eval_width // 2, eval_rect.centery - eval_height // 2))
        
        # Render and blit the rest of the line
        line_surface = font.render(line.get_single_string(), True, TEXT_COLOR)
        screen.blit(line_surface, (x + engine_icon.get_width(), y))
        
        # Move y position for the next line
        y += line_height
    
    pygame.display.update(pygame.Rect(BOARD_WIDTH + 2 * PADDING, PADDING, SIDE_PANEL_WIDTH, BOARD_HEIGHT // 2))
    
    # Call the callback to update the display
    if callback:
        callback()

def start_update_engine_panel_thread(re_analyze: bool):
    '''Start a thread to update the engine panel and update the display when done.'''
    def callback():
        update_display(pygame.Rect((BOARD_WIDTH + 2 * PADDING, PADDING, SIDE_PANEL_WIDTH, BOARD_HEIGHT // 2)), scrolling_size, update_now=True)
    
    thread = threading.Thread(target=update_engine_panel, args=(re_analyze, pygame.font.Font(None, int(BOARD_HEIGHT * 1/20)), callback))
    thread.start()

start_move_number = None
def update_move_log(scrolling_size: float = 0, font=pygame.font.Font(None, int(BOARD_HEIGHT * 1/17))) -> None:
    '''update the move log on the right side of the screen'''
    pygame.draw.rect(screen, MOVE_LOG_COLOR, pygame.Rect(BOARD_WIDTH + 2 * PADDING, BOARD_HEIGHT // 2 + PADDING, SIDE_PANEL_WIDTH, BOARD_HEIGHT // 2))

    global start_move_number
    if start_move_number is None:
        start_move_number = board.fullmove_number

    move_log_surface = pygame.Surface((SIDE_PANEL_WIDTH, BOARD_HEIGHT // 2))
    move_log_surface.fill(MOVE_LOG_COLOR)

    # Render move log
    move_log = board.move_log
    y_offset = scrolling_size + PADDING // 2
    line_height = font.get_height() + PADDING // 2

    move_counter = start_move_number
    moves_per_line = 2
    x = PADDING
    move_number_text = f"{move_counter}."
    move_number_surface = font.render(move_number_text, True, (100, 100, 100) if LIGHT_THEME else (200, 200, 200))
    move_number_width = move_number_surface.get_width()

    for i in range(0, len(move_log), moves_per_line):
        moves = move_log[i:i+moves_per_line]
        x_coord = x + move_number_width + PADDING  # Set initial x coordinate for the move text
        for idx, move in enumerate(moves, start=1):
            move_text = f"{move}"
            move_text_surface = font.render(move_text, True, (0, 255, 0) if i + idx >= len(move_log) else TEXT_COLOR)  # Green color for last move text

            if idx == 1:
                # Blit move number only for the first move of each line
                move_log_surface.blit(move_number_surface, (x, y_offset + (line_height - move_number_surface.get_height()) // 2))
                move_counter += 1  # Increment move number per line
                move_number_text = f"{move_counter}."
                move_number_surface = font.render(move_number_text, True, (100, 100, 100) if LIGHT_THEME else (200, 200, 200))
                move_number_width = move_number_surface.get_width()
            else:
                # Set x coordinate for the second move
                x_coord = SIDE_PANEL_WIDTH // 2.5

            # Calculate dimensions for transparent rectangle
            rect_width = move_text_surface.get_width() + PADDING  # Adjust width to fit the text
            rect_height = move_text_surface.get_height() + PADDING // 50  # Adjust height to fit the text
            rect_x = x_coord  # Center the rectangle horizontally
            rect_y = y_offset + (line_height - rect_height) // 2  # Center the rectangle vertically

            # Draw transparent rectangle over move text
            pygame.draw.rect(move_log_surface, ((170, 170, 170, 150) if LIGHT_THEME else (60, 60, 60, 150)), pygame.Rect(rect_x, rect_y, rect_width, rect_height), border_radius=5)

            # Blit move text
            move_log_surface.blit(move_text_surface, (x_coord + PADDING // 2, y_offset + PADDING // 4))

            # Adjust x for the next move
            x += move_number_width + move_text_surface.get_width() + PADDING * 2  # Adjust for spacing between move number and move text

        y_offset += line_height  # Move to the next line
        x = PADDING  # Reset x coordinate for the next line

    screen.blit(move_log_surface, (BOARD_WIDTH + 2 * PADDING, BOARD_HEIGHT // 2 + PADDING))

    draw_buttons()

def draw_buttons() -> None:
    '''will draw the four buttons on the right side of the screen for copy, paste, flip and light theme'''
    # drawing buttons
    button_positions = [(window_width - PADDING * 4, BOARD_HEIGHT // 2 + PADDING),
                        (window_width - PADDING * 4, BOARD_HEIGHT // 2 + PADDING * 5),
                        (window_width - PADDING * 4, BOARD_HEIGHT // 2 + PADDING * 9),
                        (window_width - PADDING * 4, BOARD_HEIGHT // 2 + PADDING * 13)]
    button_images = ['assets\images\copy_icon.png', 'assets\images\paste_icon.png', 'assets/images/flip_icon.png', 'assets\images\light_icon.png']

    for position, image_path in zip(button_positions, button_images):
        button_image = pygame.transform.smoothscale(pygame.image.load(resource_path(os.path.join(image_path))), (PADDING * 3, PADDING * 3))
        screen.blit(button_image, position)

def handle_scrolling(event, scrolling_size):
    '''a function to handle scrolling of the move log using the mouse wheel'''
    if event is None:
        start_time = time.time()
        # this will recursively scan an imaginary line at the bottom for a green pixel which indigates the last move
        # if its not found it will move down and update the move log thus increasing the scrolling size until the last move is found
        # i know there are better and more efficient methods but i was stuck, so this is what you get
        pixel_found = False
        while len(board.move_log) > 18 and not pixel_found:    
            for pixel in range(int(BOARD_WIDTH + PADDING * 2), int(BOARD_WIDTH + PADDING * 2 + SIDE_PANEL_WIDTH)):
                pixel_color = screen.get_at((pixel, int((window_height - PADDING * 5) // 1)))
                if pixel_color == (0,255, 0):
                    pixel_found = True
                    break
            scrolling_size -= 5
            update_move_log(scrolling_size)
            pygame.display.update(pygame.Rect(BOARD_WIDTH + PADDING * 2, BOARD_HEIGHT // 2 + PADDING, SIDE_PANEL_WIDTH, BOARD_HEIGHT // 2))
            if time.time() - start_time >= 5:
                # incase it somehow skips the green part
                scrolling_size = 0
                break

    elif event.type == pygame.MOUSEWHEEL:
        scrolling_size += event.y * 10  # Adjust the scrolling speed as needed
        # Calculate the maximum scroll size based on the total height of the text in the move log
        total_text_height = len(board.move_log) * pygame.font.Font(None, int(PADDING * 1.5)).get_height()
        max_scroll = max(0, total_text_height - (BOARD_HEIGHT // 2) + PADDING)
        # Ensure the scrolling size stays within the valid range
        scrolling_size = max(-max_scroll, min(0, scrolling_size))

    return scrolling_size

def draw_coordinates(pov: bool, font=pygame.font.Font(None, int(BOARD_HEIGHT * 1/20))) -> None:
    # Draw horizontal coordinates (a-h) slightly below the squares
    coordinate_labels = 'hgfedcba' if not pov else 'abcdefgh'
    for i in range(8):
        # Draw horizontal coordinates (a-h) slightly below the squares
        text_surface = font.render(coordinate_labels[i], True, TEXT_COLOR)  # White color
        text_rect = text_surface.get_rect(center=(i * SQUARE_SIZE + SQUARE_SIZE // 2 + PADDING, SQUARE_SIZE * 8 + PADDING * 3/2))
        screen.blit(text_surface, text_rect)

    # Draw vertical coordinates (1-8) on the left side
    coordinate_labels = '12345678' if not pov else '87654321'
    for i in range(8):
        # Draw vertical coordinates (1-8) on the left side
        text_surface = font.render(coordinate_labels[i], True, TEXT_COLOR)  # White color
        text_rect = text_surface.get_rect(center=(PADDING // 2, i * SQUARE_SIZE + SQUARE_SIZE // 2 + PADDING))
        screen.blit(text_surface, text_rect)

def draw_pieces(board: list, pov: bool) -> None:
    '''
    Draw the pieces on the board using the current board position array

    Args:
        board (list): A array from the board class
        pov (Bool): The board perspective(white or black)
        size(int): The desired size for the pieces
    '''
    for row in range(8):
        for column in range(8):
            piece = board[row][column]
            if piece != '--':
                if pov:
                    screen.blit(IMAGES[piece], pygame.Rect(column * SQUARE_SIZE + PADDING + SQ_PIECE_DIFFERENCE, row * SQUARE_SIZE + PADDING + SQ_PIECE_DIFFERENCE, PIECE_SIZE, PIECE_SIZE))
                else:
                    # When pov is False, adjust the row and column indices to reflect the black perspective
                    screen.blit(IMAGES[piece], pygame.Rect((7 - column) * SQUARE_SIZE + PADDING + SQ_PIECE_DIFFERENCE, (7 - row) * SQUARE_SIZE + PADDING + SQ_PIECE_DIFFERENCE, PIECE_SIZE, PIECE_SIZE))

def highlight_squares(pov: bool, coord: tuple = None) -> None:
    '''
    Iterates through the legal moves and draws transparent squares at their end positions if they match
    the selected piece's starting position. Adjusts the calculations based on the perspective (pov).

    Args:
        pov (Bool): The board perspective(white or black)
    '''
    if coord is not None:
        transparent_square = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        transparent_square.fill((20, 20, 20, 140))  # Fill with semi-transparent color
        for move in board.legal_moves:
            end_row, end_col = (move.end_row, move.end_col) if pov else (7 - move.end_row, 7 - move.end_col)

            if move.start_row == coord[0] and move.start_col == coord[1]:
                if move.piece_captured != '--' or (end_row, end_col) == board.en_passant_square:
                    transparent_square.fill((255, 0, 0, 140))  # Red for captures
                else:
                    transparent_square.fill((20, 20, 20, 140))
                    
                end_x = end_col * SQUARE_SIZE + PADDING
                end_y = end_row * SQUARE_SIZE + PADDING
                screen.blit(transparent_square, (end_x, end_y))
    draw_pieces(board.board_array, pov)    # drawing the pieces again to avoid the transparent squares to overlap the pieces
        
def highlight_checks(pov: bool):
    '''This function will highlight the king square if the king is in check and make the square color fade over time.'''
    update_display(pygame.Rect(0, 0, BOARD_WIDTH + PADDING * 2, BOARD_HEIGHT + PADDING * 2), scrolling_size)
    king_square = board.white_king_pos if board.white_to_move else board.black_king_pos 
    king_square = king_square if pov else (7 - king_square[0], 7 - king_square[1])

    if board.in_check():
        highlight_color = (255, 50, 50)
        square_color = LIGHT_SQ if (king_square[0] + king_square[1]) % 2 == 0 else DARK_SQ
        color_diff = (square_color[0] - highlight_color[0], square_color[1] - highlight_color[1], square_color[2] - highlight_color[2])
        cycles = 20
        for i in range(cycles):
            highlight_color_i = (highlight_color[0] + color_diff[0] * i // cycles, highlight_color[1] + color_diff[1] * i // cycles, highlight_color[2] + color_diff[2] * i // cycles)
            pygame.draw.rect(screen, highlight_color_i, pygame.Rect(king_square[1] * SQUARE_SIZE + PADDING, king_square[0] * SQUARE_SIZE + PADDING, SQUARE_SIZE, SQUARE_SIZE))
            draw_pieces(board.board_array, pov)
            pygame.display.flip()
            pygame.time.delay(15)

def get_promoted_piece(row: int, col: int, color: str, pov: bool) -> str:
    '''
        This function first draws the promotion menu and then waits for the player to click on a promotion piece and
        returns the selected piece bu creating a nested game loop

    Args:
        row (int): row of the selected piece
        col (int): column on the selected piece
        color (str): 'w' or 'b'
        pov (Bool): The board perspective(white or black)

    Returns:
        str: The capital character for the promoted piece type('Q', 'N', 'R', 'B')
    '''
    promotion_menu_width = SQUARE_SIZE
    promotion_menu_height = SQUARE_SIZE * 4
    background_color = (190, 190, 190)

    # Adjust menu position based on perspective and color
    if pov:
        if color == 'w':
            menu_x = col * SQUARE_SIZE + PADDING
            menu_y = row * SQUARE_SIZE + PADDING
        else:
            menu_x = col * SQUARE_SIZE + PADDING
            menu_y = row*SQUARE_SIZE - 3*SQUARE_SIZE + PADDING
    else:
        if color == 'w':
            menu_x = (7-col) * SQUARE_SIZE + PADDING
            menu_y = (7-row) * SQUARE_SIZE - 3*SQUARE_SIZE + PADDING
        else:
            menu_x = (7-col) * SQUARE_SIZE + PADDING
            menu_y = (7-row) * SQUARE_SIZE + PADDING

    # Define the order of promotion pieces based on the color and perspective
    promotion_order = {
        'w': ['wQ', 'wN', 'wR', 'wB'] if pov else ['wB', 'wR', 'wN', 'wQ'],
        'b': ['bB', 'bR', 'bN', 'bQ'] if pov else ['bQ', 'bN', 'bR', 'bB']
    }

    # Draw the background of the promotion menu
    pygame.draw.rect(screen, background_color, (menu_x, menu_y, promotion_menu_width, promotion_menu_height))

    # Draw the promotion menu by blitting the images of the promotion pieces
    for i, piece in enumerate(promotion_order[color]):
        piece_image = IMAGES[piece]
        piece_y = menu_y + i * (promotion_menu_height // len(promotion_order[color]))
        screen.blit(piece_image, (menu_x + SQ_PIECE_DIFFERENCE, piece_y + SQ_PIECE_DIFFERENCE))

    pygame.display.flip()

    # Wait for the player to click on a promotion piece
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                click_x, click_y = pygame.mouse.get_pos()
                # Check if the click is within the promotion menu bounds
                if menu_x <= click_x <= menu_x + promotion_menu_width and \
                    menu_y <= click_y <= menu_y + promotion_menu_height:
                    # Calculate the selected index based on the click's position relative to the top of the menu
                    selected_index = round((click_y - menu_y) // (promotion_menu_height // len(promotion_order[color])))
                    # only return the piece type as it is all we need in the move class
                    return promotion_order[color][selected_index][1]

def play_sound(move: Move) -> None:
    '''
    will play the appropriate sound based on the move made according to the hierarchy made by chess.com and lichess.org

    Args:
        move (Move): The current move that is supposed to be made
    '''
    # game end sound will be outside this function
    if move in board.legal_moves:
        if move.is_check:
            SOUNDS['check'].play()
        elif move.piece_captured != '--' or (move.end_row, move.end_col) == board.en_passant_square:
            SOUNDS['capture'].play()
        elif move.piece_moved[1] == 'K' and abs(move.start_col - move.end_col) == 2:
            SOUNDS['castling'].play()
        elif move.promoted_piece is not None:
            SOUNDS['promotion'].play()
        else:                    
            SOUNDS['move'].play()
    else:
        SOUNDS['illegal'].play()

def update_display(update_rect: pygame.Rect, scrolling_size, selected_piece_coordinates: tuple = None, update_now: bool = True) -> None:
    """
    Updates the display by drawing the chessboard, pieces, move log, engine panel, and highlighting squares.

    Args:
        update_rect (pygame.Rect): The rectangle area to update on the display, None if all the screen should be updated.
        scrolling_size (float, optional): The scrolling size for dynamically updating the scroll level.
        selected_piece_coordinates (tuple, optional): The coordinates of the selected chess piece. Defaults to None.
        update_now (bool, optional): Whether to update the display immediately. Defaults to True.
        
    Returns:
        None
    """        
    color_board(pov)
    highlight_squares(pov, selected_piece_coordinates)
    draw_pieces(board.board_array, pov)
    update_move_log(scrolling_size)
    update_engine_panel(False)

    if board.is_checkmate:   # highlinghting the checkmated king sqaure red permenently
        king_square = board.white_king_pos if board.white_to_move else board.black_king_pos if pov else (7 - board.white_king_pos[0], 7 - board.white_king_pos[1])
        pygame.draw.rect(screen, (180, 40, 30), pygame.Rect(king_square[1] * SQUARE_SIZE + PADDING, king_square[0] * SQUARE_SIZE + PADDING, SQUARE_SIZE, SQUARE_SIZE))
        draw_pieces(board.board_array, pov)
        
    if update_now:
        if update_rect is not None:
            pygame.display.update(update_rect)
        else:
            pygame.display.flip()

def main() -> None:
    '''
    The main function of the chess game.
    This function initializes the chess game and handles the game loop. It creates a chess board, loads the images,
    and updates the display. It also handles user input and performs actions based on the input.
    '''
    global screen, BOARD_WIDTH, BOARD_HEIGHT, SIDE_PANEL_WIDTH, PADDING, SQUARE_SIZE, PIECE_SIZE, PADDING_COLOR, LIGHT_THEME, SQ_PIECE_DIFFERENCE,\
        MOVE_LOG_COLOR, ENGINE_PANEL_COLOR, TEXT_COLOR, LIGHT_SQ, DARK_SQ, window_height, window_width, pov, board, engine_depth
    # to see if we are moving a piece or tapping the menu
    in_board = lambda: PADDING < pygame.mouse.get_pos()[0] < BOARD_WIDTH + PADDING and \
            PADDING < pygame.mouse.get_pos()[1] < BOARD_HEIGHT + PADDING 
    
    load_images()
    load_sounds()
    
    # tp pass into update_display to update only selectivea areas for optimization
    board_rect = pygame.Rect(0, 0, BOARD_WIDTH + PADDING, BOARD_HEIGHT + PADDING)
    side_panel_rect = pygame.Rect(BOARD_WIDTH + PADDING, 0, SIDE_PANEL_WIDTH + PADDING * 2, BOARD_HEIGHT + PADDING)
    
    global scrolling_size; scrolling_size = 0
    clicks = []  # The first 2 indexes will store the start click and the second 2 will have the destination click
    dragging = False
    selected_piece = None   # will store the coordinates of the selected piece
    last_move_is_legal = True   # a flag to make sure that the last move was legal so that we can re analayze the position after making the move

    update_display(None, scrolling_size)
    start_update_engine_panel_thread(re_analyze=True)
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not dragging:
                
                if in_board() and not (board.is_checkmate or board.is_draw):   # piece moves
                    row, col = coordinates_converter(pygame.mouse.get_pos(), pov, SQUARE_SIZE, PADDING)
                    selected_piece = (row, col)
                    # first click and the clicked square is not empty and is not an opponent piece
                    if len(clicks) == 0 and board.board_array[row][col] != '--' and board.board_array[row][col][0] == ('w' if board.white_to_move else 'b'):
                        clicks.extend([row, col])
                        dragging = True
                        highlight_squares(pov, selected_piece)
                        pygame.display.flip()

                    elif len(clicks) == 2 and [row, col] != clicks:   # the two click move making method
                        dragging = False
                        selected_piece = None
                        clicks.extend([row, col])

                        move = Move(board, clicks)
                        if ((move.end_row == 0  or move.end_row == 7) and board.board_array[move.start_row][move.start_col][1] == 'p'   # if we have a case of promotion
                            and move.start_row == (1 if move.piece_moved[0] == 'w' else 6)):   # and the move pawn was only one square away from promotion(to avoid popping up of menu when not needed)
                            promoted_piece = get_promoted_piece(move.end_row, move.end_col, board.board_array[move.start_row][move.start_col][0], pov)
                            move = Move(board, clicks, promoted_piece=promoted_piece)

                        play_sound(move)   # this should come before actually making the move
                            
                        if move in board.legal_moves:
                            last_move_is_legal = True   # this structure of flagging and then reanalyzing is necessary to make sure that the fen has changed after making the move so that we are analyzing the new position
                            
                        board.make_legal_move(move)

                        if board.is_checkmate or board.is_draw:
                            SOUNDS['end'].play()
                        
                        clicks.clear()   # to maintain indexing for the next 2 clicks
                        scrolling_size = handle_scrolling(None, scrolling_size)
                        highlight_checks(pov)
                        if last_move_is_legal:
                            start_update_engine_panel_thread(re_analyze=True)
                    
                    last_move_is_legal = False

                else:   # button clicks
                    mouse_pos = pygame.mouse.get_pos()
                    if window_width - PADDING * 4 <= mouse_pos[0] <= window_width - PADDING:
                        y = mouse_pos[1] - BOARD_HEIGHT // 2
                        if PADDING <= y <= PADDING * 4:
                            # copy fen
                            pyperclip.copy(board.board_to_fen())
                            display_message(screen, "FEN copied to clipboard!", (0, 255, 0))
                        elif PADDING * 5 <= y <= PADDING * 9:
                            # paste fen
                            try:
                                board = Board(pyperclip.paste())
                                display_message(screen, "FEN changed successfully!", (0, 255, 0))
                            except:
                                display_message(screen, "Invalid FEN! Please try again.", (255, 0, 0))
                        elif PADDING * 10 <= y <= PADDING * 13:
                            pov = not pov   # flip perspective
                            update_display(side_panel_rect, scrolling_size, selected_piece)
                        elif PADDING * 14 <= y <= PADDING * 17:
                            LIGHT_THEME = not LIGHT_THEME    # change  theme
                            PADDING_COLOR = (150, 150, 150) if LIGHT_THEME else (0, 0, 0)
                            MOVE_LOG_COLOR = (200, 200, 200) if LIGHT_THEME else (40, 40, 40)
                            ENGINE_PANEL_COLOR = (255, 255, 255) if LIGHT_THEME else (70, 70, 70)
                            TEXT_COLOR = (0, 0, 0) if LIGHT_THEME else (255, 255, 255)
                            update_display(side_panel_rect, scrolling_size, selected_piece) 
                        
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and not (board.is_checkmate or board.is_draw):   # replaces second click when the user is dragging
                dragging = False
                row, col = coordinates_converter(pygame.mouse.get_pos(), pov, SQUARE_SIZE, PADDING)
                if len(clicks) == 2 and clicks != [row, col]:   # only execute of the player tries to drag
                    clicks.extend([row, col])
                    selected_piece = None

                    move = Move(board, clicks)
                    if ((move.end_row == 0  or move.end_row == 7) and board.board_array[move.start_row][move.start_col][1] == 'p'   # if we have a case of promotion
                        and move.start_row == (1 if move.piece_moved[0] == 'w' else 6)):   # and the move pawn was only one square away from promotion(to avoid popping up of menu when not needed)
                        promoted_piece = get_promoted_piece(move.end_row, move.end_col, board.board_array[move.start_row][move.start_col][0], pov)
                        move = Move(board, clicks, promoted_piece=promoted_piece)

                    play_sound(move)
                    
                    if move in board.legal_moves:
                        last_move_is_legal = True
                        
                    board.make_legal_move(move)
                    
                    if board.is_checkmate or board.is_draw:
                        SOUNDS['end'].play()

                    clicks.clear()   # to maintain indexing for the next 2 clicks
                    scrolling_size = handle_scrolling(None, scrolling_size)
                    highlight_checks(pov)
                    if last_move_is_legal:
                        start_update_engine_panel_thread(re_analyze=True)
                    
                last_move_is_legal = False                
                update_display(None, scrolling_size, selected_piece)   # to update the display when we make a move or leave a dragging piece

            elif (event.type == pygame.MOUSEMOTION or pygame.mouse.get_pressed()[0]) and dragging and in_board() and not (board.is_checkmate or board.is_draw) and len(clicks) == 2:   # dragging animation, the conditions are very important
                piece = board.board_array[clicks[0]][clicks[1]]   # taking the moved piece
                # redrawing the board to remove the piece from the previous square
                update_display(board_rect, scrolling_size, selected_piece, update_now=False)
                # redrawing the square underneath the piece
                pygame.draw.rect(screen, LIGHT_SQ if clicks[0] % 2 == clicks[1] % 2 else DARK_SQ, pygame.Rect((clicks[1] if pov else 7 - clicks[1]) * SQUARE_SIZE + PADDING, (clicks[0] if pov else 7 - clicks[0]) * SQUARE_SIZE + PADDING, SQUARE_SIZE, SQUARE_SIZE))
                transparent_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                transparent_surface.fill((20, 20, 20, 170))
                screen.blit(transparent_surface, ((clicks[1] if pov else 7 - clicks[1]) * SQUARE_SIZE + PADDING, (clicks[0] if pov else 7 - clicks[0]) * SQUARE_SIZE + PADDING))
                # drawing the piece finally to be on the top
                screen.blit(IMAGES[piece], pygame.Rect(pygame.mouse.get_pos()[0] - SQUARE_SIZE // 2, pygame.mouse.get_pos()[1] - SQUARE_SIZE // 2, PIECE_SIZE, PIECE_SIZE))
                pygame.display.update(board_rect)

            elif event.type == pygame.MOUSEWHEEL and not in_board():
                # scrolling the moves
                if BOARD_HEIGHT // 2 + PADDING <= pygame.mouse.get_pos()[1]:
                    scrolling_size = handle_scrolling(event, scrolling_size)
                    update_move_log(scrolling_size)
                    pygame.display.flip()
                # changing engine depth
                elif text_y <= pygame.mouse.get_pos()[1] <= text_y + depth_text_surface.get_height() and text_x <= pygame.mouse.get_pos()[0] <= text_x + depth_text_surface.get_width():
                    engine_depth += event.y
                    if engine_depth < 10:
                        engine_depth = 10
                    elif engine_depth >= 35:
                        engine_depth = 35
                    start_update_engine_panel_thread(True)

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:   # undo move
                    board.undo_move()
                    update_display(None, scrolling_size, selected_piece)
                    start_update_engine_panel_thread(re_analyze=True)
                    
            elif event.type == pygame.VIDEORESIZE:

                try:
                    window_width, window_height = event.w, event.h
                    window_ratio = window_width/window_height

                    # defining a range for the aspect ratio to avoid any errors related to overlapping text
                    if not (ASPECT_RATIO - 0.3 <= window_ratio <= ASPECT_RATIO + 0.3) or (window_width < SCREEN_WIDTH * 0.6 or window_height < SCREEN_HEIGHT * 0.6):
                        raise pygame.error

                    pygame.display.set_mode((window_width, window_height), pygame.RESIZABLE)
                    BOARD_WIDTH = BOARD_HEIGHT = window_height * (15/16)
                    PADDING = BOARD_HEIGHT // 30
                    SIDE_PANEL_WIDTH = window_width - BOARD_WIDTH - PADDING * 3
                    SQUARE_SIZE = BOARD_HEIGHT // 8
                    PIECE_SIZE = SQUARE_SIZE*0.9
                    SQ_PIECE_DIFFERENCE = (SQUARE_SIZE - PIECE_SIZE) // 2 
                    
                    board_rect = pygame.Rect(0, 0, BOARD_WIDTH + PADDING, BOARD_HEIGHT + PADDING)
                    side_panel_rect = pygame.Rect(BOARD_WIDTH + PADDING, 0, SIDE_PANEL_WIDTH + PADDING * 2, BOARD_HEIGHT + PADDING)

                    load_images()

                except pygame.error:   # if the user tries to resize to obscure sizes
                    window_width, window_height = SCREEN_WIDTH * 0.8, SCREEN_HEIGHT * 0.8
                    # resetting dimensions to default
                    pygame.display.set_mode((window_width, window_height), pygame.RESIZABLE)
                    BOARD_WIDTH = BOARD_HEIGHT = window_height * (15/16)
                    PADDING = BOARD_HEIGHT // 30
                    SIDE_PANEL_WIDTH = window_width - BOARD_WIDTH - PADDING * 3
                    SQUARE_SIZE = BOARD_HEIGHT // 8
                    PIECE_SIZE = SQUARE_SIZE*0.9
                    SQ_PIECE_DIFFERENCE = (SQUARE_SIZE - PIECE_SIZE) // 2 
                    
                    board_rect = pygame.Rect(0, 0, BOARD_WIDTH + PADDING, BOARD_HEIGHT + PADDING)
                    side_panel_rect = pygame.Rect(BOARD_WIDTH + PADDING, 0, SIDE_PANEL_WIDTH + PADDING * 2, BOARD_HEIGHT + PADDING)

                    load_images()
                    update_display(None, scrolling_size, selected_piece)

                    # error displaying
                    display_message(pygame.display.get_surface(), "Invalid window size! Resetting...", duration=2000)
                    
                finally:
                    update_display(None, scrolling_size, selected_piece)

            elif event.type == pygame.ACTIVEEVENT and event.gain == 1:  # Window restored
                # we need to update display to remove the black screen that appears after minimizing the window
                update_display(None, scrolling_size, selected_piece)

        # coordinates for drawing the text box if the mouse is over the word depth so we can change it by scrolling
        font = pygame.font.Font(None, int(BOARD_HEIGHT * 1/20))
        depth_text_surface = font.render(f"Depth: {engine_depth}", True, TEXT_COLOR)
        icon_center_y = PADDING + engine_icon.get_height() // 2
        text_y = icon_center_y - depth_text_surface.get_height() + PADDING * 1.5
        text_x = BOARD_WIDTH + PADDING * 2 + engine_icon.get_width() + PADDING
        
        if not in_board():   # drawing text boxes over the buttons to show the user what they do
            if window_width - PADDING * 5 <= pygame.mouse.get_pos()[0] <= window_width - PADDING * 2:
                if BOARD_HEIGHT // 2 + PADDING <= pygame.mouse.get_pos()[1] <= BOARD_HEIGHT // 2 + PADDING * 5:
                    draw_text_box("Copy FEN", (window_width - PADDING * 4, BOARD_HEIGHT // 2 + PADDING))
                elif BOARD_HEIGHT // 2 + PADDING * 6 <= pygame.mouse.get_pos()[1] <= BOARD_HEIGHT // 2 + PADDING * 9:
                    draw_text_box("Paste FEN", (window_width - PADDING * 4, BOARD_HEIGHT // 2 + PADDING * 5))
                elif BOARD_HEIGHT // 2 + PADDING * 10 <= pygame.mouse.get_pos()[1] <= BOARD_HEIGHT // 2 + PADDING * 13:
                    draw_text_box("Flip Perspective", (window_width - PADDING * 4, BOARD_HEIGHT // 2 + PADDING * 9))
                elif BOARD_HEIGHT // 2 + PADDING * 14 <= pygame.mouse.get_pos()[1] <= BOARD_HEIGHT // 2 + PADDING * 17:
                    draw_text_box("Toggle Theme", (window_width - PADDING * 4, BOARD_HEIGHT // 2 + PADDING * 13))
                else:
                    update_display(side_panel_rect, scrolling_size, selected_piece)
            # elses needed to remove the box when the mouse is away from the buttons
            elif text_y <= pygame.mouse.get_pos()[1] <= text_y + depth_text_surface.get_height() and text_x <= pygame.mouse.get_pos()[0] <= text_x + depth_text_surface.get_width():
                draw_text_box('scroll to change depth', (text_x, text_y))
            else:
                update_display(side_panel_rect, scrolling_size, selected_piece)
        
        clock.tick(MAX_FPS)
