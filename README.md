# Python Battlesnake - Serprintine*

Serprintine is a project based off the Python starter-snake found at https://play.battlesnake.com/. The most developed snake (Serprintine*) lives on this branch (snake-update).

Serprintine* is a search-driven Battlesnake AI in Python 3.7 that implements A* searching and dead-end filling algorithms. Food-finding and own-tail-chasing are prioritized in the arena. Valid moves are assessed and the most positively influenced move is selected.

This snake uses [Bottle web framework](http://bottlepy.org/docs/dev/index.html) to manage HTTP requests and responses, and [gunicorn web server](http://gunicorn.org/) for running bottle on [Heroku](https://heroku.com/deploy) as a cloud application.


For API documentation, visit [https://github.com/battlesnakeio/community/blob/master/starter-snakes.md](https://github.com/battlesnakeio/community/blob/master/starter-snakes.md). Dependencies are listed in [requirements.txt](https://github.com/rbassot/serprintine/blob/snake-update/requirements.txt).

----------------------------------------------------------------------------------------------------------------------------------------

## Running Serprintine* Locally

1) [Fork this repo](https://github.com/rbassot/serprintine/fork).

2) Clone this repo to your development environment:
```
git clone git@github.com:<your github username>/serprintine.git
```

3) Checkout this development branch:
```
git checkout snake-update
```

4) Assure a version of Python 3 is installed (I used Python 3.7.6 for this project). Install dependencies using [pip](https://pip.pypa.io/en/latest/installing.html):
```
pip install -r requirements.txt
```

5) Run the local server:
```
python run.py
```

6) In a new CLI, test your snake by sending a curl to the running snake. [data.json](https://github.com/rbassot/serprintine/blob/snake-update/data.json) contains a sample JSON dataset based off the Battlesnake API. The curl below targets the /move endpoint.
```
curl -XPOST -H 'Content-Type:application/json' --data @data.json http://localhost:8080/move
```

## Deploying to Heroku

1) Create a new Heroku app:
```
heroku create [APP_NAME]
```

2) Deploy code to Heroku servers:
```
git push heroku master
```

3) Open Heroku app in browser:
```
heroku open
```
or visit [http://APP_NAME.herokuapp.com](http://APP_NAME.herokuapp.com).

4) View server logs with the `heroku logs` command:
```
heroku logs --tail
```

## Acknowledgements

Thank you to the people behind Battlesnake to allow the use of a starter snake in Python that kickstarted this project. Parts of this README were taken from the Battlesnake Python starter-snake.