/** Parse "major.minor.patch" (a leading "v" and any "-pre"/"+build" suffix are ignored). Null if unparseable. */
export function parseVersion(v: string): [number, number, number] | null {
  const m = /^v?(\d+)(?:\.(\d+))?(?:\.(\d+))?/.exec(v.trim());
  return m ? [Number(m[1]), Number(m[2] ?? 0), Number(m[3] ?? 0)] : null;
}

/** True only when both versions parse and `running` is strictly older than `required`. */
export function isOlder(running: string, required: string): boolean {
  const a = parseVersion(running);
  const b = parseVersion(required);
  if (!a || !b) return false; // unknown -> never block
  for (let i = 0; i < 3; i++) if (a[i] !== b[i]) return a[i] < b[i];
  return false;
}
