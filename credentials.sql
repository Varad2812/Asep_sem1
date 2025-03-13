-- Create credentials table
CREATE TABLE IF NOT EXISTS credentials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_credentials_username ON credentials(username);
CREATE INDEX IF NOT EXISTS idx_credentials_email ON credentials(email);

-- Create trigger to update timestamp
CREATE TRIGGER IF NOT EXISTS update_credentials_timestamp 
AFTER UPDATE ON credentials
BEGIN
    UPDATE credentials SET created_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END; 