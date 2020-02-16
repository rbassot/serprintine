
class Board(object):
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



class Snake(object):
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

        get_head(self):
            Returns the head of the snake even if it doesn't have a head attribute.

        get_length(self):
            Returns the total length of the snake.

        get_body_location(self):
            Returns the direction, from the head, where the snake's next body part exists, and
            therefore the direction the snake certainly shouldn't go next. This also decribes the
            direction that the snake selected on the previous turn.
        
    '''
    def __init__(self, body, health):
        self.body = body
        self.health = health

    def get_head(self):
        return self.body[0]

    def get_length(self):
        return len(self.body)

    def get_body_location(self):
        try:
            x, y = self.body[0]
            body_x, body_y = self.body[1]

        except IndexError:
            return ""

        if x == body_x and y < body_y:
            return "down"
        
        elif x == body_x and y > body_y:
            return "up"

        elif y == body_y and x > body_x:
            return "left"

        return "right"


