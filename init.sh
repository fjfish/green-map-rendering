#!/usr/bin/env bash
set -x

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
	CREATE USER root;
	CREATE DATABASE gis WITH OWNER "root" ENCODING 'UTF8';
	GRANT ALL PRIVILEGES ON DATABASE gis TO root;
EOSQL

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "gis" <<-EOSQL
	CREATE EXTENSION postgis;
	CREATE EXTENSION hstore;
	ALTER TABLE geometry_columns OWNER TO root;
	ALTER TABLE spatial_ref_sys OWNER TO root;
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

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "gis" <<-EOSQL
	ALTER TABLE public.external_data OWNER TO root;
	ALTER TABLE public.icesheet_outlines OWNER TO root;
	ALTER TABLE public.icesheet_polygons OWNER TO root;
	ALTER TABLE public.ne_110m_admin_0_boundary_lines_land OWNER TO root;
	ALTER TABLE public.osm2pgsql_properties OWNER TO root;
	ALTER TABLE public.planet_osm_line OWNER TO root;
	ALTER TABLE public.planet_osm_nodes OWNER TO root;
	ALTER TABLE public.planet_osm_point OWNER TO root;
	ALTER TABLE public.planet_osm_polygon OWNER TO root;
	ALTER TABLE public.planet_osm_rels OWNER TO root;
	ALTER TABLE public.planet_osm_roads OWNER TO root;
	ALTER TABLE public.planet_osm_ways OWNER TO root;
	ALTER TABLE public.simplified_water_polygons OWNER TO root;
	ALTER TABLE public.spatial_ref_sys OWNER TO root;
	ALTER TABLE public.water_polygons OWNER TO root;
EOSQL

echo Done init
