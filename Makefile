.PHONY: run init

run:
	pipenv run gunicorn run:app

init:
	pipenv run python til.py
