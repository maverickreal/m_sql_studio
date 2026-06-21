#!/bin/bash

echo "Waiting for local MongoDB node to start..."
until mongosh --eval "print('local is up')" &>/dev/null; do
  sleep 2
done

if mongosh --eval "rs.status()" | grep -q "rs0"; then
  echo "Replica set already initialized."
else
  echo "Initiating replica set..."
  mongosh <<EOF
  var config = {
    "_id": "rs0",
    "version": 1,
    "members": [
      { "_id": 0, "host": "mongo1:27017", "priority": 2 },
      { "_id": 1, "host": "mongo2:27017", "priority": 1 },
      { "_id": 2, "host": "mongo3:27017", "priority": 1 }
    ]
  };
  rs.initiate(config);
EOF
  echo "Waiting for replica set to elect primary..."
  until mongosh --eval "db.hello().isWritablePrimary" 2>/dev/null | grep -q "true"; do
    sleep 1
  done
fi

if mongosh -u "$MONGO_USER" -p "$MONGO_PASSWORD" --authenticationDatabase admin --eval "print('auth ok')" &>/dev/null; then
  echo "Users already exist."
else
  echo "Creating users..."
  mongosh <<EOF
  use admin;
  db.createUser({
    user: "$MONGO_USER",
    pwd: "$MONGO_PASSWORD",
    roles: [ { role: "root", db: "admin" } ]
  });

  db.auth("$MONGO_USER", "$MONGO_PASSWORD");

  use $API_GATEWAY_MONGO_DB;
  db.createUser({
    user: "$API_GATEWAY_MONGO_USER",
    pwd: "$API_GATEWAY_MONGO_PASSWORD",
    roles: [ { role: "$API_GATEWAY_MONGO_ROLE", db: "$API_GATEWAY_MONGO_DB" } ]
  });
EOF
fi

echo "MongoDB replica set initialization complete."
