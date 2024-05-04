import React from "react";
import "./download-button.css";
import SVGDownload from "../../svg/svg-download";
import { downloadCurrentPage } from "./download";

const DownloadButton = () => {
  return (
    <button id="dl-utils-download-button" onClick={downloadCurrentPage}>
      <SVGDownload />
      <span>Download</span>
    </button>
  );
};

export default DownloadButton;
