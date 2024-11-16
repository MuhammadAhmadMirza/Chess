'''a convenient tool to converts coordinates between any gui and engine'''

from typing import Union

# in this module we could have imported the screen size configurations however they might change 
# due to resizing of the window thus it is added to the parameters to be passed to the function for dynamic adjustment
def coordinates_converter(coordinates: Union[tuple, list], pov: bool, SQUARE_SIZE: int, PADDING: int) -> tuple:
    '''
    In pygame, the grid starts from the top-left corner, so we need to convert these coordinates into typical array indexing coordinates for Python.
    This function also adjusts the calculations for the black perspective.

    Args:
        coordinates (tuple[float] or list[float]): A list of x, y coordinates of the mouse on the board
        pov (bool): The board perspective (True for white, False for black)

    Returns:
        tuple: The coordinates converted to index coordinates
    '''
    if pov:
        # Ensure the result is within the range [0, 7]
        x = round(max(0, min(7, (coordinates[0] - PADDING) // SQUARE_SIZE)))
        y = round(max(0, min(7, (coordinates[1] - PADDING) // SQUARE_SIZE)))
    else:
        # Ensure the result is within the range [0, 7]
        x = round(max(0, min(7, 7 - (coordinates[0] - PADDING) // SQUARE_SIZE)))
        y = round(max(0, min(7, 7 - (coordinates[1] - PADDING) // SQUARE_SIZE)))

    return (y, x)
