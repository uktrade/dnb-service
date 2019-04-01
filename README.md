# A Dunn & Bradstreet caching microservice

## Dependencies

Python 3.7
Django 2+

## Installation

1. Clone this repository

2. Set up and activate a virtual env

3. Install pip-tools: `pip install pip-tools`

4. Install packages in requirements.txt using pip-sync; `pip-sync requirements.txt`

5. Create a .env file:  `cp sample_env .env`

6. Run migrations and start a web server: `./manage.py migrate` and then `./manage.py runserver`

## Run tests

Run `py.test` from the project's root directory.
