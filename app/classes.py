
class Board(Object):
    '''
    CLASS DESCRIPTION:
        An object class to maintain the attributes of the Battlesnake game board.

    ----------
    ATTRIBUTES:
        width - width of the game board.
        height - height of the game board.
        food - list of x & y tuples that describe the coordinates of all food on the board.
    
    ----------
    METHODS:
        __init__(self, width, height, food):
            Creates an instance of a Battlesnake game board.
    '''
    
    def __init__(self, width, height, food):
        self.width = width
        self.height = height
        self.food = food



class Snake(Object):
    '''
    CLASS DESCRIPTION:
        An object class for instances of snakes.

    ----------
    ATTRIBUTES:
        body - list of x & y tuples that form the body of a snake, with the head being first tuple
            (x, y) - tuple holding the x & y coordinates of a portion of the snake
            
        health - integer representing the remaining health of the snake

    ----------
    METHODS:
        __init__(self, body, health):
            Creates an instance of an existing snake in the arena.
        
    '''
    def __init__(self, body, health):
        self.body = body
        self.health = health


