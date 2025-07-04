import React from "react";
import { addDownloadIconButtonsToElements } from "./generic";
import DownloadButton from "../components/download-button/download-button";
import { createRoot } from "react-dom/client";

export function addButtonsStreamz(url: string): void {
  if (!url.match('streamz.be')) return;

  if (url.match(/\/streamz\/afspelen\//)) {
    // Streamz
    addButtonStreamzPlayer();
  } else if (url.match(/\/streamz\//)) {
    // Streamz overview
    addButtonStreamzOverview();
  }
}

function addButtonStreamzPlayer(): void {
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

function addButtonStreamzOverview(): void {
  addDownloadIconButtonsToElements('.block-list .list__item a.media__figure-link');
}
