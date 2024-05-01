import React from "react";
import { createRoot } from "react-dom/client";
import SVGSettings from "../svg/svg-settings";
import "./popup.css";
import "../../public/css/variables.css";
import "../css/button.css";
import "../css/dialog.css";
import "../css/input.css";
import SVGSave from "../svg/svg-save";
import SVGCross from "../svg/svg-cross";
import SVGCheck from "../svg/svg-check";

const Popup = () => {

  const [showSettings, setShowSettings] = React.useState(false);
  const [justSaved, setJustSaved] = React.useState(false);

  const saveSettings = () => {
    const token = (document.getElementById("token") as HTMLInputElement).value;
    const url = (document.getElementById("url") as HTMLInputElement).value;
    const quality = (document.getElementById("quality") as HTMLSelectElement).value;

    chrome.storage.sync.set({ token, quality, url }, () => {
      console.log('Settings saved', token, url, quality);
      setJustSaved(true);
      setTimeout(() => {
        setJustSaved(false);
      }, 3000);
    });
  }
  const loadSettings = () => {
    chrome.storage.sync.get(['token', 'url', 'quality'], (data) => {
      if (data.token) {
        (document.getElementById("token") as HTMLInputElement).value = data.token;
      }
      (document.getElementById("url") as HTMLInputElement).value = data?.url ?? 'http://localhost:8282';
      if (!data.url) {
        saveSettings();
      }
      if (data.quality) {
        (document.getElementById("quality") as HTMLSelectElement).value = data.quality;
      }
    });
  }

  // Load settings
  React.useEffect(() => {
    loadSettings();
  }, []);

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
          <label htmlFor="url">URL</label>
          <input type='text' id="url" name="url" placeholder="https://..."/>
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
          <button className="primary" onClick={saveSettings} disabled={justSaved}>
            {justSaved ? <SVGCheck color='#303030' /> : <SVGSave color='#303030' />}
            Save
          </button>
          <button onClick={() => setShowSettings(false)}>
            <SVGCross />
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
