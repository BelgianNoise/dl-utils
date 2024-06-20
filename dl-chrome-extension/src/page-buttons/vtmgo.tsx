import React from "react";
import { addDownloadIconButtonsToElements } from "./generic";
import DownloadButton from "../components/download-button/download-button";
import { createRoot } from "react-dom/client";

// FILE STILL NEEDS WORK

export function addButtonsVTMGO(url: string): void {
  if (!url.match('vtmgo.be')) return;

  if (url.match(/\/vtmgo\/afspelen\//)) {
    // VTM GO
    addButtonVTMGOPlayer();
  } else if (url.match(/\/vtmgo\//)) {
    // VTM GO overview
    addButtonVTMGOOverview();
  }
}

function addButtonVTMGOPlayer(): void {
  const el = document.querySelector('main');
  if (!el) return;
  const newDiv = document.createElement("div");
  newDiv.style.position = 'absolute';
  newDiv.style.top = '20px';
  newDiv.style.right = '20px';
  el.append(newDiv);
  const root = createRoot(newDiv);
  root.render(
    <React.StrictMode>
      <DownloadButton />
    </React.StrictMode>
  );
}

function addButtonVTMGOOverview(): void {
  addDownloadIconButtonsToElements('.block-list .list__item a.media__figure-link');
}