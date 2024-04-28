import { Language } from './language';

export interface Series {
  platformSpecificId: string | undefined;
  title: string;
  description: string;
  language: Language;
  hyperlink: string;
  poster: string;
  seasons: Map<string, Season>;
}

export interface Season {
  platformSpecificId: string | undefined;
  title: string;
  episodes: Episode[];
  poster: string;
}

export interface Episode {
  platformSpecificId: string | undefined;
  title: string;
  number: number;
  description: string;
  durationSeconds: number;
  hyperlink: string;
  thumbnail: string;
}
