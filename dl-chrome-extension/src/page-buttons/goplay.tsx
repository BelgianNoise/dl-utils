import { createRoot } from "react-dom/client";
import React from "react";
import DownloadButton from "../components/download-button/download-button";
import { addDownloadIconButtonsToElements } from "./generic";
import { download } from "../components/download-button/download";

const GoPlaySeriesButton = 'goplay-series-button';
const GoPlayMovieButton = 'goplay-movie-button';
const GoPlaySeasonButton = 'goplay-season-button';

export function addButtonsGoPlay(url: string): void {
  if (!url.match('goplay.be')) return;

  setInterval(() => {
    addButtonsGoPlaySwimlane();
  }, 1000);
  addSeasonButton();

  if (url.match(/\/video\/[\w-]+?\/[\w-]+?\/[\w-]+?(#autoplay)?$/)) {
    // GOPLAY SERIES
    addButtonGoPlaySeries();
  } else if (url.match(/\/video\/([\w-]+?\/[\w-]+?\/)?[\w-]+?(#autoplay)?$/)) {
    // GOPLAY MOVIE
    addButtonGoPlayMovie();
  }
}

function addButtonGoPlaySeries(): void {
  console.log('adding button to GoPlay')
  if (document.getElementById(GoPlaySeriesButton)) return;
  const el = document.querySelector('div.sbs-video__info h1.sbs-video__title');
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

function addButtonGoPlayMovie(): void {
  console.log('adding button to GoPlay')
  if (document.getElementById(GoPlayMovieButton)) return;
  const el = document.querySelector('main.l-content > article');
  if (!el) return;
  (el as HTMLDivElement).style.position = 'relative';
  const newDiv = document.createElement("div");
  newDiv.id = GoPlayMovieButton;
  newDiv.style.position = 'absolute';
  newDiv.style.left = '50%';
  newDiv.style.top = '0';
  newDiv.style.transform = 'translateX(-50%) translateY(-50%)';
  el.append(newDiv);
  const root = createRoot(newDiv);
  root.render(
    <React.StrictMode>
      <DownloadButton />
    </React.StrictMode>
  );
  console.log('added button to GoPlay')
}

function addButtonsGoPlaySwimlane(): void {
  addDownloadIconButtonsToElements('div.swimlane-section ul li a[href*="/video"]');
}

function addSeasonButton(): void {
  if (document.getElementById(GoPlaySeasonButton)) return;

  const addSeasonToQueue = () => {
    const seasonContainer = document.querySelector('div#afleveringen.seasons');
    if (!seasonContainer) return;
  
    // find all video urls in the swimlane
    const videoUrls = Array.from(seasonContainer.querySelectorAll('a[href*="/video"]'))
      .map((el) => el.getAttribute('href'))
      .filter((url) => url !== null)
      .map((url) => url!.startsWith('http') ? url : window.location.origin + url);
    
    for (const video of videoUrls) {
      if (video) download({ url: video });
    }
  }

  // Add download button to the page
  const el = document.querySelector('#afleveringen .playlist-toggle');
  if (!el) return;
  const newDiv = document.createElement("div");
  newDiv.id = GoPlaySeasonButton;
  el.append(newDiv);
  const root = createRoot(newDiv);
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
