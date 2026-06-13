-- NOTE: Schema changes should be managed via Alembic migrations.
-- This script is kept for initial development bootstrapping only.
CREATE TABLE IF NOT EXISTS books (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(255) NOT NULL,
    isbn VARCHAR(20) NOT NULL
);
