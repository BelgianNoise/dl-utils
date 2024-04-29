export enum MessageType {
  URL_UPDATED = 'URL_UPDATED',
}

export interface URLUpdatedMessage {
  type: MessageType.URL_UPDATED;
  url: string;
}

export function newURLUpdatedMessage(
  url: string,
): URLUpdatedMessage {
  return {
    type: MessageType.URL_UPDATED,
    url,
  };
}
