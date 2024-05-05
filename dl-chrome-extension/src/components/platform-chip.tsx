import React from "react";
import { DLRequestPlatform } from "../models/dl-request-platform";
import "./platform-chip.css";

const PlatformChip = (props: {
  platform: DLRequestPlatform;
}) => {
  return (
    <span className={`platform-chip ${props.platform}`}>
      {props.platform.split('_')[0]}
    </span>
  );
};

export default PlatformChip;
