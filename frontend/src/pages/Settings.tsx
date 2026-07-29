import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "../lib/api";

type Person = {
  id: string;
  full_name: string;
  email: string;
  aliases: string[];
  org: string | null;
};

type PeopleState =
  | { kind: "loading" }
  | { kind: "ok"; people: Person[] }
  | { kind: "error"; message: string };

type SyncState =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "done"; upserted: number; deactivated: number }
  | { kind: "error"; message: string };

async function errorDetail(res: Response): Promise<string> {
  const body = await res.json().catch(() => null);
  return body?.detail ?? `HTTP ${res.status}`;
}

function Settings() {
  const [people, setPeople] = useState<PeopleState>({ kind: "loading" });
  const [sync, setSync] = useState<SyncState>({ kind: "idle" });

  const loadPeople = useCallback(() => {
    setPeople({ kind: "loading" });
    apiFetch("/people")
      .then(async (res) => {
        if (!res.ok) throw new Error(await errorDetail(res));
        const data: Person[] = await res.json();
        setPeople({ kind: "ok", people: data });
      })
      .catch((err) =>
        setPeople({ kind: "error", message: String(err.message ?? err) }),
      );
  }, []);

  useEffect(() => {
    loadPeople();
  }, [loadPeople]);

  const runSync = useCallback(() => {
    setSync({ kind: "loading" });
    apiFetch("/people/sync", { method: "POST" })
      .then(async (res) => {
        if (!res.ok) throw new Error(await errorDetail(res));
        return res.json();
      })
      .then((data: { upserted: number; deactivated: number }) => {
        setSync({ kind: "done", upserted: data.upserted, deactivated: data.deactivated });
        loadPeople();
      })
      .catch((err) =>
        setSync({ kind: "error", message: String(err.message ?? err) }),
      );
  }, [loadPeople]);

  return (
    <div className="flex flex-col gap-4">
      <div className="rounded-lg border border-gray-200 bg-white px-8 py-6 shadow-sm">
        <div className="flex items-center justify-between gap-4">
          <div>
            <h2 className="font-medium text-gray-900">Sync osób z arkusza</h2>
            <p className="text-sm text-gray-500">
              Wczytuje arkusz „Osoby” i aktualizuje listę (upsert po emailu).
            </p>
          </div>
          <button
            onClick={runSync}
            disabled={sync.kind === "loading"}
            className="shrink-0 rounded-md bg-blue-600 px-4 py-2 text-white font-medium hover:bg-blue-700 disabled:opacity-50"
          >
            {sync.kind === "loading" ? "Synchronizuję…" : "Sync teraz"}
          </button>
        </div>
        {sync.kind === "done" && (
          <p className="text-sm text-green-600 mt-3">
            Zaktualizowano {sync.upserted}, dezaktywowano {sync.deactivated}.
          </p>
        )}
        {sync.kind === "error" && (
          <p className="text-sm text-red-600 mt-3">Błąd: {sync.message}</p>
        )}
      </div>

      <div className="rounded-lg border border-gray-200 bg-white px-8 py-6 shadow-sm">
        <h2 className="font-medium text-gray-900 mb-3">Osoby (aktywne)</h2>
        {people.kind === "loading" && (
          <p className="text-gray-500">Wczytywanie…</p>
        )}
        {people.kind === "error" && (
          <p className="text-red-600">Błąd: {people.message}</p>
        )}
        {people.kind === "ok" && people.people.length === 0 && (
          <p className="text-gray-500">Brak osób — kliknij „Sync teraz”.</p>
        )}
        {people.kind === "ok" && people.people.length > 0 && (
          <table className="w-full text-sm text-left">
            <thead>
              <tr className="border-b border-gray-200 text-gray-500">
                <th className="py-2 pr-4 font-medium">Imię i nazwisko</th>
                <th className="py-2 pr-4 font-medium">Email</th>
                <th className="py-2 pr-4 font-medium">Aliasy</th>
                <th className="py-2 font-medium">Firma</th>
              </tr>
            </thead>
            <tbody>
              {people.people.map((p) => (
                <tr key={p.id} className="border-b border-gray-100">
                  <td className="py-2 pr-4 text-gray-900">{p.full_name}</td>
                  <td className="py-2 pr-4 text-gray-500">{p.email}</td>
                  <td className="py-2 pr-4 text-gray-500">
                    {p.aliases.join(", ")}
                  </td>
                  <td className="py-2 text-gray-500">{p.org ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

export default Settings;
