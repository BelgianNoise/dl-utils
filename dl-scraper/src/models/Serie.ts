import { Language } from './language';

export interface Serie {
  title: string;
  description: string;
  language: Language;
  hyperlink: string;
  poster: string;
  seasons: Map<string, Season>;
}

export interface Season {
  title: string;
  episodes: Episode[];
  poster: string;
}

export interface Episode {
  title: string;
  number: number;
  description: string;
  durationSeconds: number;
  hyperlink: string;
  thumbnail: string;
}
