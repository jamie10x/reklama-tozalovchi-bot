-- Create PostgreSQL roles for the SecAdmin system
-- Run as a superuser: psql -U postgres -d adcleaner -f scripts/create_roles.sql

-- Bot role — minimal permissions on public schema only
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'adcleaner_bot') THEN
        CREATE ROLE adcleaner_bot WITH LOGIN PASSWORD 'change_me';
    END IF;
END
$$;

GRANT CONNECT ON DATABASE adcleaner TO adcleaner_bot;

-- Grant usage and CRUD on main (public) tables
GRANT USAGE ON SCHEMA public TO adcleaner_bot;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO adcleaner_bot;

-- SecAdmin API role — full access to secadmin schema
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'secadmin_api') THEN
        CREATE ROLE secadmin_api WITH LOGIN PASSWORD 'change_me';
    END IF;
END
$$;

GRANT CONNECT ON DATABASE adcleaner TO secadmin_api;
GRANT USAGE ON SCHEMA secadmin TO secadmin_api;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA secadmin TO secadmin_api;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA secadmin TO secadmin_api;

-- Migration role — full DDL access to both schemas
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'secadmin_migrations') THEN
        CREATE ROLE secadmin_migrations WITH LOGIN PASSWORD 'change_me';
    END IF;
END
$$;

GRANT CONNECT ON DATABASE adcleaner TO secadmin_migrations;
GRANT USAGE, CREATE ON SCHEMA public TO secadmin_migrations;
GRANT USAGE, CREATE ON SCHEMA secadmin TO secadmin_migrations;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO secadmin_migrations;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA secadmin TO secadmin_migrations;

-- Read-only role for reporting / analytics
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'secadmin_reader') THEN
        CREATE ROLE secadmin_reader WITH LOGIN PASSWORD 'change_me';
    END IF;
END
$$;

GRANT CONNECT ON DATABASE adcleaner TO secadmin_reader;
GRANT USAGE ON SCHEMA secadmin TO secadmin_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA secadmin TO secadmin_reader;
