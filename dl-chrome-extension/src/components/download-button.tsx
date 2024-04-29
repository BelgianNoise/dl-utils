import React from "react";
import "./download-button.css";
import DownloadSVG from "./download-svg";

const DownloadButton = () => {
  function onClick() {
    fetch(
      'http://localhost:8282/queue/add',
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url: window.location.href,
          preferredQualityMatcher: '720',
        }),
      }
    ).then((response: Response) => {
      console.log(response);
    }).catch((error: Error) => {
      console.error(error);
    });
  }

  return (
    <button onClick={onClick}>
      <DownloadSVG />
      <span>Download</span>
    </button>
  );
};

export default DownloadButton;
