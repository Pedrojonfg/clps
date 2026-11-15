const STORAGE_KEY = "cesium_ion_token";

export function loadIonToken(): string {
  try {
    return localStorage.getItem(STORAGE_KEY)?.trim() ?? "";
  } catch {
    return "";
  }
}

export function saveIonToken(token: string): void {
  const t = token.trim();
  if (!t) {
    localStorage.removeItem(STORAGE_KEY);
    return;
  }
  localStorage.setItem(STORAGE_KEY, t);
}
