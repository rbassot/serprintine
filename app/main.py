#modified to run: Python 3.7.6

import json
import sys
import os
import random
import math
from copy import deepcopy
import bottle

#custom game class module
import app.classes as classes

from .api import ping_response, start_response, move_response, end_response


#----------GAME CONSTANTS----------
LOW_HEALTH = 30
MAX_HEALTH = 100
HUNGER_MULTIPLIER = 3

BOARD_EDGE_INFLUENCE = 10
FLEE_EDGES_MULT = 1.3
CLOSE_FOOD_INFLUENCE = 6
CHASE_TAIL_INFLUENCE = 6

FLEE_ENEMIES_INFLUENCE = 7

CLOSE_FOOD_MAX_DIST = 6
MAX_SEARCH_PATH_LEN = 8
HEAD_SEARCH_MULT = 1.5


#A* Search constants
HEURISTIC_WEIGHT = 2.5

#----------GAME FUNCTIONS-----------

'''
initialize(): Function to maintain the JSON request data for usability.
'''
def initialize(request):

    #board maintenance
    width = int(request['board']['width']) 
    height = int(request['board']['height']) 
    food = []

    #create 2D game grid
    grid = []
    for i in range(width):
        grid.append([])
        for j in range(height):
            grid[i].append('empty')

    #add food
    for meal in request['board']['food']:
        x = int(meal['x'])
        y = int(meal['y'])
        food.append((x, y))
        row = y
        col = x
        grid[row][col] = 'food'

    #my snake maintenance
    health = int(request['you']['health'])
    body = []
    head_tile = True
    for part in request['you']['body']:
        x = int(part['x'])
        y = int(part['y'])
        body.append((x, y))
        row = y
        col = x

        if head_tile:
            grid[row][col] = 'mysnakehead'
            head_tile = False
        else:
            grid[row][col] = 'mysnake'

    my_snake = classes.Snake(body, health)

    #enemy snake maintenance
    enemy_snakes = []
    for snake in request['board']['snakes']:

        enemy_health = int(snake['health'])
        enemy_body = []

        for part in snake['body']:
            x = int(part['x'])
            y = int(part['y'])
            enemy_body.append((x, y))
            row = y
            col = x
            grid[row][col] = 'enemysnake'

        enemy_snake = classes.Snake(enemy_body, enemy_health)
        enemy_snakes.append(enemy_snake)
    
    #complete board object
    board = classes.Board(width, height, food, grid, int(request['turn']))

    return my_snake, enemy_snakes, board


'''
Function to calculate the coordinates of the closest -available- food source to the snake's
    head, using Pythagorus. Returns a tuple of the x & y coordinates.
'''
def find_food(snake, board):

    if len(board.food) <= 0:
        return False

    head_x, head_y = snake.get_head()
    closest_food = tuple(board.food[0])
    closest_dist = float(math.sqrt(board.width**2 + board.height**2))

    #loop through food items on the board & calc distance
    for meal in board.food:
        hyp = snake.get_distance_to(tuple(meal))

        if hyp < closest_dist:

            #check before if the food contains only 1 direct entry (3/4 adjacent tiles blocked)
            meal_x, meal_y = meal
            meal_adjacents = [board.get_grid_space(meal_x, meal_y - 1),
                                board.get_grid_space(meal_x, meal_y + 1),
                                board.get_grid_space(meal_x - 1, meal_y),
                                board.get_grid_space(meal_x + 1, meal_y)]
            meal_adjacents = [x for x in meal_adjacents if (x != '' and x != 'enemysnake' and x != 'mysnake')]

            if len(meal_adjacents) < 2:
                continue

            closest_dist = hyp
            closest_food = tuple(meal)
        
    return closest_food, closest_dist


'''
Function to check the current states of a snake in relation to the game board.
    States are strings appended to a snake's .states attribute (list).
'''
def get_states(snake, board, influence):

    #check for snake's head location at board edges - 1st priority influence
    head_x, head_y = snake.get_head()

    #snake is on left or right edge
    if head_x == 0 or head_x == board.width - 1:
        influence.inc_up(BOARD_EDGE_INFLUENCE)
        influence.inc_down(BOARD_EDGE_INFLUENCE)
        snake.add_state('horiz_board_edge')

        if head_x == 0:
            influence.inc_right(BOARD_EDGE_INFLUENCE * FLEE_EDGES_MULT)
            snake.add_state('left_board_edge')

        else:
            influence.inc_left(BOARD_EDGE_INFLUENCE * FLEE_EDGES_MULT)
            snake.add_state('right_board_edge')

    if head_y == 0 or head_y == board.height - 1:
        influence.inc_left(BOARD_EDGE_INFLUENCE)
        influence.inc_right(BOARD_EDGE_INFLUENCE)
        snake.add_state('vert_board_edge')

        if head_y == 0:
            influence.inc_down(BOARD_EDGE_INFLUENCE * FLEE_EDGES_MULT)
            snake.add_state('top_board_edge')

        else:
            influence.inc_up(BOARD_EDGE_INFLUENCE * FLEE_EDGES_MULT)
            snake.add_state('bottom_board_edge')

    return


'''
Function to check all the valid moves (directly adjacent) from a selected position on the board.
    Moving into a wall/snake/own body are considered invalid. Also adjusts influence to drive the
    snake away from an edge of the board. Moves take into account if snake tails will have moved
    away by the time that space is reached.
'''
def check_valid_moves(snake, position, board, enemies, influence):

    #create a new temp Board/enemies/self for future tail prediction - maintains the original Board object
    temp_board = deepcopy(board)
    temp_enemies = []
    for enemy in enemies:
        temp_enemy = deepcopy(enemy)
        temp_enemies.append(temp_enemy)

    temp_snake = deepcopy(snake)

    #adjust board for next turn
    adjust_future_tails(temp_board, temp_snake, temp_enemies)

    #---------- 1 ----------
    #check board edges for valid moves, and drive the snake away from the edge
    head_x, head_y = position

    if 'horiz_board_edge' in temp_snake.states and 'vert_board_edge' not in temp_snake.states:
        if 'left_board_edge' in temp_snake.states:
            possible_moves = ['up', 'down', 'right']
            #influence.inc_right(BOARD_EDGE_INFLUENCE)

        elif 'right_board_edge' in temp_snake.states:
            possible_moves = ['up', 'down', 'left']
            #influence.inc_left(BOARD_EDGE_INFLUENCE)

    elif 'vert_board_edge' in temp_snake.states and 'horiz_board_edge' not in temp_snake.states:

        if 'top_board_edge' in temp_snake.states:
            possible_moves = ['down', 'left', 'right']
            #influence.inc_down(BOARD_EDGE_INFLUENCE)

        elif 'bottom_board_edge' in temp_snake.states:
            possible_moves = ['up', 'left', 'right']
            #influence.inc_up(BOARD_EDGE_INFLUENCE)

    elif 'horiz_board_edge' in temp_snake.states and 'vert_board_edge' in temp_snake.states:

        #top left corner
        if head_x == 0 and head_y == 0:
            possible_moves = ['down', 'right']
        #top right corner
        elif head_x == temp_board.width - 1 and head_y == 0:
            possible_moves = ['down', 'left']
        #bottom left corner
        elif head_x == 0 and head_y == temp_board.height - 1:
            possible_moves = ['up', 'right']
        #bottom right corner
        elif head_x == temp_board.width - 1 and head_y == temp_board.height - 1:
            possible_moves = ['up', 'left']

    else:
        possible_moves = ['up', 'down', 'left', 'right']


    #---------- 2 ----------
    #check board components (enemy/own body) for valid moves
    tile_x, tile_y = position

    i = 0
    while i < len(possible_moves):

        spacetaker = ''
        if possible_moves[i] == 'up':
            spacetaker = temp_board.get_grid_space(tile_x, tile_y - 1)

        elif possible_moves[i] == 'down':
            spacetaker = temp_board.get_grid_space(tile_x, tile_y + 1)

        elif possible_moves[i] == 'left':
            spacetaker = temp_board.get_grid_space(tile_x - 1, tile_y)

        elif possible_moves[i] == 'right':
            spacetaker = temp_board.get_grid_space(tile_x + 1, tile_y)

        #not a valid tile
        if spacetaker == 'mysnake' or spacetaker == 'mysnakehead' or spacetaker == 'enemysnake':
            possible_moves.pop(i)
            i -= 1
        i += 1
        
    return possible_moves


'''
Function to perform an A* search for a desired destination point (own tail, closest food ...).
    Returns the complete shortest path (list of x & y coordinate tuples) to the target, excluding
    the start position. Moves take into account if snake tails will have moved away by the time
    that space is reached.

Algorithm:
    F = Total cost of the node; F = G + H
    G = Distance (in spaces/moves needed) between current node & end node
    H = Heuristic -> Estimated distance (Pythagorus, under-est.) between current node & end node

Time complexity: O(b^d), with 'd'= shortest path to target, 'b'= number of successors per state (4)
'''
def a_star_search(board, snake, enemies, start, target):

    #create lists to hold search nodes
    open_set = []
    closed_set = []

    #create a new temp board/enemies/self for future tail prediction - maintains the original objects
    temp_board = deepcopy(board)
    temp_enemies = []
    for enemy in enemies:
        temp_enemy = deepcopy(enemy)
        temp_enemies.append(temp_enemy)

    temp_snake = deepcopy(snake)
    bound = len(temp_board.grid) - 1
    
    #check for valid start position first
    start_x, start_y = start
    if start != temp_snake.get_head():
        if ((start_x < 0 or start_x > temp_board.width - 1 or start_y < 0 or start_y > temp_board.width - 1)
                or (temp_board.get_grid_space(start_x, start_y) != 'empty' and temp_board.get_grid_space(start_x, start_y) != 'food')):
            print('Invalid starting position!')
            return None

    #create start, end nodes & push start node onto the open set
    start_node = classes.SearchNode(None, start)
    start_node.g = 1
    end_node = classes.SearchNode(None, target)
    open_set.append(start_node)

    #search until open set of nodes is empty
    while open_set:

        #find current node = node with lowest f value
        current_node = open_set[0]
        current_index = 0

        for i, open_node in enumerate(open_set):

            if open_node.f <= current_node.f:
                current_node = open_node
                current_index = i

        closed_set.append(open_set.pop(i))

        #check if search target was found - end of search
        if current_node == end_node:
            
            #return the path to the target in order (head to target, inclusive)
            final_path = []
            
            while current_node != start_node:
                final_path.insert(0, current_node.position)
                current_node = current_node.parent

            print(final_path)
            return final_path


        #-----TILES-----
        #adjust board for every turn
        adjust_future_tails(temp_board, temp_snake, temp_enemies)

        #get (valid) adjacent tile coordinates to create children nodes
        #*** assumes board is square here ***
        adjacent_tiles = current_node.get_adjacent_spaces()
        adjacent_tiles = [tile for tile in adjacent_tiles
                            if not ((tile[0] < 0 or tile[0] > bound) or (tile[1] < 0 or tile[1] > bound))]

        #check tiles for node creation
        children = []
        for tile in adjacent_tiles:
            
            #skip tile if it's taken
            if temp_board.get_grid_space(tile[0], tile[1]) != 'empty' and temp_board.get_grid_space(tile[0], tile[1]) != 'food':
                continue

            #create new child node and append
            child = classes.SearchNode(current_node, tile)
            children.append(child)

        #-----CHILDREN-----
        #check children for open nodes with lower f values than child 
        for child_node in children:

            distant_child = False
            closed_child = False

            #check if child is already in closed set
            for closed_node in closed_set:

                if child_node == closed_node:
                    closed_child = True
                    break

            if closed_child:
                continue

            #valid child - create f, g, h
            child_node.g = current_node.g + 1
            child_node.h = HEURISTIC_WEIGHT * (math.sqrt(  (child_node.position[0] - target[0])**2 + (child_node.position[1] - target[1])**2  ))
            child_node.f = float(child_node.g + child_node.h)

            #check if child is already in open set; skip if it's g-val is greater
            for open_node in open_set:

                if child_node == open_node and child_node.g > open_node.g:
                    distant_child = True
                    break

            if distant_child:
                continue

            #add child to open list
            open_set.append(child_node)


    #if no more searchable tiles & no target found, return None
    print('No path found!')
    return None


'''
Function to check for enemy snakes 2 spaces away that could collide and cause death. Basically a further
    safety check 2 tiles in each direction. 'Move' parameter is the direct move that will be checked.

    Returns True if a larger enemy snake head is adjacent, else returns False.
'''
def incoming_enemy_snake(board, snake, move, enemies, influence):

    #create a new temp board/enemies/self for future tail prediction - maintains the original Board object
    temp_board = deepcopy(board)
    temp_enemies = []
    for enemy in enemies:
        temp_enemy = deepcopy(enemy)
        temp_enemies.append(temp_enemy)

    temp_snake = deepcopy(snake)

    #get direction that must not be checked, and analysis tile position
    x, y = temp_snake.get_head()
    if move == 'up':
        no_check = 'down'
        tile_analyzed = (x, y - 1)

    elif move == 'down':
        no_check = 'up'
        tile_analyzed = (x, y + 1)

    elif move == 'left':
        no_check = 'right'
        tile_analyzed = (x - 1, y)

    elif move == 'right':
        no_check = 'left'
        tile_analyzed = (x + 1, y)

    #adjust tails for next direct move -- 1 space away from head here
    adjust_future_tails(temp_board, temp_snake, temp_enemies)

    #assure analysis tile is on the grid & a valid open space
    tile_x, tile_y = tile_analyzed
    if ((tile_x < 0 or tile_x > temp_board.width - 1 or tile_y < 0 or tile_y > temp_board.width - 1)
            or (temp_board.get_grid_space(tile_x, tile_y) != 'empty' and temp_board.get_grid_space(tile_x, tile_y) != 'food')):
        return True

    #check adjacents to the analysis tile
    adjacent_dirs = ['up', 'down', 'left', 'right']
    adjacent_dirs.remove(no_check)

    #adjust tails for next move check -- 2 spaces away from head here
    adjust_future_tails(temp_board, temp_snake, temp_enemies)

    for adjacent in adjacent_dirs:

        spacetaker = ''
        enemy_found = False

        #check for which adjacency
        if adjacent == 'up':
            spacetaker = temp_board.get_grid_space(tile_x, tile_y - 1)
            adjacent_check = (tile_x, tile_y - 1)
        elif adjacent == 'down':
            spacetaker = temp_board.get_grid_space(tile_x, tile_y + 1)
            adjacent_check = (tile_x, tile_y + 1)
        elif adjacent == 'left':
            spacetaker = temp_board.get_grid_space(tile_x - 1, tile_y)
            adjacent_check = (tile_x - 1, tile_y)
        elif adjacent == 'right':
            spacetaker = temp_board.get_grid_space(tile_x + 1, tile_y)
            adjacent_check = (tile_x + 1, tile_y)

        #CHANGE THIS?? WHY IS MY OWN SNAKE HERE
        if spacetaker == 'enemysnake': #or spacetaker == 'mysnake' or spacetaker == 'mysnakehead':
                
            #find adjacent snake and check its length
            for enemy in temp_enemies:
                        
                if enemy.get_head() == adjacent_check:
                    enemy_length = enemy.get_length()
                    enemy_found = True
                    break

                #if not a head collision, check for enemy body and reduce influence for that immediate move
                for part in enemy.get_body():

                    if part == adjacent_check:
                        if move == 'up':
                            influence.inc_up(-FLEE_ENEMIES_INFLUENCE)
                        elif move == 'down':
                            influence.inc_down(-FLEE_ENEMIES_INFLUENCE)
                        elif move == 'left':
                            influence.inc_left(-FLEE_ENEMIES_INFLUENCE)
                        elif move == 'right':
                            influence.inc_right(-FLEE_ENEMIES_INFLUENCE)

        if enemy_found:

            #compare lengths
            if temp_snake.get_length() <= enemy.get_length(): 
                return True

    #if loop completes without finding larger snake, move is safe
    return False


'''
Function to adjust the tails of all snakes on the board for the next turn.
    Allows the discovery of future open squares that open once a turn passes.
'''
def adjust_future_tails(board, snake, enemies):

    #replace all tails on the board with 'empty' if the snake hasn't just eaten, and adjust all snakes
    for enemy in enemies:

        if not enemy.get_tail():
            continue

        if enemy.get_health() == MAX_HEALTH:
            continue
    
        x, y = enemy.get_tail()
        enemy.body.pop()
        board.set_grid_space(x, y, 'empty')

    #replace my own tail, if I haven't just eaten
    if not snake.get_tail() or snake.get_health() == MAX_HEALTH:
        return

    x, y = snake.get_tail()
    snake.body.pop()
    board.set_grid_space(x, y, 'empty')

    return


'''Function to compare direct snake head distances to a target object, using Pythagorus.
        Returns False if any one enemy is closer than the passed snake, otherwise, returns True.
'''
def is_closest_snake(snake, target, dist, enemies):

    snake_dist = dist
    for enemy in enemies:

        #check if enemy head exists
        if enemy.get_distance_to(target) == None:
            continue

        if enemy.get_distance_to(target) < snake_dist:
            return False

    return True


@bottle.route('/')
def index():
    return "<h1>Serprintine*</h1>"


@bottle.route('/static/<path:path>')
def static(path):
    """
    Given a path, return the static file located relative
    to the static folder.

    This can be used to return the snake head URL in an API response.
    """
    return bottle.static_file(path, root='static/')


@bottle.post('/ping')
def ping():
    """
    A keep-alive endpoint used to prevent cloud application platforms,
    such as Heroku, from sleeping the application instance.
    """
    return ping_response()


@bottle.post('/start')
def start():
    data = bottle.request.json

    """
    TODO: If you intend to have a stateful snake AI,
            initialize your snake state here using the
            request's data if necessary.
    """
    #print(json.dumps(data))

    return {
        "color": "#00b3b3",
        "headType": "tongue",
        "tailType": "curled",
    }



'''
--------------------MOVE REQUEST--------------------
{
  "game": {
    "id": "game-id-string"
  },

  "turn": 4,

  "board": {
    "height": 15,
    "width": 15,
    "food": [
      {
        "x": 1,
        "y": 3
      }
    ],

    "snakes": [
      {
        "id": "snake-id-string",
        "name": "Sneky Snek",
        "health": 90,
        "body": [
          {
            "x": 1,
            "y": 3
          }
        ]
      }
    ]
  },

  "you": {
    "id": "snake-id-string",
    "name": "Sneky Snek",
    "health": 90,
    "body": [
      {
        "x": 1,
        "y": 3
      }
    ]
  }
}

--------------------MOVE RESPONSE--------------------
{
  "move": "right",
  "shout": "It's snack time!"
}
'''

@bottle.post('/move')
def move():
    #data = bottle.request.json
    data = json.load(bottle.request.body)

    #JSON object maintenance
    my_snake, enemy_snakes, board = initialize(data)

    #----------CALCULATING BEST MOVE----------
    '''
    STRATEGY:
        - To calculate the number of move influences my snake has based on the situation of the game.
        - Total the influence counts after every check and finally select a direction to move in.
    '''
    influence = classes.Influence()

    #get snake states before calculation
    get_states(my_snake, board, influence)

    #check snake's previous move/next body part - 2nd priority influence
    invalid_dir = my_snake.get_invalid_dir()

    #----------SEARCH MAINTENANCE----------
    #Strategy: A* implemented to search from head, then from 3 adjacent (potentially) valid tiles.
    #Search performed from the head is weighted the most with a multiplier.
    head_x, head_y = my_snake.get_head()

    #setup search tiles
    search_tiles = [(head_x, head_y), (head_x, head_y - 1), (head_x, head_y + 1), (head_x - 1, head_y), (head_x + 1, head_y)]
    if invalid_dir == 'up':
        search_tiles.pop(1)
    elif invalid_dir == 'down':
        search_tiles.pop(2)
    elif invalid_dir == 'left':
        search_tiles.pop(3)
    elif invalid_dir == 'right':
        search_tiles.pop(4)

    head_search = True
    for search_tile in search_tiles:

        search_moves = []
        try:
            closest_food, closest_dist = find_food(my_snake, board)
        except TypeError:
            closest_food = False
            closest_dist = None

        if (((closest_food and closest_dist <= CLOSE_FOOD_MAX_DIST) or
                (closest_food and my_snake.get_health() <= LOW_HEALTH and closest_dist <= CLOSE_FOOD_MAX_DIST * HUNGER_MULTIPLIER)) and
                is_closest_snake(my_snake, closest_food, closest_dist, enemy_snakes)):

            food_path = a_star_search(board, my_snake, enemy_snakes, search_tile, closest_food)

            if ((food_path and len(food_path) <= MAX_SEARCH_PATH_LEN) or
                    (food_path and my_snake.get_health() <= LOW_HEALTH and len(food_path) <= MAX_SEARCH_PATH_LEN * HUNGER_MULTIPLIER)):

                if head_search:
                    head_search = False
                    search_move = my_snake.dir_towards(food_path[0])

                    if search_move == 'up':
                        influence.inc_up(CLOSE_FOOD_INFLUENCE * HEAD_SEARCH_MULT)
                    elif search_move == 'down':
                        influence.inc_down(CLOSE_FOOD_INFLUENCE * HEAD_SEARCH_MULT)
                    elif search_move == 'left':
                        influence.inc_left(CLOSE_FOOD_INFLUENCE * HEAD_SEARCH_MULT)
                    elif search_move == 'right':
                        influence.inc_right(CLOSE_FOOD_INFLUENCE * HEAD_SEARCH_MULT)

                else:
                    search_moves = my_snake.dirs_towards(food_path[0])

                    if 'up' in search_moves:
                        influence.inc_up(CLOSE_FOOD_INFLUENCE)
                    if 'down' in search_moves:
                        influence.inc_down(CLOSE_FOOD_INFLUENCE)
                    if 'left' in search_moves:
                        influence.inc_left(CLOSE_FOOD_INFLUENCE)
                    if 'right' in search_moves:
                        influence.inc_right(CLOSE_FOOD_INFLUENCE)

        else:
            chase_tail = a_star_search(board, my_snake, enemy_snakes, search_tile, my_snake.get_tail())

            if chase_tail:

                if head_search:
                    head_search = False
                    search_move = my_snake.dir_towards(chase_tail[0])

                    if search_move == 'up':
                        influence.inc_up(CHASE_TAIL_INFLUENCE * HEAD_SEARCH_MULT)
                    elif search_move == 'down':
                        influence.inc_down(CHASE_TAIL_INFLUENCE * HEAD_SEARCH_MULT)
                    elif search_move == 'left':
                        influence.inc_left(CHASE_TAIL_INFLUENCE * HEAD_SEARCH_MULT)
                    elif search_move == 'right':
                        influence.inc_right(CHASE_TAIL_INFLUENCE * HEAD_SEARCH_MULT)

                else:
                    search_moves = my_snake.dirs_towards(chase_tail[0])

                    if 'up' in search_moves:
                        influence.inc_up(CHASE_TAIL_INFLUENCE)
                    if 'down' in search_moves:
                        influence.inc_down(CHASE_TAIL_INFLUENCE)
                    if 'left' in search_moves:
                        influence.inc_left(CHASE_TAIL_INFLUENCE)
                    if 'right' in search_moves:
                        influence.inc_right(CHASE_TAIL_INFLUENCE)

    #----------MOVE DECISION-MAKING----------
    #priority influence 1
    #ADDED - drive snake away from edge, towards middle
    possible_moves = check_valid_moves(my_snake, my_snake.get_head(), board, enemy_snakes, influence)

    #priority influence 2 - remove invalid direction
    if invalid_dir:
        try:
            possible_moves.remove(invalid_dir)
        except ValueError:
            pass

    #check further for any larger, incoming snakes that would result in a death collision
    if len(possible_moves) > 1:
        possible_moves = [move for move in possible_moves if not incoming_enemy_snake(board, my_snake, move, enemy_snakes, influence)]
    
    #secondary influences
    move_influences = []
    if 'up' in possible_moves:
        move_influences.append(influence.move_up)
    if 'down' in possible_moves:
        move_influences.append(influence.move_down)
    if 'left' in possible_moves:
        move_influences.append(influence.move_left)
    if 'right' in possible_moves:
        move_influences.append(influence.move_right)

    move_pairs = dict(zip(possible_moves, move_influences))
    move = max(move_pairs, key=move_pairs.get)
    
    shout = "It's snack time!"
    print(move_pairs)
    print('Selected move: ' + move)
    return move_response(move, shout)


@bottle.post('/end')
def end():
    data = bottle.request.json

    """
    TODO: If your snake AI was stateful,
        clean up any stateful objects here.
    """
    print(json.dumps(data))

    return end_response()



#Expose WSGI app (so gunicorn can find it)
application = bottle.default_app()

def main():
    bottle.run(
        application,
        host=os.getenv('IP', '0.0.0.0'),
        port=os.getenv('PORT', '8080'),
        #debug=os.getenv('DEBUG', True)
    )

if __name__ == '__main__':
    main()