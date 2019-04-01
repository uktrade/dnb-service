# A Dunn & Bradstreet caching microservice

## Dependencies

Python 3.7
Django 2+

## Installation

1. Set up and activate a virtual env

2. Install pip-tools: `pip install pip-tools`

3. Install packages in requirements.txt using pip-sync; `pip-sync requirements.txt`

4. Create a .env file:  `cp sample_env .env`

5. Run migrations and start a web server: `./manage.py migrate` and then `./manage.py runserver`

