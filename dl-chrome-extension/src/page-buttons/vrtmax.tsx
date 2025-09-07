import React from "react";
import { addLoopingInterval } from "../content_script";
import { addDownloadIconButtonsToElements } from "./generic";
import DownloadButton from "../components/download-button/download-button";
import { createRoot } from "react-dom/client";

export function addButtonsVRTMAX(url: string): void {
  if (!url.match('vrt.be/vrtmax')) return;

  addLoopingInterval(
    () => addDownloadIconButtonsToElements('ul > li a[href^="/vrtmax/a-z/"]')
  );

  if (url.match(/\/vrtmax\/a-z\/([^\/]+\/)+/)) {
    // /vrtmax/a-z/reizen-waes/8/reizen-waes-s8a1-taiwan/
    console.log('===============')
    addButtonVRTMAXPlayer();
  }
}

function addButtonVRTMAXPlayer(): void {
  console.log('adding button to VRTMAX')
  const player = document.querySelector('section[aria-label="Mediaspeler"]');
  if (!player) return;
  const newDiv = document.createElement("div");
  player.parentNode!.insertBefore(newDiv, player);
  const root = createRoot(newDiv);
  root.render(
    <React.StrictMode>
      <DownloadButton />
    </React.StrictMode>
  );
  console.log('added button to VRTMAX')
}
