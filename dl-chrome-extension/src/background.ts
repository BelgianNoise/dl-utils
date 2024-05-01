import { MessageType } from "./types";

chrome.tabs.onUpdated.addListener(
  (tabId, changeInfo, tab) => {
    console.log('TAB UPDATED', tabId, changeInfo)
    // This ends up sending messages to a tab that is
    // not ready to receive them yet. So let's not.
    // if (changeInfo.url) {
    //   console.log('URL UPDATED', changeInfo.url)
    //   chrome.tabs.sendMessage(tabId, MessageType.URL_UPDATED);
    // }
    if (changeInfo.status === 'complete') {
      console.log('TAB LOADED', tabId)
      chrome.tabs.sendMessage(tabId, MessageType.URL_UPDATED);
    }
  }
);
