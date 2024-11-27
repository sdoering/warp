#!/bin/bash
set -e

# Debug information
echo "Running as user: $(id)"
echo "Data directory permissions: $(ls -la /opt/warp/data)"

# Check for required environment variables
if [ -z "$WARP_ADMIN_USER" ] || [ -z "$WARP_ADMIN_PASSWORD" ]; then
    echo "Error: WARP_ADMIN_USER and WARP_ADMIN_PASSWORD must be set"
    exit 1
fi

# Check directory permissions
if [ ! -w "/opt/warp/data" ]; then
    echo "Error: Data directory /opt/warp/data is not writable by $(id)"
    exit 1
fi

# Function to initialize the database
initialize_database() {
    echo "Initializing database..."
    
    # Create database file with correct permissions
    touch /opt/warp/data/warp.db
    chmod 644 /opt/warp/data/warp.db
    
    if ! sqlite3 /opt/warp/data/warp.db < /opt/warp/sql/sqlite_schema.sql; then
        echo "Error: Failed to initialize database schema"
        exit 1
    fi
    
    # Create admin user if it doesn't exist
    echo "Checking for admin user..."
    if ! sqlite3 /opt/warp/data/warp.db "SELECT 1 FROM users WHERE username = '${WARP_ADMIN_USER}' LIMIT 1;" 2>/dev/null; then
        echo "Creating admin user..."
        if ! sqlite3 /opt/warp/data/warp.db "INSERT INTO users (username, password, is_admin) VALUES ('${WARP_ADMIN_USER}', '${WARP_ADMIN_PASSWORD}', 1);"; then
            echo "Error: Failed to create admin user"
            exit 1
        fi
    fi
}

# Check if database exists and is initialized
if [ ! -f /opt/warp/data/warp.db ]; then
    initialize_database
else
    # Check if database is writable
    if [ ! -w "/opt/warp/data/warp.db" ]; then
        echo "Error: Database file is not writable by $(id)"
        exit 1
    fi
    
    # Verify database structure
    if ! sqlite3 /opt/warp/data/warp.db "SELECT 1 FROM users LIMIT 1;" &>/dev/null; then
        echo "Database exists but appears to be invalid. Reinitializing..."
        initialize_database
    fi
fi

echo "Database initialization complete"
echo "Final database permissions: $(ls -la /opt/warp/data/warp.db)"

# Execute the main command (uwsgi)
exec "$@"