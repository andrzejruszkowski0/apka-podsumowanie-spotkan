import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "../lib/api";

type Topic = { id: string; name: string; kind: string; notes: string | null };

type Decision = {
  id: string;
  meeting_id: string;
  topic_id: string | null;
  topic_name: string | null;
  statement: string;
  decided_on: string;
  category: string | null;
  decided_by: string | null;
  created_at: string;
};

type State = { kind: "loading" } | { kind: "ok" } | { kind: "error"; message: string };

async function errorDetail(res: Response): Promise<string> {
  const body = await res.json().catch(() => null);
  return body?.detail ?? `HTTP ${res.status}`;
}

function Decisions() {
  const [state, setState] = useState<State>({ kind: "loading" });
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [topics, setTopics] = useState<Topic[]>([]);
  const [topicFilter, setTopicFilter] = useState("");
  const [queryInput, setQueryInput] = useState("");
  const [activeQuery, setActiveQuery] = useState("");

  useEffect(() => {
    apiFetch("/topics")
      .then(async (res) => {
        if (!res.ok) throw new Error(await errorDetail(res));
        setTopics(await res.json());
      })
      .catch(() => {
        // Filtr po temacie jest wygodą, nie warunkiem działania ekranu — brak
        // listy tematów nie powinien blokować wyświetlenia decyzji.
      });
  }, []);

  const load = useCallback(() => {
    setState({ kind: "loading" });
    const params = new URLSearchParams();
    if (topicFilter) params.set("topic_id", topicFilter);
    if (activeQuery) params.set("q", activeQuery);
    apiFetch(`/decisions?${params.toString()}`)
      .then(async (res) => {
        if (!res.ok) throw new Error(await errorDetail(res));
        const data: Decision[] = await res.json();
        setDecisions(data);
        setState({ kind: "ok" });
      })
      .catch((err) => setState({ kind: "error", message: String(err.message ?? err) }));
  }, [topicFilter, activeQuery]);

  useEffect(() => {
    load();
  }, [load]);

  const runSearch = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      setActiveQuery(queryInput.trim());
    },
    [queryInput],
  );

  const clearSearch = useCallback(() => {
    setQueryInput("");
    setActiveQuery("");
  }, []);

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-lg font-medium text-gray-900">Rejestr decyzji</h1>

      <div className="flex flex-wrap items-center gap-4 rounded-lg border border-gray-200 bg-white px-4 py-3">
        <label className="flex items-center gap-1 text-sm text-gray-600">
          Temat
          <select
            value={topicFilter}
            onChange={(e) => setTopicFilter(e.target.value)}
            className="rounded-md border border-gray-300 px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">wszystkie</option>
            {topics.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>
        </label>
        <form onSubmit={runSearch} className="flex items-center gap-2">
          <input
            type="text"
            value={queryInput}
            onChange={(e) => setQueryInput(e.target.value)}
            placeholder="Szukaj semantycznie…"
            className="rounded-md border border-gray-300 px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="submit"
            className="rounded-md bg-blue-600 px-3 py-1 text-sm font-medium text-white hover:bg-blue-700"
          >
            Szukaj
          </button>
          {activeQuery && (
            <button
              type="button"
              onClick={clearSearch}
              className="rounded-md border border-gray-300 px-3 py-1 text-sm text-gray-600 hover:bg-gray-100"
            >
              Wyczyść
            </button>
          )}
        </form>
      </div>

      {activeQuery && (
        <p className="text-sm text-gray-500">Wyniki wyszukiwania semantycznego dla „{activeQuery}”.</p>
      )}

      {state.kind === "loading" && <p className="text-gray-500">Wczytywanie…</p>}
      {state.kind === "error" && <p className="text-red-600">Błąd: {state.message}</p>}
      {state.kind === "ok" && decisions.length === 0 && (
        <p className="text-gray-500">Brak decyzji spełniających kryteria.</p>
      )}
      {state.kind === "ok" && decisions.length > 0 && (
        <div className="flex flex-col gap-3">
          {decisions.map((d) => (
            <div key={d.id} className="rounded-lg border border-gray-200 bg-white px-4 py-3">
              <p className="text-gray-900">{d.statement}</p>
              <div className="mt-2 flex flex-wrap gap-3 text-xs text-gray-500">
                <span>{d.decided_on}</span>
                {d.topic_name && <span>· {d.topic_name}</span>}
                {d.category && <span>· {d.category}</span>}
                {d.decided_by && <span>· zdecydował: {d.decided_by}</span>}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default Decisions;
