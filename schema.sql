-- Whitehat Challenge A — Database schema
-- Single table: products
--
-- Design notes:
--   - price stored as INTEGER (cents) to avoid floating-point rounding errors
--   - CHECK constraints act as the last line of defense (defense in depth):
--     even if Flask validation is bypassed, the DB itself rejects bad data
--   - created_at provides a basic audit trail

CREATE TABLE IF NOT EXISTS products (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL
                        CHECK (length(name) > 0 AND length(name) <= 200),
    price       INTEGER NOT NULL
                        CHECK (price >= 0),
    created_at  TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Index on name to speed up the search page queries (step 5)
CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);
