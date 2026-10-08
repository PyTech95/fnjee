#!/bin/sh
# Daily mongodump into /backups, prunes archives older than KEEP_DAYS.
set -eu
while true; do
  ts=$(date -u +%Y%m%d-%H%M%S)
  out="/backups/fnjee-$ts.archive.gz"
  if mongodump --uri="$MONGO_URI" --archive="$out" --gzip; then
    echo "[backup] ok $out"
  else
    echo "[backup] FAILED $ts" >&2
    rm -f "$out"
  fi
  find /backups -name 'fnjee-*.archive.gz' -mtime +"$KEEP_DAYS" -delete
  sleep 86400
done
