# A Dunn & Bradstreet caching microservice

## Dependencies

Python 3.7
Django 2+

## Prerequisites 

1. Clone this repository

2. Set up and activate a virtual env

3. Install pip-tools: `pip install pip-tools`

## Installation

1. Install packages in requirements-dev.txt using pip-sync: `pip-sync requirements-dev.txt`

2. Create an .env file: `cp sample_env .env`

3. Get some SSO credentials and add them to your .env file. See the section below on staff-sso integration.
   NOTE: only required if you want to access the admin section.

4. Run migrations and start a web server: `./manage.py migrate` and then `./manage.py runserver`

## Run tests

Run `py.test` from the project's root directory

## DIT staff-sso integration

The admin section is protected by the DIT's internal SSO application.  To run a local development environment with admin
access you can either request a set of UAT SSO credentials from the webops team, or check out the staff-sso github
repository and run the application locally. See https://www.github.com/uktrade/staff-sso for more details.
