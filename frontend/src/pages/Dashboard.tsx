import { useCallback, useEffect, useState } from "react";
import { API_URL, apiFetch } from "../lib/api";
import { btnPrimary, btnSecondary } from "../lib/styles";
import { Badge, MeetingStatusBadge } from "../components/Badge";

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

type MeetingSummary = {
  id: string;
  title: string;
  meeting_date: string;
  status: string;
};

type MeetingsState =
  | { kind: "loading" }
  | { kind: "ok"; meetings: MeetingSummary[] }
  | { kind: "error"; message: string };

function Dashboard({ navigate }: { navigate: (to: string) => void }) {
  const [health, setHealth] = useState<HealthState>({ kind: "loading" });
  const [auth, setAuth] = useState<AuthState>({ kind: "loading" });
  const [meetings, setMeetings] = useState<MeetingsState>({ kind: "loading" });

  useEffect(() => {
    apiFetch("/meetings")
      .then(async (res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data: MeetingSummary[] = await res.json();
        setMeetings({ kind: "ok", meetings: data.slice(0, 10) });
      })
      .catch((err) =>
        setMeetings({ kind: "error", message: String(err.message ?? err) }),
      );
  }, []);

  useEffect(() => {
    apiFetch("/health")
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
    apiFetch("/auth/me")
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
    apiFetch("/auth/logout", { method: "POST" }).finally(loadMe);
  }, [loadMe]);

  const startDemo = useCallback(() => {
    apiFetch("/auth/demo-login", { method: "POST" }).finally(loadMe);
  }, [loadMe]);

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-semibold tracking-tight text-white">
        Analiza spotkań
      </h1>

      <div className="rounded-xl border border-zinc-800 bg-zinc-900 px-8 py-6">
        {health.kind === "loading" && (
          <p className="text-zinc-500">Sprawdzanie backendu…</p>
        )}
        {health.kind === "ok" && (
          <p className="font-medium text-emerald-400">{health.status}</p>
        )}
        {health.kind === "error" && (
          <p className="text-red-400">Błąd: {health.message}</p>
        )}
      </div>

      <div className="rounded-xl border border-zinc-800 bg-zinc-900 px-8 py-6">
        {auth.kind === "loading" && (
          <p className="text-zinc-500">Sprawdzanie sesji…</p>
        )}
        {auth.kind === "error" && (
          <p className="text-red-400">Błąd: {auth.message}</p>
        )}
        {auth.kind === "anonymous" && (
          <div className="flex flex-col items-start gap-2">
            <a href={`${API_URL}/auth/login`} className={"inline-block " + btnPrimary}>
              Zaloguj się przez Google
            </a>
            <p className="max-w-sm text-xs text-zinc-500">
              Logowanie Google jest w trybie testowym — dostęp mają tylko
              zaproszeni testerzy. Chcesz tylko zobaczyć appkę?
            </p>
            <button
              onClick={startDemo}
              className="text-sm text-blue-400 underline hover:text-blue-300"
            >
              Wypróbuj demo bez logowania Google
            </button>
          </div>
        )}
        {auth.kind === "authenticated" && (
          <div className="text-left">
            <p className="text-zinc-100">
              Zalogowano jako{" "}
              <span className="font-semibold text-white">
                {auth.me.display_name ?? auth.me.email}
              </span>
            </p>
            <p className="text-sm text-zinc-500">{auth.me.email}</p>
            <p className="mt-2 flex items-center gap-2 text-sm text-zinc-400">
              Dostęp do Gmail/Sheets:
              {auth.me.reauth_required ? (
                <Badge tone="negative">wymaga ponownej zgody</Badge>
              ) : auth.me.google_connected ? (
                <Badge tone="positive">aktywny</Badge>
              ) : (
                <Badge tone="neutral">nieznany</Badge>
              )}
            </p>
            <button onClick={logout} className={"mt-4 " + btnSecondary}>
              Wyloguj
            </button>
          </div>
        )}
      </div>

      <div className="rounded-xl border border-zinc-800 bg-zinc-900 px-8 py-6">
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-zinc-500">
          Ostatnie spotkania
        </h2>
        {meetings.kind === "loading" && <p className="text-zinc-500">Wczytywanie…</p>}
        {meetings.kind === "error" && (
          <p className="text-red-400">Błąd: {meetings.message}</p>
        )}
        {meetings.kind === "ok" && meetings.meetings.length === 0 && (
          <p className="text-zinc-500">
            Brak spotkań —{" "}
            <a
              href="/upload"
              onClick={(e) => {
                e.preventDefault();
                navigate("/upload");
              }}
              className="text-blue-400 hover:underline"
            >
              dodaj pierwsze
            </a>
            .
          </p>
        )}
        {meetings.kind === "ok" && meetings.meetings.length > 0 && (
          <ul className="flex flex-col divide-y divide-zinc-800">
            {meetings.meetings.map((m) => (
              <li key={m.id}>
                <a
                  href={`/meetings/${m.id}`}
                  onClick={(e) => {
                    e.preventDefault();
                    navigate(`/meetings/${m.id}`);
                  }}
                  className="flex items-center justify-between gap-4 py-2.5 text-sm hover:text-white"
                >
                  <span className="text-zinc-100">{m.title}</span>
                  <span className="flex items-center gap-2 text-zinc-500">
                    {m.meeting_date}
                    <MeetingStatusBadge status={m.status} />
                  </span>
                </a>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

export default Dashboard;
