-- Grant CREATE permission on the schema to allow checkpointer to create its tables
-- Run this against your database (e.g., using a SQL client or pgadmin)

GRANT CREATE ON SCHEMA conthunt TO conthunt_service;
