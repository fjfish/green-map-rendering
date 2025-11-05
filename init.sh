#!/usr/bin/env bash
set -x

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
	CREATE USER _renderd;
	CREATE DATABASE gis WITH OWNER "_renderd" ENCODING 'UTF8';
	GRANT ALL PRIVILEGES ON DATABASE gis TO _renderd;
EOSQL

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "gis" <<-EOSQL
	CREATE EXTENSION postgis;
	CREATE EXTENSION hstore;
	ALTER TABLE geometry_columns OWNER TO _renderd;
	ALTER TABLE spatial_ref_sys OWNER TO _renderd;
EOSQL

osm2pgsql -d gis --create --slim  -G --hstore \
    --tag-transform-script \
        /src/openstreetmap-carto/openstreetmap-carto.lua \
    -C 2500 --number-processes 1 \
    -S /src/openstreetmap-carto/openstreetmap-carto.style \
    /merseyside-latest.osm.pbf

#Does the below need to be run by user _renderd?

cd /src/openstreetmap-carto
psql -d gis -f indexes.sql
psql -d gis -f functions.sql
#sudo chown _renderd data
./scripts/get-external-data.py

echo Done init
