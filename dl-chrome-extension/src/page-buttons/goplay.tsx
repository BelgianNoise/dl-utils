import { createRoot } from "react-dom/client";
import React from "react";
import DownloadButton from "../components/download-button/download-button";
import { addDownloadIconButtonsToElements } from "./generic";
import { download } from "../components/download-button/download";
import { addLoopingInterval } from "../content_script";

const GoPlaySeriesButton = 'goplay-series-button';
const GoPlayMovieButton = 'goplay-movie-button';
const GoPlaySeasonButton = 'goplay-season-button';

export function addButtonsGoPlay(url: string): void {
  if (!url.match('goplay.be')) return;

  addLoopingInterval(() => {
    addButtonsGoPlaySwimlane();
  });

  addSeasonButton();

  if (url.match(/\/video\/[\w-]+?\/[\w-]+?\/[\w-]+?(#autoplay)?$/)) {
    // GOPLAY SERIES
    addButtonGoPlaySeries();
  } else if (url.match(/\/video\/([\w-]+?\/[\w-]+?\/)?[\w-]+?(#autoplay)?$/)) {
    // GOPLAY MOVIE
    addButtonGoPlaySeries();
  }
}

function addButtonGoPlaySeries(): void {
  console.log('adding button to GoPlay')
  if (document.getElementById(GoPlaySeriesButton)) return;
  const el = document.querySelector('div.videoInfo h1');
  if (!el) return;
  const newDiv = document.createElement("div");
  newDiv.id = GoPlaySeriesButton;
  el.parentNode!.insertBefore(newDiv, el);
  const root = createRoot(newDiv);
  root.render(
    <React.StrictMode>
      <DownloadButton />
    </React.StrictMode>
  );
  console.log('added button to GoPlay')
}

function addButtonsGoPlaySwimlane(): void {
  addDownloadIconButtonsToElements('ul li a[href*="/video"]');
}

function addSeasonButton(): void {
  if (document.getElementById(GoPlaySeasonButton)) return;

  const addSeasonToQueue = () => {
    const videoUrls = Array.from(document.querySelectorAll('ul li a[href*="/video"]'))
      .map((el) => el.getAttribute('href'))
      .filter((url) => url !== null)
      .map((url) => url!.startsWith('http') ? url : window.location.origin + url)
      .sort((a, b) => a!.localeCompare(b!));
    
    for (const video of videoUrls) {
      if (video) download({ url: video });
    }
  }

  // Add download button to the page
  const el: HTMLDivElement | null = document.querySelector('div:has(> div#season)');
  if (!el) return;
  const newDiv = document.createElement("div");
  newDiv.id = GoPlaySeasonButton;
  el.append(newDiv);
  el.style.display = 'flex';
  const root = createRoot(newDiv);
  console.log('Adding season button');
  root.render(
    <React.StrictMode>
      <DownloadButton
        text={'Download Season'}
        styles={{ marginLeft: '10px' }}
        onClick={() => addSeasonToQueue()}
      />
    </React.StrictMode>
  );
}
