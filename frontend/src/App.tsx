import { useCallback, useEffect, useState } from "react";

type HealthState =
  | { kind: "loading" }
  | { kind: "ok"; status: string }
  | { kind: "error"; message: string };

type Me = {
  id: string;
  email: string;
  display_name: string | null;
  google_connected: boolean;
  reauth_required: boolean;
  access_token_expires_at: string | null;
};

type AuthState =
  | { kind: "loading" }
  | { kind: "anonymous" }
  | { kind: "authenticated"; me: Me }
  | { kind: "error"; message: string };

function App() {
  const [health, setHealth] = useState<HealthState>({ kind: "loading" });
  const [auth, setAuth] = useState<AuthState>({ kind: "loading" });

  useEffect(() => {
    fetch("/health")
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data) => setHealth({ kind: "ok", status: data.status }))
      .catch((err) =>
        setHealth({ kind: "error", message: String(err.message ?? err) }),
      );
  }, []);

  const loadMe = useCallback(() => {
    fetch("/auth/me")
      .then(async (res) => {
        if (res.status === 401) {
          setAuth({ kind: "anonymous" });
          return;
        }
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const me: Me = await res.json();
        setAuth({ kind: "authenticated", me });
      })
      .catch((err) =>
        setAuth({ kind: "error", message: String(err.message ?? err) }),
      );
  }, []);

  useEffect(() => {
    loadMe();
  }, [loadMe]);

  const logout = useCallback(() => {
    fetch("/auth/logout", { method: "POST" }).finally(loadMe);
  }, [loadMe]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="flex flex-col gap-4">
        <div className="rounded-lg border border-gray-200 bg-white px-8 py-6 shadow-sm text-center">
          <h1 className="text-xl font-medium text-gray-900 mb-2">
            Analiza spotkań
          </h1>
          {health.kind === "loading" && (
            <p className="text-gray-500">Sprawdzanie backendu…</p>
          )}
          {health.kind === "ok" && (
            <p className="text-green-600 font-semibold">{health.status}</p>
          )}
          {health.kind === "error" && (
            <p className="text-red-600">Błąd: {health.message}</p>
          )}
        </div>

        <div className="rounded-lg border border-gray-200 bg-white px-8 py-6 shadow-sm text-center">
          {auth.kind === "loading" && (
            <p className="text-gray-500">Sprawdzanie sesji…</p>
          )}
          {auth.kind === "error" && (
            <p className="text-red-600">Błąd: {auth.message}</p>
          )}
          {auth.kind === "anonymous" && (
            <a
              href="/auth/login"
              className="inline-block rounded-md bg-blue-600 px-4 py-2 text-white font-medium hover:bg-blue-700"
            >
              Zaloguj się przez Google
            </a>
          )}
          {auth.kind === "authenticated" && (
            <div className="text-left">
              <p className="text-gray-900">
                Zalogowano jako{" "}
                <span className="font-semibold">
                  {auth.me.display_name ?? auth.me.email}
                </span>
              </p>
              <p className="text-sm text-gray-500">{auth.me.email}</p>
              <p className="text-sm mt-2">
                Dostęp do Gmail/Sheets:{" "}
                {auth.me.reauth_required ? (
                  <span className="text-red-600 font-medium">
                    wymaga ponownej zgody
                  </span>
                ) : auth.me.google_connected ? (
                  <span className="text-green-600 font-medium">aktywny</span>
                ) : (
                  <span className="text-gray-500">nieznany</span>
                )}
              </p>
              <button
                onClick={logout}
                className="mt-4 rounded-md border border-gray-300 px-4 py-2 text-gray-700 hover:bg-gray-100"
              >
                Wyloguj
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
