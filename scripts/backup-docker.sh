#!/bin/sh
set -eu
project_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$project_dir"
backup_name="bsw-rotacija-$(date -u +%Y%m%d-%H%M%S)-$$.sqlite3"
# Supply -f compose.local.yaml when backing up the local Docker installation.
if [ "${1:-}" = "local" ]; then
  docker compose -f compose.local.yaml exec -T app python backup.py "/backups/$backup_name"
else
  docker compose exec -T app python backup.py "/backups/$backup_name"
fi
