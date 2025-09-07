import { createRoot } from "react-dom/client";
import DownloadButton from "../components/download-button/download-button";
import { buttonElementId } from "../content_script";
import React from "react";

export function addButtonYouTube(): void {
  console.log('adding button to YouTube')
  if (document.getElementById(buttonElementId)) return;
  const el: HTMLDivElement = document.querySelector(
    'div#above-the-fold div#title',
  ) as HTMLDivElement;
  if (!el) return;
  const newDiv = document.createElement("div");
  newDiv.id = buttonElementId;
  el.style.display = 'flex';
  el.style.justifyContent = 'space-between';
  el.style.alignItems = 'center';
  el.style.gap = '20px';
  el.append(newDiv);
  const root = createRoot(newDiv);
  root.render(
    <React.StrictMode>
      <DownloadButton />
    </React.StrictMode>
  );
  console.log('added button to YouTube')
}