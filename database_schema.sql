PRAGMA foreign_keys = off;
BEGIN TRANSACTION;

-- Table: matches
CREATE TABLE matches (id INTEGER PRIMARY KEY ON CONFLICT ROLLBACK AUTOINCREMENT NOT NULL, date DATETIME DEFAULT (datetime('now')) NOT NULL, player1 BIGINT REFERENCES players (id) NOT NULL, player2 BIGINT REFERENCES players (id) NOT NULL, player1_score INTEGER NOT NULL CHECK (player1_score > - 1), player2_score INTEGER NOT NULL CHECK (player2_score > - 1), player1_old_mu DOUBLE NOT NULL, player1_old_phi DOUBLE NOT NULL, player1_old_sigma DOUBLE NOT NULL, player1_new_mu DOUBLE NOT NULL, player1_new_phi DOUBLE NOT NULL, player1_new_sigma DOUBLE NOT NULL, player2_old_mu DOUBLE NOT NULL, player2_old_phi DOUBLE NOT NULL, player2_old_sigma DOUBLE NOT NULL, player2_new_mu DOUBLE NOT NULL, player2_new_phi DOUBLE NOT NULL, player2_new_sigma DOUBLE NOT NULL, player1_rating_change INTEGER GENERATED ALWAYS AS (CAST (player1_new_mu AS INT) - CAST (player1_old_mu AS INT)) STORED, player2_rating_change INTEGER GENERATED ALWAYS AS (CAST (player2_new_mu AS INT) - CAST (player2_old_mu AS INT)) STORED);

-- Table: pending_matches
CREATE TABLE pending_matches (message_id INTEGER NOT NULL PRIMARY KEY ON CONFLICT REPLACE, player1 INTEGER REFERENCES players (id) NOT NULL, player2 INTEGER REFERENCES players (id) NOT NULL, time DATETIME NOT NULL);

-- Table: players
CREATE TABLE players (id BIGINT PRIMARY KEY ON CONFLICT ROLLBACK NOT NULL, registration_date DATETIME DEFAULT (datetime('now')) NOT NULL, platforms STRING NOT NULL, display_name STRING UNIQUE ON CONFLICT ROLLBACK COLLATE NOCASE, rating_mu DOUBLE DEFAULT (1500) NOT NULL, rating_phi DOUBLE DEFAULT (350) NOT NULL, rating_sigma DOUBLE NOT NULL DEFAULT (0.06), username_pc STRING UNIQUE ON CONFLICT ROLLBACK COLLATE NOCASE, username_switch STRING UNIQUE ON CONFLICT ROLLBACK COLLATE NOCASE, username_ps4 STRING UNIQUE ON CONFLICT ROLLBACK COLLATE NOCASE);

-- Trigger: Report
CREATE TRIGGER Report AFTER INSERT ON matches BEGIN UPDATE players SET rating_mu = new.player1_new_mu, rating_phi = new.player1_new_phi, rating_sigma = new.player1_new_sigma WHERE id = new.player1; UPDATE players SET rating_mu = new.player2_new_mu, rating_phi = new.player2_new_phi, rating_sigma = new.player2_new_sigma WHERE id = new.player2; END;

COMMIT TRANSACTION;
PRAGMA foreign_keys = on;
