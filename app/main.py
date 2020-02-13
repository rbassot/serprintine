#modified to run: Python 3.7.6

import json
import sys
import os
import random
import bottle

#custom game class module
sys.path.insert(0, "C:/Users/pbass/OneDrive/code_projects/battlesnake/serprintine/app")
from .classes import *

from .api import ping_response, start_response, move_response, end_response


#----------GAME CONSTANTS----------
LOW_HEALTH = 30



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
    print(json.dumps(data))

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
    data = bottle.request.json

    #JSON object maintenance
    my_snake, enemy_snakes, board = initialize(json.dumps(data))


    #----------CALCULATING BEST MOVE----------
    '''
    STRATEGY:
        - To calculate the amount of move influences my snake has based on the situation of the game.
        - Total the influence counts after every check and select a direction to move in.
    '''
    move_up = move_down = move_left = move_right = 0

    #get my head coordinates
    head_x, head_y = my_snake.get_head()

    #check snake's head location on board - 1st priority influence
    if head_x == 1 or head_x == board.width:
        move_up += 1
        move_down += 1
        horiz_board_edge = True

    if head_y == 1 or head_y == board.height:
        move_left += 1
        move_right += 1
        vert_board_edge = True

    #check snake's previous move/next body part - 2nd priority influence
    prev_direction = my_snake.get_body_location()

    




    print("TEST\n")
    print(json.dumps(data))

    #----------MOVE DECISION-MAKING----------
    #priority influence 1
    if horiz_board_edge and not vert_board_edge:
        possible_moves = ['up', 'down']
    
    elif vert_board_edge and not horiz_board_edge:
        possible_moves = ['left', 'right']

    #Case where snake is in a corner of the board???
    #elif horiz_board_edge and vert_board_edge:        

    else:
        possible_moves = ['up', 'down', 'left', 'right']

    #priority influence 2
    try:
        possible_moves.remove(prev_direction)
    except ValueError:
        pass
    
    #secondary influences
    move_influences = []
    if 'up' in possible_moves:
        move_influences.append(move_up)
    if 'down' in possible_moves:
        move_influences.append(move_down)
    if 'left' in possible_moves:
        move_influences.append(move_left)
    if 'right' in possible_moves:
        move_influences.append(move_right)

    move_pairs = dict(zip(possible_moves, move_influences))
    move = max(move_pairs, key=move_pairs.get)

    #directions = ['up', 'down', 'left', 'right']
    #move = 'up'

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



#----------GAME FUNCTIONS-----------

'''
initialize(): Function to convert the JSON request data into usable objects.
'''
def initialize(request):

    #board maintenance
    width = request['board']['width'] 
    height = request['board']['height'] 
    food = []

    for meal in request['board']['food']:
        x = meal['x']
        y = meal['y']
        food.append((x, y))

    board = classes.Board(width, height, food)

    #my snake maintenance
    health = request['you']['health']
    body = []
    for part in request['you']['body']:
        x = part['x']
        y = part['y']
        body.append((x, y))

    my_snake = classes.Snake(body, health)

    #enemy snake maintenance
    enemy_snakes = []
    for snake in request['board']['snakes']:

        enemy_health = snake['health']
        enemy_body = []

        for part in snake['body']:
            x = part['x']
            y = part['y']
            enemy_body.append((x, y))

        enemy_snake = Snake(enemy_body, enemy_health)
        enemy_snakes.extend(enemy_snake)

    return my_snake, enemy_snakes, board


# Expose WSGI app (so gunicorn can find it)
application = bottle.default_app()

def main():
    bottle.run(
        application,
        host=os.getenv('IP', '0.0.0.0'),
        port=os.getenv('PORT', '8080'),
        debug=os.getenv('DEBUG', True)
    )

if __name__ == '__main__':
    main()