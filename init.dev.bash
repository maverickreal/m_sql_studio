#!/usr/bin/env bash

# To run the E2E test:
# E2E_TEST=true MONGO_HOST= REDIS_HOST= npm run test -- assignment_execution.e2e.test.ts
# Check the test file for altering certain values.

set -e

echo "Installing dependencies for api-gateway and sandbox."
cd ../m_sql_studio_api_gateway && npm ci
cd ../m_sql_studio_sandbox && npm ci
cd ../m_sql_studio

# Cleanup containers, volumes, and networks and rebuild images.
docker stop $(docker ps -q) 2>/dev/null || true && \
docker rm -f $(docker ps -aq) 2>/dev/null || true && \
docker volume rm -f $(docker volume ls -q) 2>/dev/null || true && \
docker network rm $(docker network ls --filter type=custom -q) 2>/dev/null || true && \
echo "Removed containers, volumes, and networks and rebuilding images.";

docker compose up -d --build;

# Seed initial data in DBs for dev env.
if [ -f .env ]; then
  ENV_MODE=$(grep "^ENV_MODE=" .env | cut -d'=' -f2);

  if [ "$ENV_MODE" = "DEV" ]; then
    echo "Seeding initial data in DBs for dev env."
    API_GATEWAY_URL=$(grep "^API_GATEWAY_URL=" .env | cut -d'=' -f2);
    export API_GATEWAY_URL=$API_GATEWAY_URL;
    node misc/seed.js;
  fi
fi

echo "Running `docker compose watch`."
docker compose watch
