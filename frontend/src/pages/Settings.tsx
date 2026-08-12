import { ArrowsClockwise, Users } from "@phosphor-icons/react";
import { useCallback, useEffect, useState } from "react";
import { apiFetch, errorDetail } from "../lib/api";
import { EmptyState, ErrorState, LoadingState } from "../components/States";
import { btnPrimary, btnSecondarySm } from "../lib/styles";

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
      <h1 className="text-2xl font-semibold tracking-tight text-white">Ustawienia</h1>

      <div className="rounded-xl border border-zinc-800 bg-zinc-900 px-4 sm:px-8 py-6">
        <div className="flex items-center justify-between gap-4">
          <div>
            <h2 className="font-medium text-zinc-100">Sync osób z arkusza</h2>
            <p className="text-sm text-zinc-500">
              Wczytuje arkusz „Osoby” i aktualizuje listę (upsert po emailu).
            </p>
          </div>
          <button
            onClick={runSync}
            disabled={sync.kind === "loading"}
            className={"flex shrink-0 items-center gap-1.5 " + btnPrimary}
          >
            <ArrowsClockwise size={16} weight="bold" className={sync.kind === "loading" ? "animate-spin" : undefined} />
            {sync.kind === "loading" ? "Synchronizuję…" : "Sync teraz"}
          </button>
        </div>
        {sync.kind === "done" && (
          <p className="mt-3 text-sm text-emerald-400">
            Zaktualizowano {sync.upserted}, dezaktywowano {sync.deactivated}.
          </p>
        )}
        {sync.kind === "error" && (
          <p className="mt-3 text-sm text-red-400">Błąd: {sync.message}</p>
        )}
      </div>

      <div className="rounded-xl border border-zinc-800 bg-zinc-900 px-4 sm:px-8 py-6">
        <h2 className="mb-3 font-medium text-zinc-100">Osoby (aktywne)</h2>
        {people.kind === "loading" && <LoadingState />}
        {people.kind === "error" && (
          <ErrorState message={people.message} onRetry={loadPeople} />
        )}
        {people.kind === "ok" && people.people.length === 0 && (
          <EmptyState
            icon={Users}
            title="Kartoteka osób jest pusta"
            description="Lista mieszka w arkuszu Google „Osoby” — synchronizacja pobiera z niego imiona, e-maile i aliasy używane do rozpoznawania mówców w transkrypcji."
            action={
              <button onClick={runSync} className={btnSecondarySm}>
                Sync teraz
              </button>
            }
          />
        )}
        {people.kind === "ok" && people.people.length > 0 && (
          // Jedyna tabela w projekcie, która nie miała overflow-x-auto —
          // na wąskim ekranie cztery kolumny (w tym aliasy, zmiennej
          // długości) rozpychały całą stronę w bok zamiast przewijać się
          // we własnym kontenerze.
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-zinc-800 text-xs uppercase tracking-wide text-zinc-500">
                  <th className="py-2 pr-4 font-medium">Imię i nazwisko</th>
                  <th className="py-2 pr-4 font-medium">Email</th>
                  <th className="py-2 pr-4 font-medium">Aliasy</th>
                  <th className="py-2 font-medium">Firma</th>
                </tr>
              </thead>
              <tbody>
                {people.people.map((p) => (
                  <tr key={p.id} className="border-b border-zinc-800/60 last:border-0">
                    <td className="py-2 pr-4 whitespace-nowrap text-zinc-100">{p.full_name}</td>
                    <td className="py-2 pr-4 whitespace-nowrap text-zinc-400">{p.email}</td>
                    <td className="py-2 pr-4 text-zinc-400">{p.aliases.join(", ")}</td>
                    <td className="py-2 whitespace-nowrap text-zinc-400">{p.org ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

export default Settings;
