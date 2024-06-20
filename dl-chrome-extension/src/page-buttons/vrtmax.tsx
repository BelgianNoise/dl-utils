import React from "react";
import { createRoot } from "react-dom/client";
import DownloadButton from "../components/download-button/download-button";

// FILE STILL NEEDS WORK
const VRTMAXButton = 'vrtmax-dl-utils-button';

export function addButtonsVRTMAX(
  url: string,
): void {
  if (!url.match('vrt.be/vrtmax')) return;

  if (url.match(/\/a-z\/([\w-]+?)\/([\w-]+?)\/([\w-]+?)\/?$/)) {
    addButtonVRTMAX();
  } else {
    removeButton();
  }
}

function removeButton(): void {
  const el = document.getElementById(VRTMAXButton);
  if (el) el.remove();
}

function addButtonVRTMAX(): void {
  console.log('adding button to VRT MAX')
  if (document.getElementById(VRTMAXButton)) return;
  const el = document.querySelector('sso-login');
  if (!el) return;
  const newDiv = document.createElement("div");
  newDiv.id = VRTMAXButton;
  el.parentNode!.insertBefore(newDiv, el);
  const root = createRoot(newDiv);
  root.render(
    <React.StrictMode>
      <DownloadButton />
    </React.StrictMode>
  );
  console.log('added button to VRT MAX')
}