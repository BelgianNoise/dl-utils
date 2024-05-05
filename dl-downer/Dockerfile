# Use an official Python runtime as the base image
FROM python:3.12

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

COPY . .

# Make all binaries executable
RUN chmod +x /binaries/linux/*
# Move binaries to /bin
RUN mv /binaries/linux/* /bin/

# install ffmpeg and mkvmerge
RUN apt-get update
RUN apt-get install -y ffmpeg mkvtoolnix

# Install python packages + playwright install
RUN pip install --no-cache-dir -r requirements.txt
# RUN pip install playwright==@1.42.0
RUN playwright install --with-deps

CMD [ "python", "start.py" ]
