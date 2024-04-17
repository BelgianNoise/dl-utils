import { getLogger } from '../utils/logging';
import { Retriever } from './retriever';

export class VRTMAXRetriever extends Retriever {
  constructor() {
    super(getLogger('VRTMAXRetriever'), 'vrt');
  }

  public retrieve(url: string): Promise<void> {
    this.logger.debug(`Retrieving VRTMAX URL: ${url}`);
    return Promise.resolve();
  }
}
