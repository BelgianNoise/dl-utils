import React from "react";
import { createRoot } from "react-dom/client";
import SVGSettings from "../svg/svg-settings";
import "./popup.css";
import "./button.css";
import "./dialog.css";
import "./input.css";

const Popup = () => {

  const [showSettings, setShowSettings] = React.useState(false);

  return (
    <div className='container'>
      <div className='header'>
        <h1>Queue</h1>
        <button onClick={() => setShowSettings(true)} disabled={showSettings}>
          <SVGSettings />
        </button>
      </div>

      <dialog open={showSettings}>
        <h2>Settings</h2>
        <div className="input-container">
          <label htmlFor="token">Auth token</label>
          <input type='text' id="token" name="token" placeholder="ey..."/>
        </div>
        <div className="input-container">
          <label htmlFor="quality">Preferred quality</label>
          <select id="quality" name="quality">
            <option value="best">best</option>
            <option value="1080">1080p</option>
            <option value="720">720p</option>
            <option value="540">540p</option>
            <option value="480">480p</option>
          </select>
        </div>
        <div className='buttons'>
          <button onClick={() => setShowSettings(false)}>
            Close
          </button>
        </div>
      </dialog>
    </div>
  );
};

export default Popup;

const root = document.getElementById("root")
if (root) {
  createRoot(root).render(<Popup />);
}
