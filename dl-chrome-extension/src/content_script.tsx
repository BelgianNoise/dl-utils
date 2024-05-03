import { createRoot } from "react-dom/client";
import React from "react";
import DownloadButton from "./components/download-button/download-button";
import { MessageType } from "./types";

console.log('RUNNING CONTENT SCRIPT')

export const buttonElementId = "dl-utils-download-button";
export const notificationContainerElementId = "dl-utils-notification-container";

function addButtonVRTMAX(): void {
  console.log('adding button to VRT MAX')
  if (document.getElementById(buttonElementId)) return;
  const el = document.querySelector('sso-login');
  if (!el) return;
  const newDiv = document.createElement("div");
  newDiv.id = buttonElementId;
  el.parentNode!.insertBefore(newDiv, el);
  const root = createRoot(newDiv);
  root.render(
    <React.StrictMode>
      <DownloadButton />
    </React.StrictMode>
  );
  console.log('added button to VRT MAX')
}

function addButtonGoPlaySeries(): void {
  console.log('adding button to GoPlay')
  if (document.getElementById(buttonElementId)) return;
  const el = document.querySelector('div.sbs-video__info');
  if (!el) return;
  (el as HTMLDivElement).style.position = 'relative';
  const newDiv = document.createElement("div");
  newDiv.id = buttonElementId;
  newDiv.style.position = 'absolute';
  newDiv.style.right = '20px';
  newDiv.style.top = '10px';
  el.append(newDiv);
  const root = createRoot(newDiv);
  root.render(
    <React.StrictMode>
      <DownloadButton />
    </React.StrictMode>
  );
  console.log('added button to GoPlay')
}

function addButtonGoPlayMovie(): void {
  console.log('adding button to GoPlay')
  if (document.getElementById(buttonElementId)) return;
  const el = document.querySelector('main.l-content > article');
  if (!el) return;
  (el as HTMLDivElement).style.position = 'relative';
  const newDiv = document.createElement("div");
  newDiv.id = buttonElementId;
  newDiv.style.position = 'absolute';
  newDiv.style.left = '50%';
  newDiv.style.top = '0';
  newDiv.style.transform = 'translateX(-50%) translateY(-50%)';
  el.append(newDiv);
  const root = createRoot(newDiv);
  root.render(
    <React.StrictMode>
      <DownloadButton />
    </React.StrictMode>
  );
  console.log('added button to GoPlay')
}

function addButtonYouTube(): void {
  console.log('adding button to YouTube')
  if (document.getElementById(buttonElementId)) return;
  const el: HTMLDivElement = document.querySelector(
    'div#above-the-fold div#title',
  ) as HTMLDivElement;
  if (!el) return;
  const newDiv = document.createElement("div");
  newDiv.id = buttonElementId;
  el.style.display = 'flex';
  el.style.justifyContent = 'space-between';
  el.style.alignItems = 'center';
  el.style.gap = '20px';
  el.append(newDiv);
  const root = createRoot(newDiv);
  root.render(
    <React.StrictMode>
      <DownloadButton />
    </React.StrictMode>
  );
  console.log('added button to YouTube')
}

function removeButton(): void {
  const el = document.getElementById(buttonElementId);
  if (el) {
    el.remove();
  }
}

function handleURLUpdated() {
  const url = window.location.href;
  console.log('URL updated:', url);
  if (url.match(/\/a-z\/([\w-]+?)\/([\w-]+?)\/([\w-]+?)\/?$/)) {
    // VRT MAX
    addButtonVRTMAX();
  } else if (url.match(/\/video\/[\w-]+?\/[\w-]+?\/[\w-]+?(#autoplay)?$/)) {
    // GOPLAY SERIES
    addButtonGoPlaySeries();
  } else if (url.match(/\/video\/([\w-]+?\/[\w-]+?\/)?[\w-]+?(#autoplay)?$/)) {
    // GOPLAY MOVIE
    addButtonGoPlayMovie();
  } else if (url.match(/youtube\.com\/watch/)) {
    // YOUTUBE
    addButtonYouTube();
  } else {
    removeButton();
  }
}

function addNotificationContainer(): void {
  if (document.getElementById(notificationContainerElementId)) return;
  const html = document.querySelector('html');
  if (!html) return;
  const newDiv = document.createElement("div");
  newDiv.id = notificationContainerElementId;
  html.append(newDiv);
}


addNotificationContainer();
console.log('added notification container to the page')
// Fake a URL update at init
handleURLUpdated();
console.log('handled URL update at init')

chrome.runtime.onMessage.addListener(
  (message, sender, sendResponse) => {
    console.log('message', message)
    if (message === MessageType.URL_UPDATED) {
      handleURLUpdated()
    }
});

console.log('CONTENT SCRIPT LOADED')
