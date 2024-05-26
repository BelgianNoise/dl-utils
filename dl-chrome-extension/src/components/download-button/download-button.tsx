import React from "react";
import "./download-button.css";
import SVGDownload from "../../svg/svg-download";
import { downloadCurrentPage } from "./download";

type DownloadButtonProps = {
  onClick?: (event: React.MouseEvent) => void;
  hideText?: boolean;
};

const DownloadButton = ({
  onClick = downloadCurrentPage,
  hideText = false,
}: DownloadButtonProps) => {
  return (
    <button className={hideText ? 'small-padding' : ''} id="dl-utils-download-button" onClick={onClick}>
      <SVGDownload />
      {!hideText && (
        <span>Download</span>
      )}
    </button>
  );
};

export default DownloadButton;
