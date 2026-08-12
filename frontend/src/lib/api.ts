// W dev VITE_API_URL zwykle jest puste — ścieżki względne idą przez proxy
// Vite (patrz vite.config.ts) tak jak dotychczas. W produkcji (frontend i
// backend na osobnych domenach, np. Vercel + Render) trzeba podać pełny URL
// backendu, bo nie ma tam żadnego proxy między nimi.
export const API_URL = import.meta.env.VITE_API_URL ?? "";

const CSRF_HEADER = "X-CSRF-Token";
const SAFE_METHODS = new Set(["GET", "HEAD", "OPTIONS"]);

// Token CSRF trzymamy w pamięci modułu, nie w localStorage: ma żyć dokładnie
// tyle, co karta. Backend wydaje go z GET /auth/csrf i trzyma w sesji.
let csrfToken: string | null = null;
let inFlight: Promise<string> | null = null;

async function loadCsrfToken(): Promise<string> {
  const res = await fetch(`${API_URL}/auth/csrf`, { credentials: "include" });
  if (!res.ok) throw new Error(`Nie udało się pobrać tokena CSRF (HTTP ${res.status}).`);
  const data: { csrf_token: string } = await res.json();
  csrfToken = data.csrf_token;
  return data.csrf_token;
}

function getCsrfToken(): Promise<string> {
  if (csrfToken) return Promise.resolve(csrfToken);
  // Współdzielony promise — kilka równoległych mutacji na starcie nie powinno
  // wywołać kilku żądań o token.
  inFlight ??= loadCsrfToken().finally(() => {
    inFlight = null;
  });
  return inFlight;
}

/** Po wylogowaniu backend czyści sesję i wydaje nowy token — ten w pamięci
 *  jest już nieważny. */
export function resetCsrfToken(): void {
  csrfToken = null;
}

function withCsrf(init: RequestInit | undefined, token: string): RequestInit {
  const headers = new Headers(init?.headers);
  headers.set(CSRF_HEADER, token);
  return { ...init, headers };
}

export async function apiFetch(path: string, init?: RequestInit): Promise<Response> {
  const url = `${API_URL}${path}`;
  // Cross-origin fetch nie wysyła cookies domyślnie — a sesja logowania
  // (po Google OAuth) jest trzymana właśnie w cookie ustawianym przez backend.
  const base: RequestInit = { credentials: "include", ...init };

  const method = (init?.method ?? "GET").toUpperCase();
  if (SAFE_METHODS.has(method)) {
    return fetch(url, base);
  }

  const token = await getCsrfToken();
  const res = await fetch(url, withCsrf(base, token));
  if (res.status !== 403) return res;

  // 403 może znaczyć, że sesja (a z nią token) wygasła albo została wyczyszczona
  // przez wylogowanie w innej karcie. Jedna próba z odświeżonym tokenem.
  csrfToken = null;
  const retryToken = await getCsrfToken();
  if (retryToken === token) return res;
  return fetch(url, withCsrf(base, retryToken));
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
