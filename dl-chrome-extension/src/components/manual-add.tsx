import React from "react";
import SVGCross from "../svg/svg-cross";
import { download } from "./download-button/download";

const ManualAddDialog = (props: {
  open: boolean;
  onClose: () => void;
}) => {

  const urlInput = React.useRef<HTMLInputElement>(null);
  const filenameInput = React.useRef<HTMLInputElement>(null);

  const addToQueue = () => {
    const url = urlInput.current?.value;
    if (!url) return;
    const filename = filenameInput.current?.value;
    
    // clear inputs
    urlInput.current!.value = '';
    filenameInput.current!.value = '';

    download({ url, filename, notify: false });
    props.onClose();
  }

  return (
    <dialog open={props.open}>
      <h2>Add to queue</h2>
      <div className="input-container">
        <label htmlFor="url">Video or manifest URL</label>
        <input ref={urlInput} type='text' id="url" name="url" placeholder="https://..."/>
      </div>
      <div className="input-container">
        <label htmlFor="filename">filename (optional)</label>
        <input ref={filenameInput} type='text' id="filename" name="filename" placeholder="File.Name.S01E01"/>
      </div>

      <div className='buttons'>
        <button className="primary" onClick={addToQueue}>
          Add to queue
        </button>
        <button onClick={() => props.onClose()}>
          <SVGCross />
          Close
        </button>
      </div>
    </dialog>
  );
};

export default ManualAddDialog;
