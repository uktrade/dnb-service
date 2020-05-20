# Deployment instructions

## Deploying to staging

Here is how to deploy dnb-service to staging:

1. Go to Jenkins and navigate to `external-company-service-staging`, then append `/build?delay=0sec` to the end of the URL.
2. Scroll down to the bottom of the page and press the 'Build' button
3. Click on the “progress bar” to see the logs
4. If it says SUCCESS at the end, your changes have deployed successfully

## Deploying to production

Here is how to deploy dnb-service to production:

1. Go to Jenkins and navigate to `external-company-service-prod`. Click on the 'Build Now' button.
2. Click on the “progress bar” to see the logs
3. If it says SUCCESS at the end, your changes have deployed successfully
