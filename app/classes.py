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

        get_height(self):
            Returns the height (int) of the game board.

        get_width(self):
            Returns the width (int) of the game board.

        get_food(self):
            Returns the list containing all food coordinates on the board.

        get_grid_space(self, x, y):
            Returns the object type (string) occupying the tile at the x & y coordinates of the grid.

        get_grid(self):
            Returns the grid (2D list) describing the locations

        set_grid_space(self, x, y, value):
            Sets the value (string) that will occupy the tile at the x & y coordinates of the grid.

        is_dead_end(self, x, y):
            Returns True if the tile at the passed coordinates is not occupied and has either:
            only one approachable entry (ie. 3 of 4 adjacent tiles are blocked/occupied), or no entries.
            **An adjacent tile is not blocked if my snake's head is the occupant**

        find_open_tiles(self, x, y):
            Returns a list of all the open unoccupied tiles that are adjacent to the passed coordinates.
            Will return an empty list if there are none.

        fill_path(self, x, y):
            Iteratively fills the entire open path on the grid by starting from a specified dead end.

        remove_fills(self):
            Removes all fill markers in the board's grid attribute, resetting the lists.
    '''
    
    def __init__(self, width, height, food, grid, turn):
        self.width = width
        self.height = height
        self.food = food
        self.grid = grid
        self.turn = turn

    def get_height(self):
        return self.height

    def get_width(self):
        return self.width

    def get_food(self):
        return self.food

    def get_grid(self):
        return self.grid

    def get_turn(self):
        return self.turn

    def get_grid_space(self, x, y):
        row = y
        col = x
        if x < 0 or x > self.width - 1 or y < 0 or y > self.height - 1:
            return 'invalid'

        grid_space = self.grid[row][col]
        return grid_space

    def set_grid_space(self, x, y, value):
        row = y
        col = x
        if x < 0 or x > self.width - 1 or y < 0 or y > self.height - 1:
            return 'invalid'

        self.grid[row][col] = value
        return

    def get_adjacent_spaces(self, x, y):
        return [(x, y - 1), (x, y + 1), (x - 1, y), (x + 1, y)]

    def is_dead_end(self, x, y):
        if self.get_grid_space(x, y) not in ('empty', 'food'):
            return False

        blocked_count = 0
        for adj_x, adj_y in self.get_adjacent_spaces(x, y):
            if self.get_grid_space(adj_x, adj_y) not in ('empty', 'food', 'mysnakehead'):
                blocked_count += 1

        if blocked_count >= 3:
            return True
        else:
            return False

    def find_open_tiles(self, x, y):
        adjacencies = self.get_adjacent_spaces(x, y)
        open_tiles = []
        for tile_x, tile_y in adjacencies:
            if self.get_grid_space(tile_x, tile_y) in ('empty', 'food'):
                open_tiles.append((tile_x, tile_y))

        return open_tiles


    def fill_path(self, x, y):
        while self.is_dead_end(x, y):
            open_adjacents = self.find_open_tiles(x, y)
            if len(open_adjacents) <= 1:
                self.set_grid_space(x, y, 'filled')
                try:
                    next_x, next_y = open_adjacents[0]
                    x, y = next_x, next_y
                except IndexError:
                    continue
                
    def remove_fills(self):
        for row in range(len(self.grid)):
            for col in range(len(self.grid[row])):
                x = col
                y = row
                if self.get_grid_space(x, y) == 'filled':
                    if (x, y) in self.food:
                        self.set_grid_space(x, y, 'food')
                    else:
                        self.set_grid_space(x, y, 'empty')


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
            Returns the head of the snake, or None if non-existent.

        get_tail(self):
            Returns the tail of the snake, or None if non-existent.

        get_body(self):
            Returns the body (list of tuples) of the snake.

        get_health(self):
            Returns the health of the snake.

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
            Returns the unique valid direction (string) required to approach the passed target. Used for 
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
        try:
            head = tuple(self.body[0])
        except IndexError:
            return None
        return head

    def get_tail(self):
        try:
            tail = tuple(self.body[len(self.body) - 1])
        except IndexError:
            return None
        return tail

    def get_body(self):
        return self.body

    def get_health(self):
        return self.health

    def get_length(self):
        return len(self.body)

    def get_invalid_dir(self):
        try:
            x, y = self.get_head()
            body_x, body_y = self.body[1]

        except IndexError:
            return None

        if x == body_x and y < body_y:
            return "up"
        
        elif x == body_x and y > body_y:
            return "down"

        elif y == body_y and x > body_x:
            return "left"

        return "right"

    def get_distance_to(self, target):
        try:
            x, y = self.get_head()
            target_x, target_y = target
            return float(math.sqrt(  (x - target_x)**2 + (y - target_y)**2  ))
        except IndexError:
            return None

    def dir_towards(self, target):
        target_x, target_y = target
        x, y = self.get_head()
        if y < target_y:
            return "up"
        if y > target_y:
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
        if y < target_y:
            directions.append("up")
        if y > target_y:
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
        move_up - total summation (float) of influences towards moving up (+y)

        move_down - total summation (float) of influences towards moving down (-y)

        move_left - total summation (float) of influences towards moving left (-x)

        move_right - total summation (float) of influences towards moving right (+x)

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
        self.move_up = 0.0
        self.move_down = 0.0
        self.move_left = 0.0
        self.move_right = 0.0

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
        return [(x, y + 1), (x, y - 1), (x - 1, y), (x + 1, y)]

    def get_parent(self):
        return self.parent