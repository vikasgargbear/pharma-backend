-- Set search path for the application user
-- This ensures the application can find tables in all schemas

-- Set the search path for the current session
SET search_path TO master, parties, inventory, sales, procurement, financial, gst, compliance, system_config, analytics, public;

-- Make it permanent for the database user
ALTER ROLE postgres SET search_path TO master, parties, inventory, sales, procurement, financial, gst, compliance, system_config, analytics, public;

-- Grant necessary permissions
GRANT USAGE ON SCHEMA master TO postgres;
GRANT USAGE ON SCHEMA parties TO postgres;
GRANT USAGE ON SCHEMA inventory TO postgres;
GRANT USAGE ON SCHEMA sales TO postgres;
GRANT USAGE ON SCHEMA procurement TO postgres;
GRANT USAGE ON SCHEMA financial TO postgres;
GRANT USAGE ON SCHEMA gst TO postgres;
GRANT USAGE ON SCHEMA compliance TO postgres;
GRANT USAGE ON SCHEMA system_config TO postgres;
GRANT USAGE ON SCHEMA analytics TO postgres;

-- Grant table permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA master TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA parties TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA inventory TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA sales TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA procurement TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA financial TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA gst TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA compliance TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA system_config TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA analytics TO postgres;

-- Grant sequence permissions
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA master TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA parties TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA inventory TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA sales TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA procurement TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA financial TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA gst TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA compliance TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA system_config TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA analytics TO postgres;