import React from "react";
import { download } from "../components/download-button/download";
import DownloadButton from "../components/download-button/download-button";
import { createRoot } from "react-dom/client";

const GenericButton = 'dl-utils-generic-button';

export function addDownloadIconButtonsToElements(
  selector: string,
): void {
  const els = document.querySelectorAll(selector);
  console.log(`Attempting to add ${els.length} download buttons`);
  for (const el of els) {
    if (el.querySelector(`.${GenericButton}`)) continue;
    addDownloadIconButton(el);
    console.log('added download button to element');
  }
}

export function addDownloadIconButton(
  el: Element,
): void {
  const newDiv = document.createElement("div");
  newDiv.className = GenericButton;
  newDiv.style.position = 'absolute';
  newDiv.style.top = '5px';
  newDiv.style.right = '5px';
  newDiv.style.zIndex = '10';

  const href = el.getAttribute('href');
  if (!href) return;
  const videoLink = href.startsWith('http') ? href : window.location.origin + href;
  const onClick = () => {
    download({ url: videoLink });
  }

  el.append(newDiv);
  (el as HTMLElement).style.position = 'relative';
  const root = createRoot(newDiv);
  root.render(
    <React.StrictMode>
      <DownloadButton smallPadding hideText onClick={onClick} />
    </React.StrictMode>
  );
}