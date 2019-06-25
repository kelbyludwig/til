.PHONY: run init

run:
	FLASK_APP=til.py pipenv run flask run

init:
	pipenv run python til.py
