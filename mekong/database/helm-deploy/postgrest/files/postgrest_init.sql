CREATE ROLE authenticator LOGIN NOINHERIT NOCREATEDB NOCREATEROLE NOSUPERUSER;
CREATE ROLE anonymous NOLOGIN;
CREATE ROLE webuser NOLOGIN;

CREATE USER postgrest WITH PASSWORD '12345678';
GRANT ALL PRIVILEGES ON DATABASE {{ .Values.database.name }} TO postgrest;
GRANT ALL ON SCHEMA public TO postgrest;

GRANT anonymous TO postgrest;

-- setup permissions
create schema basic_auth;
create schema migration;
create schema loco;

-- https://postgrest.org/en/v12/how-tos/sql-user-management.html#sql-user-management
create table
basic_auth.users (
  email    text primary key check ( email ~* '^.+@.+\..+$' ),
  pass     text not null check (length(pass) < 512),
  role     name not null check (length(role) < 512)
);


create table
migration.white_listed_tables (
  table_name    text primary key,
  cron          text not null,
  alias         text
);

GRANT USAGE ON SCHEMA migration TO anonymous;
GRANT SELECT ON ALL TABLES IN SCHEMA migration TO anonymous;

GRANT INSERT, UPDATE, DELETE ON TABLE migration.white_listed_tables TO anonymous;