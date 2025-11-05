FROM postgis/postgis:18-3.6
RUN apt-get update && apt-get upgrade -y && apt install -y \
    sudo screen locate libapache2-mod-tile renderd \
    git tar unzip wget bzip2 lua5.1 \
    mapnik-utils python3-mapnik python3-psycopg2 \
    python3-yaml gdal-bin npm node-carto \
    osm2pgsql net-tools curl nik4
COPY init.sh /docker-entrypoint-initdb.d/init-user-db.sh
COPY test.py /test.py
RUN wget https://download.geofabrik.de/europe/united-kingdom/england/merseyside-latest.osm.pbf
WORKDIR "/src"
RUN git clone https://github.com/gravitystorm/openstreetmap-carto
WORKDIR "/src/openstreetmap-carto"
RUN git pull --all
RUN git switch --detach v5.9.0
RUN npm install -g carto
RUN carto project.mml > mapnik.xml
