#!/usr/bin/env bash

# To run the E2E test:
# E2E_TEST=true MONGO_HOST= REDIS_HOST= npm run test -- assignment_execution.e2e.test.ts
# Check the test file for altering certain values.

set -e

KEYFILE="misc/init-db/mongodb/mongo-keyfile"
if [ ! -f "$KEYFILE" ]; then
  echo "Generating MongoDB keyfile..."
  mkdir -p misc/init-db/mongodb
  openssl rand -base64 741 > "$KEYFILE"
  chmod 400 "$KEYFILE"
fi

echo "Installing dependencies for api-gateway and sandbox."
cd ../m_sql_studio_api_gateway && npm ci
cd ../m_sql_studio_sandbox && npm ci
cd ../m_sql_studio

export COMPOSE_FILE=docker-compose.yml:docker-compose.dev.yml
export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-msql-studio}"

pkill -f "docker.*compose.*watch" || true

# Only this compose project — do not stop or prune the rest of the machine.
echo "Recreating ${COMPOSE_PROJECT_NAME} (containers + project volumes)."
docker compose down -v
docker compose up -d --build

# Seed initial data in DBs for dev env.
if [ -f .env ]; then
  ENV_MODE=$(grep "^ENV_MODE=" .env | cut -d'=' -f2);

  if [ "$ENV_MODE" = "DEV" ]; then
    echo "Seeding initial data in DBs for dev env."
    API_GATEWAY_URL=$(grep "^API_GATEWAY_URL=" .env | cut -d'=' -f2);
    export API_GATEWAY_URL=$API_GATEWAY_URL
    node misc/seed.js
  fi
fi

echo "Running 'docker compose watch'."
docker compose watch
