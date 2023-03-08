DROP TABLE IF EXISTS staff;
CREATE TABLE staff (
    'id' INT PRIMARY KEY NOT NULL,
    'totem' TEXT NOT NULL,
    'nom' TEXT NOT NULL,
    'image' BLOB NOT NULL,
    'description' TEXT NOT NULL,
);