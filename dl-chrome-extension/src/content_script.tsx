import { createRoot } from "react-dom/client";
import React from "react";
import DownloadButton from "./components/download-button/download-button";
import { MessageType } from "./types";
import { addButtonsGoPlay } from "./page-buttons/goplay";
import { addButtonsVTMGO } from "./page-buttons/vtmgo";
import { addButtonsVRTMAX } from "./page-buttons/vrtmax";

console.log('RUNNING CONTENT SCRIPT')

export const buttonElementId = "dl-utils-download-button";
export const notificationContainerElementId = "dl-utils-notification-container";

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

function handleURLUpdated() {
  const url = window.location.href;
  console.log('URL updated:', url);
  if (url.match('vrt.be/vrtmax')) {
    addButtonsVRTMAX(url);
  } else if (url.match('goplay.be')) {
    addButtonsGoPlay(url);
  } else if (url.match('vtmgo.be')) {
    addButtonsVTMGO(url);
  } else if (url.match(/youtube\.com\/watch/)) {
    // YOUTUBE
    addButtonYouTube();
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
