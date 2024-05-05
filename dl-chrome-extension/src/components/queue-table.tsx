import React from "react";
import { DLRequest } from "../models/dl-request";
import PlatformChip from "./platform-chip";

const QueueList = (props: {
  requests: DLRequest[];
}) => {
  return (
    <div className="queue-list-container">
      <div className="queue-list-item head">
        <span>Platform</span>
        <span>URL</span>
        <span>Filename</span>
        <span>Quality</span>
      </div>

      {props.requests.map((request) => {
        return (
          <div key={request.id} className="queue-list-item">
            <PlatformChip platform={request.platform} />
            <a
              href={request.videoPageOrManifestUrl}
              title={request.videoPageOrManifestUrl}
              target="_blank"
              rel="noopener noreferrer"
            >{request.videoPageOrManifestUrl}</a>
            <span title={request.outputFilename}>{request.outputFilename || 'auto'}</span>
            <span title={request.preferredQualityMatcher}>{request.preferredQualityMatcher || 'best'}</span>
          </div>
        );
      })}

    </div>
  );
};

export default QueueList;
