# Use an official Python runtime as the base image
FROM python:3.12-slim

LABEL org.opencontainers.image.source https://github.com/BelgianNoise/dl-utils

VOLUME /downloads
VOLUME /storage_states
VOLUME /cdm

ENV DOWNLOADS_FOLDER=/downloads
ENV STORAGE_STATES_FOLDER=/storage_states
ENV CDM_FILE_PATH=/cdm/cdm.wvd

ENV HEADLESS=true
ENV POSTGRES_USERNAME=
ENV POSTGRES_PASSWORD=
ENV POSTGRES_HOST=
ENV POSTGRES_PORT=
ENV POSTGRES_DATABASE=

ENV AUTH_VRTMAX_EMAIL=
ENV AUTH_VRTMAX_PASSWORD=
ENV AUTH_GOPLAY_EMAIL=
ENV AUTH_GOPLAY_PASSWORD=

ENV PUID=6969
ENV PGID=6969

WORKDIR /app

COPY . /app

# Make all binaries executable
RUN chmod +x binaries/linux/*
# Move binaries to /bin
RUN mv binaries/linux/* /bin/
# Move entry.sh to /bin
RUN chmod +x entry.sh
RUN mv entry.sh /bin/

# install ffmpeg and mkvmerge
RUN apt-get update
RUN apt-get install -y ffmpeg mkvtoolnix

# Install python packages + playwright install
RUN pip install --no-cache-dir -r requirements.txt
# install playwright dependencies
RUN apt-get install -y \
  libnss3 \
  libatk-bridge2.0-0 \
  libx11-xcb1 \
  libxcomposite1 \
  libxdamage1 \
  libxrandr2 \
  libxss1 \
  libxtst6 \
  libgbm1 \
  libasound2 \
  libgtk-3-0
# RUN apt-get install -y \
#   libsoup2.4-1 \
#   gstreamer1.0-plugins-base \
#   libatomic1 \
#   libxslt1.1 \
#   libwoff1 \
#   libevent-2.1-6 \
#   libharfbuzz-icu0 \
#   gstreamer1.0-plugins-base \
#   gstreamer1.0-plugins-good \
#   libwebpdemux2 \
#   enchant \
#   libsecret-1-0 \
#   hyphen-en-us \
#   libgles2

RUN apt-get install -y sudo gosu
RUN rm -rf /var/lib/apt/lists/*

ENTRYPOINT [ "entry.sh" ]

CMD [ "python", "start.py" ]
