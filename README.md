# dl-utils

This project aims to aid me in downloading videos from certain content providers.
The downloaded files are strictly for personal use only without any intend to break user agreements.
The focus lays not on illegally acquiring video content, content that is stored behind a paywall is only to be consumed when actively paying for that service.

This project consists of 4 subprojects that can mostly be used on their own, this is done to reduce debugging complexity and maximize availability.

## [dl-downer](dl-downer/)

Python script that monitors a database table for new download requests, if a new request is found the script does its best to download (and decrypt) the video (using a local CDM).

## [dl-queue](dl-queue/)

Express.js server exposing 2 endpoints:
1. `POST /queue/add` - to add download requests to the queue (authenticated)
2. `GET /queue` - get json representation of the current download queue

In the background, this server will emulate a browser to retrieve the required parameters to handle a request.

## [dl-scraper](dl-scraper/)

A webcrawler/-scraper written in TypeScript using puppeteer to scrape content provider's websites and/or APIs for available content.
Data is stored in a PostgreSQL database to be used in other places.

## [dl-viewer](dl-viewer/)

Next.js server hosted on Vercel using DaisyUI components. This service provives a frontend for all data retrieved and/or handled by the other services listed in this README file.
- search content retrieved by `dl-scraper`
- send download requests to `dl-queue`
- show download queue from `dl-queue`
