#!/bin/sh
# Usage: ./deploy/restore.sh backups/fnjee-YYYYMMDD-HHMMSS.archive.gz
# Restores into the running mongo container (drops collections that exist in the archive).
set -eu
[ -f "${1:-}" ] || { echo "usage: $0 <archive.gz>"; exit 1; }
. ./.env
docker compose exec -T mongo mongorestore \
  --uri="mongodb://${MONGO_ROOT_USER}:${MONGO_ROOT_PASSWORD}@localhost:27017/?authSource=admin" \
  --archive --gzip --drop < "$1"
echo "restored $1"
