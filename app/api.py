import json
from bottle import HTTPResponse

def ping_response():
    return HTTPResponse(
        status=200
    )

def start_response(color):
    assert type(color) is str, \
        "Color value must be string"

    return HTTPResponse(
        status=200,
        headers={
            "Content-Type": "application/json"
        },
        body=json.dumps({
            "color": color
        })
    )

def move_response(move, shout):
    assert move in ['up', 'down', 'left', 'right'], \
        "Move must be one of [up, down, left, right]"
    assert str(shout)

    return HTTPResponse(
        status=200,
        headers={
            "Content-Type": "application/json"
        },
        body=json.dumps({
            "move": move,
            "shout": shout
        })
    )

def end_response():
    return HTTPResponse(
        status=200
    )
