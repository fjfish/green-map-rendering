FROM postgis/postgis:18-3.6
RUN apt-get update && apt-get upgrade -y && apt install -y \
    sudo screen locate libapache2-mod-tile renderd \
    git tar unzip wget bzip2 lua5.1 \
    mapnik-utils python3-mapnik python3-psycopg2 \
    python3-yaml gdal-bin npm node-carto \
    osm2pgsql net-tools curl nik4 python3-pil

RUN wget https://download.geofabrik.de/europe/united-kingdom/england/merseyside-latest.osm.pbf
WORKDIR "/src"
RUN git clone https://github.com/gravitystorm/openstreetmap-carto
WORKDIR "/src/openstreetmap-carto"
RUN git pull --all
RUN git switch --detach v5.9.0
RUN npm install -g carto
RUN carto project.mml > mapnik.xml
RUN sed -i "s/'https:\/\/fonts.google.com\/download?family=Noto%20Emoji'/https:\/\/archive.org\/download\/noto-emoji\/Noto_Emoji.zip/" ./scripts/get-fonts.sh
RUN ./scripts/get-fonts.sh
RUN mkdir data
RUN chmod ugo+rw data

COPY init.sh /docker-entrypoint-initdb.d/init-user-db.sh
WORKDIR "/"
COPY *.otf base.xml *.csv getmaps.py /


#FIXME PostGres database needs to start running and init.sh run before the rest of the commands

# FIXME User should be able to specify the google drive ID and the ward name in the next line
#RUN python3 getmaps.py 1Dpz_dnouwZWP4I7i-Uu9EYcNk-jKt6w Oxton 

# FIXME An Oxton directory then wants to be copied back to the users computer

