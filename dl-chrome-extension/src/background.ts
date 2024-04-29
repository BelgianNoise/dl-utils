import { newURLUpdatedMessage } from "./types";

chrome.tabs.onUpdated.addListener(
  (tabId, changeInfo, tab) => {
    console.log('TAB UPDATED', tabId, changeInfo, tab)
    if (changeInfo.url) {
      console.log('URL UPDATED', changeInfo.url)
      chrome.tabs.sendMessage(
        tabId,
        newURLUpdatedMessage(changeInfo.url),
      )
    }
  }
);
