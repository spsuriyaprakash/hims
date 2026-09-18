#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE USER hims WITH PASSWORD 'hims';
    CREATE DATABASE hims OWNER hims;
    GRANT ALL PRIVILEGES ON DATABASE hims TO hims;

    CREATE USER keycloak WITH PASSWORD 'keycloak';
    CREATE DATABASE keycloak OWNER keycloak;
    GRANT ALL PRIVILEGES ON DATABASE keycloak TO keycloak;
EOSQL

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname hims <<-EOSQL
    GRANT ALL ON SCHEMA public TO hims;
    ALTER SCHEMA public OWNER TO hims;
EOSQL

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname keycloak <<-EOSQL
    GRANT ALL ON SCHEMA public TO keycloak;
    ALTER SCHEMA public OWNER TO keycloak;
EOSQL
