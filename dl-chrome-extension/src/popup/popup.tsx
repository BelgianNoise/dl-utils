import React from "react";
import { createRoot } from "react-dom/client";

const Popup = () => {
  return (
    <div>
      <h1>TEST</h1>
    </div>
  );
};

export default Popup;

const root = document.getElementById("root")
if (root) {
  createRoot(root).render(<Popup />);
}
