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

BOARD_EDGE_INFLUENCE = 5
CLOSE_FOOD_INFLUENCE = 10

CLOSE_FOOD_MAX_DIST = 5




#----------GAME FUNCTIONS-----------

'''
initialize(): Function to maintain the JSON request data for usability.
'''
def initialize(request):

    #board maintenance
    width = int(request["board"]["width"]) 
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
        grid[x][y] = 'food'

    #my snake maintenance
    health = int(request['you']['health'])
    body = []
    for part in request['you']['body']:
        x = int(part['x'])
        y = int(part['y'])
        body.append((x, y))
        grid[x][y] = 'mysnake'

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
            grid[x][y] = 'enemysnake'

        enemy_snake = classes.Snake(enemy_body, enemy_health)
        enemy_snakes.append(enemy_snake)
    
    #complete board object
    board = classes.Board(width, height, food, grid)

    return my_snake, enemy_snakes, board


'''
find_food: Calculates the coordinates of the closest food source to the snake's
    head, using Pythagorus. Returns a tuple of the x & y coordinates.
'''
def find_food(snake, board):

    head_x, head_y = snake.get_head()
    closest_food = board.food[0]
    closest_dist = float(math.sqrt((board.width^2 + board.height^2)))

    #loop through food items on the board & calc distance
    if len(board.food) > 0: 
        for meal in board.food:
            hyp = snake.get_distance_to(meal)

            if hyp < closest_dist:
                closest_dist = hyp
                closest_food = meal
        
        return meal, closest_dist
    return False


@bottle.route('/')
def index():
    return "<h1>Serprintine</h1>"


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
    horiz_board_edge = False
    vert_board_edge = False

    #get my_snake head coordinates
    head_x, head_y = my_snake.get_head()

    #check for snake's head location at board edge - 1st priority influence
    if head_x == 0 or head_x == board.width - 1:
        influence.inc_up(BOARD_EDGE_INFLUENCE)
        influence.inc_down(BOARD_EDGE_INFLUENCE)
        horiz_board_edge = True

        if head_x == 0:
            left_board_edge = True

        else:
            right_board_edge = True

    if head_y == 0 or head_y == board.height - 1:
        influence.inc_left(BOARD_EDGE_INFLUENCE)
        influence.inc_right(BOARD_EDGE_INFLUENCE)
        vert_board_edge = True

        if head_y == 0:
            top_board_edge = True

        else:
            bottom_board_edge = True

    #check snake's previous move/next body part - 2nd priority influence
    invalid_dir = ""
    if data["turn"] >= 3:
        invalid_dir = my_snake.get_invalid_dir()

    #finding food
    if int(data["turn"]) >= 3:
        closest_food, closest_dist = find_food(my_snake, board)

        if closest_food and closest_dist <= CLOSE_FOOD_MAX_DIST:
            food_dirs = my_snake.dirs_towards(closest_food)

            if 'up' in food_dirs:
                influence.inc_up(CLOSE_FOOD_INFLUENCE)
            if 'down' in food_dirs:
                influence.inc_down(CLOSE_FOOD_INFLUENCE)
            if 'left' in food_dirs:
                influence.inc_left(CLOSE_FOOD_INFLUENCE)
            if 'right' in food_dirs:
                influence.inc_right(CLOSE_FOOD_INFLUENCE)



    #----------MOVE DECISION-MAKING----------
    #priority influence 1
    #ADDED - drive snake away from edge, towards middle
    if horiz_board_edge and not vert_board_edge:
        if left_board_edge:
            possible_moves = ['up', 'down', 'right']

            if int(data["turn"]) >= 3:
                influence.inc_right(BOARD_EDGE_INFLUENCE + 1)

        elif right_board_edge:
            possible_moves = ['up', 'down', 'left']

            if int(data["turn"]) >= 3:
                influence.inc_left(BOARD_EDGE_INFLUENCE + 1)

    elif vert_board_edge and not horiz_board_edge:

        if top_board_edge:
            possible_moves = ['down', 'left', 'right']

            if int(data["turn"]) >= 3:
                influence.inc_down(BOARD_EDGE_INFLUENCE + 1)

        elif bottom_board_edge:
            possible_moves = ['up', 'left', 'right']

            if int(data["turn"]) >= 3:
                influence.inc_up(BOARD_EDGE_INFLUENCE + 1)

        else:    
            possible_moves = ['left', 'right']

    elif horiz_board_edge and vert_board_edge:
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

    #directions = ['up', 'down', 'left', 'right']
    #index = random.randint(0,3)
    #move = directions[index]
    
    return move_response(move)


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