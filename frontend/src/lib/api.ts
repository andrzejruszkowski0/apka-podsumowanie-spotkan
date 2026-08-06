// W dev VITE_API_URL zwykle jest puste — ścieżki względne idą przez proxy
// Vite (patrz vite.config.ts) tak jak dotychczas. W produkcji (frontend i
// backend na osobnych domenach, np. Vercel + Render) trzeba podać pełny URL
// backendu, bo nie ma tam żadnego proxy między nimi.
export const API_URL = import.meta.env.VITE_API_URL ?? "";

export function apiFetch(path: string, init?: RequestInit): Promise<Response> {
  return fetch(`${API_URL}${path}`, {
    // Cross-origin fetch nie wysyła cookies domyślnie — a sesja logowania
    // (po Google OAuth) jest trzymana właśnie w cookie ustawianym przez
    // backend.
    credentials: "include",
    ...init,
  });
}

// Backend zwraca {detail, reauth_required: true} gdy konto nie ma ważnych
// tokenów Google (m.in. konto demo — patrz auth/demo-login — nigdy ich nie
// ma). Tłumaczymy to na komunikat zrozumiały dla użytkownika zamiast
// surowego opisu z backendu.
export async function errorDetail(res: Response): Promise<string> {
  const body = await res.json().catch(() => null);
  if (body?.reauth_required) {
    return "Ta funkcja wymaga połączonego konta Google (wysyłka maili) — niedostępna w trybie demo.";
  }
  return body?.detail ?? `HTTP ${res.status}`;
}
