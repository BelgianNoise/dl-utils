import React from "react";
import { download } from "../components/download-button/download";
import DownloadButton from "../components/download-button/download-button";
import { createRoot } from "react-dom/client";

const GenericButton = 'dl-utils-generic-button';

export function addDownloadIconButtonsToElements(
  selector: string,
): void {
  const els = document.querySelectorAll(selector);
  console.log(`Found ${els.length} elements for selector ${selector}`);
  // Filter out els that already have a download button
  const filteredEls = Array.from(els).filter(el => !el.querySelector(`.${GenericButton}`));
  console.log(`Attempting to add ${filteredEls.length} download buttons`);
  for (const el of filteredEls) {
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
  newDiv.style.zIndex = '9999';

  const href = el.getAttribute('href');
  if (!href) return;
  const videoLink = href.startsWith('http') ? href : window.location.origin + href;
  const onClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    e.nativeEvent.stopImmediatePropagation();
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