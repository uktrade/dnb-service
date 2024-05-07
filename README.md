# A Dun & Bradstreet caching microservice

[![codecov](https://codecov.io/gh/uktrade/dnb-service/branch/master/graph/badge.svg)](https://codecov.io/gh/uktrade/dnb-service)

## Dependencies

Python 3.10
Django 4.2.11+  
Postgres 10  

## Prerequisites

1. Clone this repository

2. Set up and activate a virtual env  
   ````
   python3.10 -m venv env
   source env/bin/activate
   ````

3. Install pip-tools: `pip install pip-tools`

## Installation on the metal

1. Install packages in requirements-dev.txt using pip-sync: `pip-sync requirements-dev.txt`

2. Create an .env file: `cp sample_env .env`

3. Get some SSO credentials and add them to your .env file. See the section below on staff-sso integration.
   NOTE: only required if you want to access the admin section.

4. Load country fixtures (optional): `./manage.py loaddata company/fixtures/countries.yaml`

5. Run migrations and start a web server: `./manage.py migrate` and then `./manage.py runserver`

## Running with docker

1. Create a .env file: `cp sample_env.docker .env`

2. Get some SSO credentials and add them to your .env file. See the section below on staff-sso integration.
   NOTE: only required if you want to access the admin section.

3. Run the app under docker-compose: `docker-compose up -d`

4. When using Apple M1 chipset you may have to run `docker-compose up --build` to force the load of the latest release of Dockerize.

## Run tests

Run `py.test` from the project's root directory

## Creating the `DNB_SERVICE_TOKEN` for data-hub-api

For data-hub-api to connect to dnb-service, it must be provided with a token which is set inside the data-hub-api .env file under `DNB_SERVICE_TOKEN`.

### Local development token

1. Create a user in dnb-service.
2. Log into the admin with this user.
3. Go to tokens.
4. Add a token.
5. Select your user and save.
6. Copy your token key into the data-hub-api `DNB_SERVICE_TOKEN` environment variable.

### UAT, dev, staging and prod token

#### Using the current api user

1. There is a default user set for these environments with the username: api-user@digital.trade.gov.uk
2. You can find this users token in the Django Admin and selecting the token model or by accessing the django shell for the environment you require.
3. For getting the token in the Django shell run the following:
   ```
   from rest_framework.authtoken.models import Token
   from django.contrib.auth import get_user_model

   User = get_user_model()
   user = User.objects.get(email='api-user@digital.trade.gov.uk')

   token = Token.objects.get(user=user)
   print(token.key)
   ```
4. Copy the token printed above into data-hub-api `DNB_SERVICE_TOKEN` environment variable.

#### Creating a new api user

1. Access the Django shell for the environment you want to create a user for.
2. Run the following, you can change the email if required:
   ```
   from rest_framework.authtoken.models import Token
   from django.contrib.auth import get_user_model

   User = get_user_model()

   user = User.objects.create(email='api-user@digital.trade.gov.uk')
   token = Token.objects.create(user=user)

   print(token.key)
   ```
4. Copy the token printed above into data-hub-api `DNB_SERVICE_TOKEN` environment variable.

## DIT staff-sso integration

The admin section is protected by the DIT's internal SSO application.  To run a local development environment with admin
access you can either request a set of UAT SSO credentials from the webops team, or check out the staff-sso github
repository and run the application locally. See <https://www.github.com/uktrade/staff-sso> for more details.

## Swagger Documentation

Once the app is running, you will be able to visit <http://localhost:9000/api/swagger/> to see documentation for the endpoints.
