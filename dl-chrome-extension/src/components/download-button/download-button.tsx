import React from "react";
import "./download-button.css";
import SVGDownload from "../../svg/svg-download";
import { downloadCurrentPage } from "./download";

type DownloadButtonProps = {
  onClick?: (event: React.MouseEvent) => void;
  hideText?: boolean;
  smallPadding?: boolean;
  text?: string;
  styles?: React.CSSProperties;
};

const DownloadButton = ({
  onClick = downloadCurrentPage,
  hideText = false,
  smallPadding = false,
  text = "Download",
  styles = {},
}: DownloadButtonProps) => {

  const onClickWithoutPropagation = (event: React.MouseEvent) => {
    event.stopPropagation();
    event.preventDefault();
    onClick(event);
  }

  return (
    <button
      className={`dl-utils-download-button ${smallPadding ? 'small-padding' : ''}`}
      onClick={onClickWithoutPropagation}
      style={styles}
    >
      <SVGDownload />
      {!hideText && (
        <span>{text}</span>
      )}
    </button>
  );
};

export default DownloadButton;
