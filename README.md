# dl-utils

This project aims to aid me in downloading videos from certain content providers.
The downloaded files are strictly for personal use only without any intend to break user agreements.
The focus lays not on illegally acquiring video content, content that is stored behind a paywall is only to be consumed when actively paying for that service.

This project consists of 4 subprojects that can mostly be used on their own, this is done to reduce debugging complexity and maximize availability.

## dl-downer

## dl-queue

## dl-scraper

A webcrawler/-scraper written in TypeScript using puppeteer to scrape content provider's websites and/or APIs.
Data is stored in a PostgreSQL database to be used in other places.

## dl-viewer
