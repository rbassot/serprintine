#modified to run: Python 3.7.6

import json
import sys
import os
import random
import math
import bottle

#custom game class module
import app.classes as classes

from .api import ping_response, start_response, move_response, end_response


#----------GAME CONSTANTS----------
LOW_HEALTH = 30

BOARD_EDGE_INFLUENCE = 10
CLOSE_FOOD_INFLUENCE = 5

CLOSE_FOOD_MAX_DIST = 10


#A* Search constants
HEURISTIC_WEIGHT = 3

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
    for part in request['you']['body']:
        x = int(part['x'])
        y = int(part['y'])
        body.append((x, y))
        row = y
        col = x
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
find_food: Calculates the coordinates of the closest food source to the snake's
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
            closest_dist = float(hyp)
            closest_food = tuple(meal)
        
    return meal, closest_dist


'''
Function to check the possible states of a snake in relation to the game board.
    States are strings appended to a snake's .states[] attribute.
'''
def get_states(snake, board, influence):

    #check for snake's head location at board edges - 1st priority influence
    head_x, head_y = snake.get_head()

    if head_x == 0 or head_x == board.width - 1:
        influence.inc_up(BOARD_EDGE_INFLUENCE)
        influence.inc_down(BOARD_EDGE_INFLUENCE)
        snake.add_state('horiz_board_edge')

        if head_x == 0:
            snake.add_state('left_board_edge')

        else:
            snake.add_state('right_board_edge')

    if head_y == 0 or head_y == board.height - 1:
        influence.inc_left(BOARD_EDGE_INFLUENCE)
        influence.inc_right(BOARD_EDGE_INFLUENCE)
        snake.add_state('vert_board_edge')

        if head_y == 0:
            snake.add_state('top_board_edge')

        else:
            snake.add_state('bottom_board_edge')

    return


'''
Function to check all the valid moves (directly adjacent) from a selected position on the board.
    Moving into a wall/snake/own body are considered invalid.
'''
def check_valid_moves(snake, position, board, influence):

    #---------- 1 ----------
    #check board edges for valid moves
    head_x, head_y = position

    if 'horiz_board_edge' in snake.states and 'vert_board_edge' not in snake.states:
        if 'left_board_edge' in snake.states:
            possible_moves = ['up', 'down', 'right']

            if board.turn >= 3:
                influence.inc_right(BOARD_EDGE_INFLUENCE + 1)

        elif 'right_board_edge' in snake.states:
            possible_moves = ['up', 'down', 'left']

            if board.turn >= 3:
                influence.inc_left(BOARD_EDGE_INFLUENCE + 1)

    elif 'vert_board_edge' in snake.states and 'horiz_board_edge' not in snake.states:

        if 'top_board_edge' in snake.states:
            possible_moves = ['down', 'left', 'right']

            if board.turn >= 3:
                influence.inc_down(BOARD_EDGE_INFLUENCE + 1)

        elif 'bottom_board_edge' in snake.states:
            possible_moves = ['up', 'left', 'right']

            if board.turn >= 3:
                influence.inc_up(BOARD_EDGE_INFLUENCE + 1)

    elif 'horiz_board_edge' in snake.states and 'vert_board_edge' in snake.states:

        #top left corner
        if head_x == 0 and head_y == 0:
            possible_moves = ['down', 'right']
        #top right corner
        elif head_x == board.width - 1 and head_y == 0:
            possible_moves = ['down', 'left']
        #bottom left corner
        elif head_x == 0 and head_y == board.height - 1:
            possible_moves = ['up', 'right']
        #bottom right corner
        elif head_x == board.width - 1 and head_y == board.height - 1:
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
            spacetaker = board.get_grid_space(tile_x, tile_y - 1)

        elif possible_moves[i] == 'down':
            spacetaker = board.get_grid_space(tile_x, tile_y + 1)

        elif possible_moves[i] == 'left':
            spacetaker = board.get_grid_space(tile_x - 1, tile_y)

        elif possible_moves[i] == 'right':
            spacetaker = board.get_grid_space(tile_x + 1, tile_y)

        #not a valid tile
        if spacetaker == 'mysnake' or spacetaker == 'enemysnake':
            possible_moves.pop(i)
            i -= 1
        i += 1
        
    return possible_moves


'''
Function to perform an A* search for a desired destination point (own tail, closest food ...).
Heuristic:
    F = Total cost of the node; F = G + H
    G = Distance (in spaces/moves needed) between current node & end node
    H = Heuristic -> Estimated distance (Pythagorus, under-est.) between current node & end node

    Time complexity: O(b^d), with 'd'= shortest path to target, 'b'= number of successors per state (4)
'''
def a_star_search(board, start, target):

    #create lists to hold search nodes
    open_set = []
    closed_set = []
    bound = len(board.grid) - 1

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

        #get (valid) adjacent tile coordinates to create children nodes
        #*** assumes board is square here ***
        adjacent_tiles = current_node.get_adjacent_spaces()
        adjacent_tiles = [tile for tile in adjacent_tiles
                            if not ((tile[0] < 0 or tile[0] > bound) or (tile[1] < 0 or tile[1] > bound))]

        #check tiles for node creation
        children = []
        for tile in adjacent_tiles:
            
            #skip tile if it's taken
            if board.get_grid_space(tile[0], tile[1]) != 'empty' and board.get_grid_space(tile[0], tile[1]) != 'food':
                continue

            #create new child node and append
            child = classes.SearchNode(current_node, tile)
            children.append(child)

        #-----CHILDREN-----
        
        #check children for open nodes with lower f values thn child 
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
  "move": "right"
}
'''

@bottle.post('/move')
def move():
    #data = bottle.request.json
    data = json.load(bottle.request.body)

    #print("TEST\n")
    #print(json.dumps(data))

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

    #get my_snake head coordinates
    #head_x, head_y = my_snake.get_head()


    #check snake's previous move/next body part - 2nd priority influence
    invalid_dir = ''
    if board.turn >= 3:
        invalid_dir = my_snake.get_invalid_dir()

    #finding food - Pythagorus for closest food find, A* Search to get the shortest path
    if board.turn >= 3:
        closest_food, closest_dist = find_food(my_snake, board)

        if closest_food and closest_dist <= CLOSE_FOOD_MAX_DIST:
            food_path = a_star_search(board, my_snake.get_head(), closest_food)

            if food_path:
                first_move = my_snake.dir_towards(food_path[0])

                if first_move == 'up':
                    influence.inc_up(CLOSE_FOOD_INFLUENCE)
                elif first_move == 'down':
                    influence.inc_down(CLOSE_FOOD_INFLUENCE)
                elif first_move == 'left':
                    influence.inc_left(CLOSE_FOOD_INFLUENCE)
                elif first_move == 'right':
                    influence.inc_right(CLOSE_FOOD_INFLUENCE)


  #----------MOVE DECISION-MAKING----------
    #priority influence 1
    #ADDED - drive snake away from edge, towards middle
    possible_moves = check_valid_moves(my_snake, my_snake.get_head(), board, influence)

    #priority influence 2
    try:
        possible_moves.remove(invalid_dir)
    except ValueError:
        pass
    
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