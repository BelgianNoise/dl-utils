import React from "react";
import { DLRequest } from "../models/dl-request";
import Loader from "./loader";
import { DLRequestStatus } from "../models/dl-request-status";
import QueueList from "./queue-table";
import "./queue.css";

const Queue = () => {

  const [pending, setPending] = React.useState<DLRequest[]>([]);
  const [inProgress, setInProgress] = React.useState<DLRequest[]>([]);
  const [completed, setCompleted] = React.useState<DLRequest[]>([]);
  const [failed, setFailed] = React.useState<DLRequest[]>([]);

  const [loading, setLoading] = React.useState(true);
  // Just a simple error message for now
  const [error, setError] = React.useState<string | undefined>(undefined);

  function fetchData() {
    chrome.storage.sync.get(['token', 'url'], (data) => {
      const reqURL = new URL('/queue', data.url || 'http://localhost:8282');
      fetch(
        reqURL.toString(),
        {
          method: 'POST',
          headers: {
            'Authorization': data.token,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            list: [DLRequestStatus.PENDING, DLRequestStatus.IN_PROGRESS, DLRequestStatus.COMPLETED, DLRequestStatus.FAILED],
          }),
        }
      )
        .then((response) => response.json())
        .then((data) => {
          setPending(data[DLRequestStatus.PENDING]);
          setInProgress(data[DLRequestStatus.IN_PROGRESS]);
          setCompleted(data[DLRequestStatus.COMPLETED]);
          setFailed(data[DLRequestStatus.FAILED]);
          setLoading(false);
          setError(undefined);
        })
        .catch((error) => {
          console.error('Error:', error);
          setLoading(false);
          setError(error.toString());
        });
    })
  }

  // Every 30 seconds, fetch the data from the server
  React.useEffect(() => {
    fetchData(); // Fetch data on load
    const interval = setInterval(() => fetchData(), 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="queue-container">

      {error ? <div>{error}</div> : <>
        {loading ? <Loader /> : (<>
          <div className="table-container">
            <h2 className="chip in-progress">
              <span>In Progress</span>
              <span>({inProgress.length})</span>
            </h2>
            {inProgress.length > 0 && (<QueueList requests={inProgress} />)}
          </div>

          <div className="table-container">
            <h2 className="chip pending">
              <span>Pending</span>
              <span>({pending.length})</span>
            </h2>
            {pending.length > 0 && (<QueueList requests={pending} />)}
          </div>

          <div className="table-container">
            <h2 className="chip failed">
              <span>Failed</span>
              <span>({failed.length})</span>
            </h2>
            {failed.length > 0 && (<QueueList requests={failed} />)}
          </div>

          <div className="table-container">
            <h2 className="chip completed">
              <span>Completed</span>
              <span>({completed.length})</span>
            </h2>
            {completed.length > 0 && (<QueueList requests={completed} />)}
          </div>
        </>)}
      </>}

    </div>
  );
};

export default Queue;
