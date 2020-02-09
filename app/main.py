import json
import os
import random
import bottle

#custom game class module
import classes

from api import ping_response, start_response, move_response, end_response


#----------GAME CONSTANTS----------
LOW_HEALTH = 30


#----------GAME FUNCTIONS-----------

'''
initialize(): Function to convert the JSON request data into usable objects.
'''
def initialize(request):

    #Parse JSON into a dictionary
    data = json.loads(request)

    #board maintenance
    width = data['board']['width'] 
    height = data['board']['height'] 
    food = []

    for meal in data['board']['food']:
        x = meal['x']
        y = meal['y']
        food.extend((x, y))

    board = classes.Board(width, height, food)

    #my snake maintenance
    health = data['you']['health']
    body = []
    for part in data['you']['body']:
        x = part['x']
        y = part['y']
        body.extend((x, y))

    my_snake = classes.Snake(body, health)

    #opponent snake maintenance
    opp_snakes = []
    for snake in snakes:

        opp_health = snake['health']
        body = []

        for part in snake['body']:
            x = part['x']
            y = part['y']
            body.extend((x, y))

        opp_snake = Snake(body, health)
        opp_snakes.extend(opp_snake)

    return my_snake, opp_snakes, board



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
    #data = bottle.request.json

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
        'taunt': "Printin' lines faster than you",
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

    #Parse JSON object
    my_snake, snakes, game = initialize(data)

    """
    TODO: Using the data from the endpoint request object, your
            snake AI must choose a direction to move in.
    """
    print("TEST\n")
    print(json.dumps(data))

    directions = ['up', 'down', 'left', 'right']
    move = 'up'

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


# Expose WSGI app (so gunicorn can find it)
application = bottle.default_app()

if __name__ == '__main__':
    bottle.run(
        application,
        host=os.getenv('IP', '0.0.0.0'),
        port=os.getenv('PORT', '8080'),
        debug=os.getenv('DEBUG', True)
    )
