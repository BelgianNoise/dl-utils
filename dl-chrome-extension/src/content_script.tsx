import { MessageType } from "./types";
import { addButtonsGoPlay } from "./page-buttons/goplay";
import { addButtonsVTMGO } from "./page-buttons/vtmgo";
import { addButtonsStreamz } from "./page-buttons/streamz";
import { addButtonsVRTMAX } from "./page-buttons/vrtmax";
import { addButtonYouTube } from "./page-buttons/youtube";

console.log('RUNNING CONTENT SCRIPT')

export const buttonElementId = "dl-utils-download-button";
export const notificationContainerElementId = "dl-utils-notification-container";

const loopingIntervals: NodeJS.Timer[] = [];

function clearAllIntervals() {
  const firstElement = loopingIntervals.shift();
  if (firstElement) {
    clearInterval(firstElement);
    clearAllIntervals();
  }
}
export function addLoopingInterval(fn: () => void, timeout = 1000) {
  const interval = setInterval(fn, timeout);
  loopingIntervals.push(interval);
}

function handleURLUpdated() {
  const url = window.location.href;
  console.log('URL updated:', url);
  clearAllIntervals();

  if (url.match('vrt.be/vrtmax')) {
    addButtonsVRTMAX(url);
  } else if (url.match('goplay.be')) {
    addButtonsGoPlay(url);
  } else if (url.match('vtmgo.be')) {
    addButtonsVTMGO(url);
  } else if (url.match('streamz.be')) {
    addButtonsStreamz(url);
  } else if (url.match(/youtube\.com\/watch/)) {
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
