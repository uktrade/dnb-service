# A Dunn & Bradstreet caching microservice

## Dependencies

Python 3.7
Django 2+
Postgres 10

## Prerequisites 

1. Clone this repository

2. Set up and activate a virtual env

3. Install pip-tools: `pip install pip-tools`

## Installation

1. Install packages in requirements-dev.txt using pip-sync: `pip-sync requirements-dev.txt`

2. Create an .env file: `cp sample_env .env`

3. Run migrations and start a web server: `./manage.py migrate` and then `./manage.py runserver`

## Run tests

Run `py.test` from the project's root directory
