import React from "react";
import { Notification } from "./notifications";
import "./notification.css";

const NotificationComponent = (props: {
  notification: Notification;
}) => {


  return (
    <div className={`notification ${props.notification.level.toLowerCase()}`}>
      <span>{props.notification.message}</span>
    </div>
  );
};

export default NotificationComponent;
