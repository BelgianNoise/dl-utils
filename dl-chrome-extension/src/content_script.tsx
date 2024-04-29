import { createRoot } from "react-dom/client";
import React from "react";
import DownloadButton from "./components/download-button";
import { MessageType } from "./types";

console.log('RUNNING CONTENT SCRIPT')

const elementId = "dl-utils-download-button";

function addButton(): void {
  if (document.getElementById(elementId)) return;
  const el = document.querySelector('sso-login');
  if (!el) return;
  const newDiv = document.createElement("div");
  newDiv.id = elementId;
  el.parentNode!.insertBefore(newDiv, el);
  const root = createRoot(newDiv);
  root.render(
    <React.StrictMode>
      <DownloadButton />
    </React.StrictMode>
  );
}

function showButton(): void {
  const el = document.getElementById(elementId);
  if (el) {
    el.style.display = "block";
  }
}

function hideButton(): void {
  const el = document.getElementById(elementId);
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

addButton();
shouldIStayOrShouldIGo(window.location.href);

chrome.runtime.onMessage.addListener(
  (message, sender, sendResponse) => {
    if (message?.type === MessageType.URL_UPDATED) {
      shouldIStayOrShouldIGo(message.url);
    }
});
