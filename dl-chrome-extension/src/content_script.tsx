import { createRoot } from "react-dom/client";
import React from "react";
import DownloadButton from "./components/download-button/download-button";
import { Message, MessageType, URLUpdatedMessage } from "./types";

console.log('RUNNING CONTENT SCRIPT')

export const buttonElementId = "dl-utils-download-button";
export const notificationContainerElementId = "dl-utils-notification-container";

function addButton(): void {
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
}

function showButton(): void {
  const el = document.getElementById(buttonElementId);
  if (el) {
    el.style.display = "block";
  }
}

function hideButton(): void {
  const el = document.getElementById(buttonElementId);
  if (el) {
    el.style.display = "none";
  }
}

function shouldIStayOrShouldIGo(
  url: string,
) {
  if (url.match(/\/a-z\/([\w-]*?)\/([\w-]*?)\/([\w-]*?)\/?$/)) {
    showButton();
  } else {
    hideButton();
  }
}

function handleURLUpdatedMessage(message: URLUpdatedMessage) {
  shouldIStayOrShouldIGo(message.url);
}

function addNotificationContainer(): void {
  if (document.getElementById(notificationContainerElementId)) return;
  const html = document.querySelector('html');
  if (!html) return;
  const newDiv = document.createElement("div");
  newDiv.id = notificationContainerElementId;
  html.append(newDiv);
}

addButton();
console.log('added button to the page')
addNotificationContainer();
console.log('added notification container to the page')
shouldIStayOrShouldIGo(window.location.href);


chrome.runtime.onMessage.addListener(
  (message: Message, sender, sendResponse) => {
    if (message && message.type){ // this kinda checks if the typing is correct
      if (message.type === MessageType.URL_UPDATED) {
        handleURLUpdatedMessage(message as URLUpdatedMessage)
      }
    }
});
