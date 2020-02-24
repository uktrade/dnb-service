#!/bin/bash -xe
python /app/manage.py migrate --noinput
# Load initial country fixture
python /app/manage.py loaddata company/fixtures/countries.yaml
python /app/manage.py create_dev_auth_token $DEV_AUTH_EMAIL $DEV_AUTH_TOKEN

# Run runserver in a while loop as the whole docker container will otherwise die
# when there is bad syntax
while true; do
    python /app/manage.py runserver 0.0.0.0:8000
    sleep 1
done
