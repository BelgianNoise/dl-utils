import React from "react";
import "./download-button.css";
import SVGDownload from "../../svg/svg-download";
import { download } from "./download";

const DownloadButton = () => {
  return (
    <button id="dl-utils-download-button" onClick={download}>
      <SVGDownload />
      <span>Download</span>
    </button>
  );
};

export default DownloadButton;
