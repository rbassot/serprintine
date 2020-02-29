import math

class Board(object):
    '''
    CLASS DESCRIPTION:
        An object class to maintain the attributes of the Battlesnake game board.

    ----------
    ATTRIBUTES:
        width - width of the game board.
        height - height of the game board.
        food - list of x & y tuples that describe the coordinates of all food on the board.
        grid - a 2D list of values describing the objects on the board at all coordinates.
    
    ----------
    METHODS:
        __init__(self, width, height, food):
            Creates an instance of a Battlesnake game board.
    '''
    
    def __init__(self, width, height, food, grid):
        self.width = width
        self.height = height
        self.food = food
        self.grid = grid


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
            Returns the head of the snake, even if it doesn't have a head attribute.

        get_length(self):
            Returns the total length of the snake.

        get_invalid_dir(self):
            Returns the direction, from the head, where the snake cannot travel, determined by
            the location of its next body part. This also decribes the
            direction that the snake selected on the previous turn.

        get_distance_to(self, target):
            Returns the direct distance (float) to the passed target object by using Pythagorus.
            Does not worry about direction or order of moves. Target object is a set of x & y coordinates.

        dirs_towards(self, target):
            Returns all valid directions (list of strings) towards approaching the passed target.
            Target object is a set of x & y coordinates.
        
    '''
    def __init__(self, body, health):
        self.body = body
        self.health = health

    def get_head(self):
        return tuple(self.body[0])

    def get_length(self):
        return len(self.body)

    def get_invalid_dir(self):
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

    def get_distance_to(self, target):
        x, y = self.get_head()
        target_x, target_y = target
        return float(math.sqrt(  abs((x - target_x)^2) + abs((y - target_y)^2)  ))

    def dirs_towards(self, target):
        target_x, target_y = target
        x, y = self.get_head()
        directions = []
        if y > target_y:
            directions.append("up")
        if y < target_y:
            directions.append("down")
        if x > target_x:
            directions.append("left")
        if x < target_x:
            directions.append("right")
        return directions
        


class Influence(object):
    '''
    CLASS DESCRIPTION:
        An object class to maintain the calculation of influences to determine game movement.

    ----------
    ATTRIBUTES:
        move_up - total of influences towards moving up (-y)

        move_down - total of influences towards moving down (+y)

        move_left - total of influences towards moving left (-x)

        move_right - total of influences towards moving right (+x)

    ----------
    METHODS:
        __init__(self):
            Creates an instance of an influence tracker.

        inc_up(self, multiple):
            Increments the influence towards moving up by the passed amount.

        inc_down(self, multiple):
            Increments the influence towards moving down by the passed amount.

        inc_left(self, multiple):
            Increments the influence towards moving left by the passed amount.

        inc_right(self, multiple):
            Increments the influence towards moving right by the passed amount.
    '''
    def __init__(self):
        self.move_up = 0
        self.move_down = 0
        self.move_left = 0
        self.move_right = 0

    def inc_up(self, multiple):
        self.move_up += 1 * multiple

    def inc_down(self, multiple):
        self.move_down += 1 * multiple

    def inc_left(self, multiple):
        self.move_left += 1 * multiple

    def inc_right(self, multiple):
        self.move_right += 1 * multiple