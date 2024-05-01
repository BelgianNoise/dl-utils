import React from 'react';
import { createRoot } from "react-dom/client";
import { notificationContainerElementId } from '../content_script';
import NotificationComponent from './notification';

export enum NotificationLevel {
  SUCCESS = 'SUCCESS',
  INFO = 'INFO',
  ERROR = 'ERROR',
}

export interface Notification {
  level: NotificationLevel;
  message: string;
  timeout?: number;
}

export function addNotification(notif: Notification) {
  const container = document.getElementById(notificationContainerElementId);
  if (!container) {
    console.error('Notification container not found');
    return;
  };
  const newDiv = document.createElement("div");
  container.prepend(newDiv);
  const root = createRoot(newDiv);
  root.render(
    <React.StrictMode>
      <NotificationComponent notification={notif} />
    </React.StrictMode>
  );
  setTimeout(() => {
    newDiv.remove();
  }, notif.timeout || 5000);
}
