# dl-utils

This project aims to aid me in downloading videos from certain content providers.
The downloaded files are strictly for personal use only without any intend to break user agreements.
The focus lies not on illegally acquiring or consuming video content, content is only to be consumed in accordance to the platform's terms of service.

This project consists of 3 subprojects that can mostly be used on their own, this is done to reduce debugging complexity and maximize availability.

Currently supported content providers:

| Content Provider | dl-downer | dl-queue | dl-chrome-extension |
|----------------------|-----------|----------|---------------------|
| VRT MAX              |    ✔️     |    ✔️   |         ✔️          |
| GoPlay               |    ✔️     |    ✔️   |         ✔️          |
| VTM GO               |    ✔️     |    ✔️   |         ✔️          |
| Streamz              |    ✔️     |    ✔️   |         ✔️          |
| YouTube              |    ✔️     |    ✔️   |         ✔️          |
| Plain manifest url   |    ✔️     |    ✔️   |         ✔️          |
| NPO Start            |    ❌     |    ❌   |         ❌          |

## [dl-downer](dl-downer/)

Python script that monitors a database table for new download requests, if a new request is found the script does its best to download (and decrypt) the video (using a local CDM).

### Troubleshooting

If you encouter issues with the login for VTM GO, you might need to create a storage state by turning off `HEADLESS` mode via the env variable. (You might need to do this on another machine as non-headless might not be supported in the current environment)
DPG Media's login is pretty good at detecting bots, but once you are logged in, they don't seem to care that much anymore.
(Keep in mind that your refresh token will expire after a while, so you might need to repeat this process every now and then if you don't use the downloader for a while)

## [dl-queue](dl-queue/)

Express.js server exposing 2 endpoints:

1. `POST /queue/add` - to add download requests to the queue
2. `POST /queue` - get json representation of the current download queue

This service acts as a middleman between the chrome extension and the downloader, it stores download requests in a PostgreSQL database for the downloader to pick up.
This makes it so that the chrome extension can be used on any device without exposing any sensitive information and keeps the downloader from being exposed to the internet.

Currently deployed on <https://dl-queue.nasaj.be/> (GCP Cloud Run). Don't bother sending requests cause you will just get a 403 without the right `authorization` header.

## [dl-chrome-extension](dl-chrome-extension/)

This chrome extension adds a download button to all supported websites, when clicked it sends a download request to the queue service.
It also shows an overview of all the download requests in the queue, already completed or failed.

