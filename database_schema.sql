PRAGMA foreign_keys = off;
BEGIN TRANSACTION;

-- Table: matches
CREATE TABLE matches (id INTEGER PRIMARY KEY ON CONFLICT ROLLBACK AUTOINCREMENT NOT NULL, date DATETIME DEFAULT (datetime('now')) NOT NULL, player1 BIGINT REFERENCES players (id) NOT NULL, player2 BIGINT REFERENCES players (id) NOT NULL, player1_score INTEGER NOT NULL CHECK (player1_score > - 1), player2_score INTEGER NOT NULL CHECK (player2_score > - 1), player1_old_mu DOUBLE NOT NULL, player1_old_phi DOUBLE NOT NULL, player1_old_sigma DOUBLE NOT NULL, player1_new_mu DOUBLE NOT NULL, player1_new_phi DOUBLE NOT NULL, player1_new_sigma DOUBLE NOT NULL, player2_old_mu DOUBLE NOT NULL, player2_old_phi DOUBLE NOT NULL, player2_old_sigma DOUBLE NOT NULL, player2_new_mu DOUBLE NOT NULL, player2_new_phi DOUBLE NOT NULL, player2_new_sigma DOUBLE NOT NULL, player1_rating_change INTEGER GENERATED ALWAYS AS (CAST (player1_new_mu AS INT) - CAST (player1_old_mu AS INT)) STORED, player2_rating_change INTEGER GENERATED ALWAYS AS (CAST (player2_new_mu AS INT) - CAST (player2_old_mu AS INT)) STORED);

-- Table: players
CREATE TABLE players (id BIGINT PRIMARY KEY ON CONFLICT ROLLBACK NOT NULL, registration_date DATETIME DEFAULT (datetime('now')) NOT NULL, platforms STRING NOT NULL, display_name STRING UNIQUE ON CONFLICT ROLLBACK, rating_mu DOUBLE DEFAULT (1500) NOT NULL, old_rating_phi DOUBLE NOT NULL DEFAULT (350), rating_phi DOUBLE DEFAULT (350) NOT NULL, rating_sigma DOUBLE NOT NULL DEFAULT (0.06), username_pc STRING UNIQUE ON CONFLICT ROLLBACK, username_switch STRING UNIQUE ON CONFLICT ROLLBACK, username_ps4 STRING UNIQUE ON CONFLICT ROLLBACK);

-- Trigger: Report
CREATE TRIGGER Report AFTER INSERT ON matches BEGIN UPDATE players SET rating_mu = new.player1_new_mu, rating_phi = new.player1_new_phi, rating_sigma = new.player1_new_sigma WHERE id = new.player1; UPDATE players SET rating_mu = new.player2_new_mu, rating_phi = new.player2_new_phi, rating_sigma = new.player2_new_sigma WHERE id = new.player2; END;

-- Trigger: Update phi
CREATE TRIGGER "Update phi" AFTER UPDATE OF rating_phi ON players BEGIN UPDATE players SET old_rating_phi = old.rating_phi WHERE rowid = old.rowid; END;

COMMIT TRANSACTION;
PRAGMA foreign_keys = on;
