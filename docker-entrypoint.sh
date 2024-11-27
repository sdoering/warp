#!/bin/bash
set -e

# Initialize the database if it doesn't exist or is empty
if [ ! -s /opt/warp/data/warp.db ]; then
    echo "Initializing database..."
    sqlite3 /opt/warp/data/warp.db < /opt/warp/sql/sqlite_schema.sql
fi

# Execute the original command (uwsgi)
exec "$@"