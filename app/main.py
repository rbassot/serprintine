#modified to run: Python 3.7.6

import json
import sys
import os
import random
import bottle

#custom game class module
import app.classes as classes

from .api import ping_response, start_response, move_response, end_response


#----------GAME CONSTANTS----------
LOW_HEALTH = 30

BOARD_EDGE_INFLUENCE = 5
CLOSE_FOOD_INFLUENCE = 6




#----------GAME FUNCTIONS-----------

'''
initialize(): Function to maintain the JSON request data for usability.
'''
def initialize(request):

    #board maintenance
    width = int(request["board"]["width"]) 
    height = int(request['board']['height']) 
    food = []

    for meal in request['board']['food']:
        x = int(meal['x'])
        y = int(meal['y'])
        food.append((x, y))

    board = classes.Board(width, height, food)

    #my snake maintenance
    health = int(request['you']['health'])
    body = []
    for part in request['you']['body']:
        x = int(part['x'])
        y = int(part['y'])
        body.append((x, y))

    my_snake = classes.Snake(body, health)

    #enemy snake maintenance
    enemy_snakes = []
    for snake in request['board']['snakes']:

        enemy_health = snake['health']
        enemy_body = []

        for part in snake['body']:
            x = int(part['x'])
            y = int(part['y'])
            enemy_body.append((x, y))

        enemy_snake = classes.Snake(enemy_body, enemy_health)
        enemy_snakes.append(enemy_snake)

    return my_snake, enemy_snakes, board


'''
find_closest_food(): Calculates the coordinates of the closest food source to the snake's head.
    Returns a tuple of the x & y coordinates.
'''
def find_closest_food(snake, board):

    food_dist = board.width
    closest_food = ()

    for meal in board.food:
        if snake.get_distance_to(meal) < food_dist:
            closest_food = meal
            food_dist = snake.get_distance_to(meal)

    if food_dist == board.width:
        return None, None
    
    return closest_food[0], closest_food[1]



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

    if head_y == 0 or head_y == board.height - 1:
        influence.inc_left(BOARD_EDGE_INFLUENCE)
        influence.inc_right(BOARD_EDGE_INFLUENCE)
        vert_board_edge = True

    #check snake's previous move/next body part - 2nd priority influence
    prev_direction = ""
    if data["turn"] >= 3:
        prev_direction = my_snake.get_body_location()

    #finding food
    meal_x, meal_y = find_closest_food(my_snake, board)
    if meal_x != None and meal_y != None:
        meal = (meal_x, meal_y)
        food_dir = my_snake.dir_towards(meal)

        if food_dir == 'up':
            influence.inc_up(CLOSE_FOOD_INFLUENCE)
        elif food_dir == 'down':
            influence.inc_down(CLOSE_FOOD_INFLUENCE)
        elif food_dir == 'left':
            influence.inc_left(CLOSE_FOOD_INFLUENCE)
        elif food_dir == 'right':
            influence.inc_right(CLOSE_FOOD_INFLUENCE)



    #----------MOVE DECISION-MAKING----------
    #priority influence 1
    if horiz_board_edge and not vert_board_edge:
        possible_moves = ['up', 'down']
    
    elif vert_board_edge and not horiz_board_edge:
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
    if horiz_board_edge or vert_board_edge:
        try:
            possible_moves.remove(prev_direction)
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