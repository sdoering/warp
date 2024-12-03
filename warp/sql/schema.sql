CREATE TABLE blobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mimetype TEXT NOT NULL,
    data BLOB NOT NULL,
    etag INTEGER NOT NULL
);

CREATE TABLE users (
    login TEXT PRIMARY KEY,
    password TEXT,
    name TEXT,
    account_type INTEGER NOT NULL
);

-- create initial admin with password 'noneshallpass'
INSERT OR IGNORE INTO users VALUES ('admin','scrypt:32768:8:1$YqyVMsZYy1nLWStFSInR2g$2YgVN0QgzxxqkZfdV9mM/4JUe3L3CEfriMtgnnnKx9o','Admin',10);

CREATE INDEX users_account_type_idx ON users(account_type);

CREATE TABLE groups (
    "group" TEXT NOT NULL,
    login TEXT NOT NULL,
    PRIMARY KEY ("group", login),
    FOREIGN KEY ("group") REFERENCES users(login) ON DELETE CASCADE,
    FOREIGN KEY (login) REFERENCES users(login) ON DELETE CASCADE
);

CREATE TABLE zone (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    zone_group INTEGER NOT NULL,
    name TEXT NOT NULL,
    iid INTEGER,
    FOREIGN KEY (iid) REFERENCES blobs(id) ON DELETE SET NULL
);

CREATE TABLE zone_assign (
    zid INTEGER NOT NULL,
    login TEXT NOT NULL,
    zone_role INTEGER NOT NULL,
    PRIMARY KEY (zid, login),
    FOREIGN KEY (zid) REFERENCES zone(id) ON DELETE CASCADE,
    FOREIGN KEY (login) REFERENCES users(login) ON DELETE CASCADE
);

CREATE TABLE seat (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    zid INTEGER NOT NULL,
    name TEXT NOT NULL,
    x INTEGER NOT NULL,
    y INTEGER NOT NULL,
    enabled INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (zid) REFERENCES zone(id) ON DELETE CASCADE
);

CREATE TABLE seat_assign (
    sid INTEGER NOT NULL,
    login TEXT NOT NULL,
    PRIMARY KEY (sid, login),
    FOREIGN KEY (sid) REFERENCES seat(id) ON DELETE CASCADE,
    FOREIGN KEY (login) REFERENCES users(login) ON DELETE CASCADE
);

CREATE INDEX seat_zid ON seat(zid);

CREATE TABLE book (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    login TEXT NOT NULL,
    sid INTEGER NOT NULL,
    fromts INTEGER NOT NULL,
    tots INTEGER NOT NULL,
    FOREIGN KEY (login) REFERENCES users(login) ON DELETE CASCADE,
    FOREIGN KEY (sid) REFERENCES seat(id) ON DELETE CASCADE
);

CREATE INDEX book_login ON book(login);
CREATE INDEX book_sid ON book(sid);
CREATE INDEX book_fromTS ON book(fromts);
CREATE INDEX book_toTS ON book(tots);

-- Replace materialized view with a regular view for SQLite
CREATE VIEW user_to_zone_roles AS
    WITH RECURSIVE zone_assign_expanded("login", zid, zone_role, account_type) AS (
        SELECT za."login", za.zid, za.zone_role, u.account_type 
        FROM zone_assign za
        JOIN users u ON za."login" = u."login"
        UNION ALL
        SELECT g."login", za.zid, za.zone_role, u.account_type 
        FROM zone_assign_expanded za
        JOIN groups g ON g."group" = za."login"
        JOIN users u ON g."login" = u."login"
    )
    SELECT login, zid, MIN(zone_role) as zone_role
    FROM zone_assign_expanded
    WHERE account_type < 100
    GROUP BY zid, login;

-- Replace PostgreSQL trigger with SQLite trigger for booking validation
CREATE TRIGGER book_overlap_insert_check
BEFORE INSERT ON book
FOR EACH ROW
BEGIN
    SELECT CASE
        WHEN NEW.fromts >= NEW.tots THEN
            RAISE(ABORT, 'Incorrect time')
        WHEN EXISTS (
            SELECT 1 FROM book b
            JOIN seat s ON b.sid = s.id
            JOIN zone z ON s.zid = z.id
            WHERE z.zone_group = (
                SELECT zone_group 
                FROM zone z 
                JOIN seat s ON z.id = s.zid 
                WHERE s.id = NEW.sid 
                LIMIT 1
            )
            AND (b.sid = NEW.sid OR b.login = NEW.login)
            AND b.fromts < NEW.tots
            AND b.tots > NEW.fromts
        ) THEN
            RAISE(ABORT, 'Overlapping time for this seat or users')
    END;
END;
