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

        get_grid_space(self, x, y):
            Returns the value (string) occupying the tile at the x & y coordinates of the grid.

        set_grid_space(self, x, y, value):
            Sets the value (string) that will occupy the tile at the x & y coordinates of the grid.
    '''
    
    def __init__(self, width, height, food, grid, turn):
        self.width = width
        self.height = height
        self.food = food
        self.grid = grid
        self.turn = turn

    def get_grid_space(self, x, y):
        try:
            row = y
            col = x
            grid_space = self.grid[row][col]

        except IndexError:
            return ''
        return grid_space

    def set_grid_space(self, x, y, value):
        try:
            row = y
            col = x
            self.grid[row][col] = value

        except IndexError or ValueError:
            return
        return


class Snake(object):
    '''
    CLASS DESCRIPTION:
        An object class for instances of snakes.

    ----------
    ATTRIBUTES:
        body - list of x & y tuples that form the body of a snake, with the head being first tuple
            (x, y) - tuple holding the x & y coordinates of a portion of the snake
            
        health - integer representing the remaining health of the snake

        states - list of strings containing the important states of the snake on a current move

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

        dir_towards(self, target):
            Returns the lone valid direction (strings) that approaches the passed target. Used for 
            A*, where an adjacent tile on the shortest path is passed to this function.
            Target object is a set of x & y coordinates.

        dirs_towards(self, target):
            Returns all valid directions (list of strings) that approach the passed target.
            Target object is a set of x & y coordinates.

        add_state(self, state):
            Appends a state object (string) to the states list attribute.
        
    '''
    def __init__(self, body, health):
        self.body = body
        self.health = health

        self.states = []

    def get_head(self):
        return tuple(self.body[0])

    def get_tail(self):
        return tuple(self.body[len(self.body) - 1])

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
        return float(math.sqrt(  (x - target_x)**2 + (y - target_y)**2  ))

    def dir_towards(self, target):
        target_x, target_y = target
        x, y = self.get_head()
        if y > target_y:
            return "up"
        if y < target_y:
            return "down"
        if x > target_x:
            return "left"
        if x < target_x:
            return "right"
        return None

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

    def add_state(self, state):
        self.states.append(state)
        


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
        self.move_up += (1 * multiple)

    def inc_down(self, multiple):
        self.move_down += (1 * multiple)

    def inc_left(self, multiple):
        self.move_left += (1 * multiple)

    def inc_right(self, multiple):
        self.move_right += (1 * multiple)


class SearchNode():
    '''
    CLASS DESCRIPTION:
        A node class used to perform an A* search algorithm for pathfinding.

    ----------
    ATTRIBUTES:

        parent - the node's parent node. Helps determine final path.

        position - the node's x & y coordinates (tuple)

        f - total cost of the node; F = G + H

        g - distance (in spaces/moves needed) between current node & end node

        h - heuristic -> Estimated distance (hypotenuse) between current node & end node

    ----------
    METHODS:
        __init__(self, parent=None, position=None):
            Creates an instance of a SearchNode.

        __eq__(self, other):
            Modifies object comparison - two objects are equal if their positions are the same.

        get_adjacent_spaces(self):
            Returns a list of the x & y coordinates (tuple) of the 4 spaces adjacent to the node.
            **This disregards if the adjacent spaces are off the board/out of bounds/occupied spaces.

        get_parent(self):
            Returns the node's parent node.
    '''

    def __init__(self, parent=None, position=None):
        self.parent = parent
        self.position = tuple(position)
        self.f = 0
        self.g = 0
        self.h = 0

    def __eq__(self, other):
        return self.position == other.position

    def get_adjacent_spaces(self):
        x, y = self.position
        return [(x, y - 1), (x, y + 1), (x - 1, y), (x + 1, y)]

    def get_parent(self):
        return self.parent