import React from "react";
import { createRoot } from "react-dom/client";
import SVGSettings from "../svg/svg-settings";
import "./popup.css";
import "../../public/css/variables.css";
import "../css/button.css";
import "../css/dialog.css";
import "../css/input.css";
import SettingsDialog from "../components/settings";
import SVGCross from "../svg/svg-cross";
import ManualAddDialog from "../components/manual-add";

const Popup = () => {

  const [showSettings, setShowSettings] = React.useState(false);
  const [showManualAdd, setShowManualAdd] = React.useState(false);

  return (
    <div className='container'>
      <div className='header'>
        <h1>Queue</h1>
        <div className='buttons'>
          <button
            id='add-manual-manifest-button'
            onClick={() => setShowManualAdd(true)}
            disabled={showSettings || showManualAdd}
          >
            <SVGCross />
          </button>
          <button
            onClick={() => setShowSettings(true)}
            disabled={showSettings || showManualAdd}
          >
            <SVGSettings />
          </button>
        </div>
      </div>

      <SettingsDialog
        open={showSettings}
        onClose={() => setShowSettings(false)}
      />
      <ManualAddDialog
        open={showManualAdd}
        onClose={() => setShowManualAdd(false)}
      />
    </div>
  );
};

export default Popup;

const root = document.getElementById("root")
if (root) {
  createRoot(root).render(<Popup />);
}
