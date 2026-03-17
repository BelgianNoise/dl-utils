export function buildURL(path: string, base: string): URL {
  const normalizedBase = base.replace(/\/?$/, '/');
  return new URL(path, normalizedBase);
}
