export enum MessageType {
  URL_UPDATED = 'URL_UPDATED',
}

export interface Message {
  type: MessageType;
}

export interface URLUpdatedMessage extends Message {
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
