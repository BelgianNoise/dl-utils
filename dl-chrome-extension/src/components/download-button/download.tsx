import { NotificationLevel, addNotification } from "../../notifications/notifications";

export function download() {
  chrome.storage.sync.get(['token', 'url', 'quality'], (data) => {
    const token = data.token;
    const url = data.url;
    const quality = data.quality;

    const fetchUrl = new URL('/queue/add', url);
    console.log('Sending download request', {
      url: fetchUrl.toString(),
      token: token,
      quality: quality,
    });

    fetch(
      fetchUrl.toString(),
      {
        method: 'POST',
        headers: {
          'Authorization': `${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url: window.location.href,
          preferredQualityMatcher: quality,
        }),
      }
    ).then((response: Response) => {
      if (response.status === 201) {
        addNotification({
          level: NotificationLevel.SUCCESS,
          message: `Download successfully added to the queue`,
        });
      } else if (response.status === 409) {
        addNotification({
          level: NotificationLevel.INFO,
          message: `Download already in the queue`,
        });
      } else if (response.status === 401) {
        addNotification({
          level: NotificationLevel.ERROR,
          message: `Failed to add download to the queue (unauthorized)`,
        });
      } else {
        addNotification({
          level: NotificationLevel.ERROR,
          message: `Failed to add download to the queue (check the console for more information)`,
        });
        response.text().then((content) => {
          console.log('Failed to add download to the queue', {
            status: response.status,
            statusText: response.statusText,
            content: content,
          });
        });
      }
    }).catch((error: Error) => {
      addNotification({
        level: NotificationLevel.ERROR,
        message: `Failed to add download to the queue (check the console for more information)`,
      });
      console.error('Failed to add download to the queue', error);
    });
  });
}
