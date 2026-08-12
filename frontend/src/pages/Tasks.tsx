import { FunnelSimple, ListChecks } from "@phosphor-icons/react";
import { useCallback, useEffect, useState } from "react";
import { apiFetch, errorDetail } from "../lib/api";
import { todayIso } from "../lib/dates";
import { btnPrimarySm, btnSecondarySm } from "../lib/styles";
import { TaskStatusBadge } from "../components/Badge";
import { EmptyState, ErrorState, LoadingState } from "../components/States";

type Topic = { id: string; name: string; kind: string; notes: string | null };

type TaskRaci = { R: string | null; A: string | null; C: string[]; I: string[] };

type Task = {
  id: string;
  meeting_id: string;
  topic_id: string | null;
  topic_name: string | null;
  description: string;
  deadline: string | null;
  status: "open" | "done" | "cancelled";
  done_at: string | null;
  ai_confidence: number | null;
  sheets_row: number | null;
  raci: TaskRaci;
  created_at: string;
};

type State = { kind: "loading" } | { kind: "ok" } | { kind: "error"; message: string };

function isOverdue(t: Task): boolean {
  if (t.status !== "open" || !t.deadline) return false;
  return t.deadline < todayIso();
}

function raciSummary(raci: TaskRaci): string {
  const parts: string[] = [];
  if (raci.R) parts.push(`R: ${raci.R}`);
  if (raci.A) parts.push(`A: ${raci.A}`);
  return parts.join(" · ");
}

const selectClass =
  "rounded-md border border-zinc-500 bg-zinc-950 px-2 py-1 text-sm text-zinc-100 focus:outline-none focus:ring-2 focus:ring-blue-500";

function Tasks({ navigate }: { navigate: (to: string) => void }) {
  const [state, setState] = useState<State>({ kind: "loading" });
  const [tasks, setTasks] = useState<Task[]>([]);
  const [topics, setTopics] = useState<Topic[]>([]);
  const [statusFilter, setStatusFilter] = useState<"" | "open" | "done" | "cancelled">("open");
  const [topicFilter, setTopicFilter] = useState("");
  const [overdueOnly, setOverdueOnly] = useState(false);
  const [pendingIds, setPendingIds] = useState<string[]>([]);

  useEffect(() => {
    apiFetch("/topics")
      .then(async (res) => {
        if (!res.ok) throw new Error(await errorDetail(res));
        setTopics(await res.json());
      })
      .catch(() => {
        // Filtr po temacie jest wygodą, nie warunkiem działania ekranu — brak
        // listy tematów nie powinien blokować wyświetlenia zadań.
      });
  }, []);

  const load = useCallback(() => {
    setState({ kind: "loading" });
    const params = new URLSearchParams();
    if (statusFilter) params.set("status", statusFilter);
    if (topicFilter) params.set("topic_id", topicFilter);
    if (overdueOnly) params.set("overdue", "true");
    apiFetch(`/tasks?${params.toString()}`)
      .then(async (res) => {
        if (!res.ok) throw new Error(await errorDetail(res));
        const data: Task[] = await res.json();
        setTasks(data);
        setState({ kind: "ok" });
      })
      .catch((err) => setState({ kind: "error", message: String(err.message ?? err) }));
  }, [statusFilter, topicFilter, overdueOnly]);

  useEffect(() => {
    load();
  }, [load]);

  // Pusty wynik ma dwie zupełnie różne przyczyny: nie ma jeszcze żadnych zadań
  // albo filtry je odsiały. Domyślny filtr to „otwarte", więc bez tego
  // rozróżnienia świeży użytkownik dostawał komunikat obwiniający filtry,
  // których sam nie ustawił.
  const filtersActive = statusFilter !== "" || topicFilter !== "" || overdueOnly;

  const clearFilters = useCallback(() => {
    setStatusFilter("");
    setTopicFilter("");
    setOverdueOnly(false);
  }, []);

  const toggleDone = useCallback(async (t: Task) => {
    const nextStatus = t.status === "done" ? "open" : "done";
    setPendingIds((prev) => [...prev, t.id]);
    try {
      const res = await apiFetch(`/tasks/${t.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: nextStatus }),
      });
      if (!res.ok) throw new Error(await errorDetail(res));
      const updated: Task = await res.json();
      setTasks((prev) => prev.map((x) => (x.id === updated.id ? updated : x)));
    } catch (err) {
      setState({ kind: "error", message: String((err as Error).message ?? err) });
    } finally {
      setPendingIds((prev) => prev.filter((id) => id !== t.id));
    }
  }, []);

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-semibold tracking-tight text-white">Zadania</h1>

      <div className="flex flex-wrap items-center gap-4 rounded-xl border border-zinc-800 bg-zinc-900 px-4 py-3">
        <label className="flex items-center gap-2 text-sm text-zinc-400">
          Status
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as typeof statusFilter)}
            className={selectClass}
          >
            <option value="">wszystkie</option>
            <option value="open">otwarte</option>
            <option value="done">zrobione</option>
            <option value="cancelled">anulowane</option>
          </select>
        </label>
        <label className="flex items-center gap-2 text-sm text-zinc-400">
          Temat
          <select
            value={topicFilter}
            onChange={(e) => setTopicFilter(e.target.value)}
            className={selectClass}
          >
            <option value="">wszystkie</option>
            {topics.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>
        </label>
        <label className="flex items-center gap-2 text-sm text-zinc-400">
          <input
            type="checkbox"
            checked={overdueOnly}
            onChange={(e) => setOverdueOnly(e.target.checked)}
            className="focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          tylko po terminie
        </label>
      </div>

      {state.kind === "loading" && <LoadingState />}
      {state.kind === "error" && <ErrorState message={state.message} onRetry={load} />}
      {state.kind === "ok" && tasks.length === 0 && (
        <div className="rounded-xl border border-zinc-800 bg-zinc-900 px-4 py-3">
          {filtersActive ? (
            <EmptyState
              icon={FunnelSimple}
              title="Żadne zadanie nie pasuje do filtrów"
              description="Zawęziłeś widok — zadania mogą istnieć poza tym wyborem. Domyślnie pokazujemy tylko otwarte."
              action={
                <button onClick={clearFilters} className={btnSecondarySm}>
                  Wyczyść filtry
                </button>
              }
            />
          ) : (
            <EmptyState
              icon={ListChecks}
              title="Nie ma jeszcze żadnych zadań"
              description="Zadania powstają automatycznie z zatwierdzonych spotkań — z terminem, rolą wykonawcy i osobą odpowiedzialną za efekt. Zacznij od wgrania rozmowy."
              action={
                <button onClick={() => navigate("/upload")} className={btnPrimarySm}>
                  Dodaj spotkanie
                </button>
              }
            />
          )}
        </div>
      )}
      {state.kind === "ok" && tasks.length > 0 && (
        <div className="overflow-x-auto rounded-xl border border-zinc-800 bg-zinc-900">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-zinc-800 text-left text-xs uppercase tracking-wide text-zinc-400">
                <th className="px-4 py-2.5">Zrobione</th>
                <th className="px-4 py-2.5">Zadanie</th>
                <th className="px-4 py-2.5">Temat</th>
                <th className="px-4 py-2.5">RACI</th>
                <th className="px-4 py-2.5">Deadline</th>
                <th className="px-4 py-2.5">Status</th>
              </tr>
            </thead>
            <tbody>
              {tasks.map((t) => (
                <tr key={t.id} className="border-b border-zinc-800/60 last:border-0 hover:bg-zinc-800/30">
                  <td className="px-4 py-2.5">
                    {/* Bez etykiety obok — jedyny sposób, żeby czytnik ekranu
                        wiedział, KTÓREGO zadania dotyczy, to opis w aria-label. */}
                    <input
                      type="checkbox"
                      checked={t.status === "done"}
                      disabled={pendingIds.includes(t.id) || t.status === "cancelled"}
                      onChange={() => toggleDone(t)}
                      aria-label={`Oznacz jako ${t.status === "done" ? "otwarte" : "zrobione"}: ${t.description}`}
                      className="focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </td>
                  <td className="px-4 py-2.5 text-zinc-100">{t.description}</td>
                  <td className="px-4 py-2.5 text-zinc-400">{t.topic_name ?? "—"}</td>
                  <td className="px-4 py-2.5 text-zinc-400">{raciSummary(t.raci) || "—"}</td>
                  <td
                    className={
                      "px-4 py-2.5 " + (isOverdue(t) ? "font-medium text-red-400" : "text-zinc-400")
                    }
                  >
                    {t.deadline ?? "—"}
                  </td>
                  <td className="px-4 py-2.5">
                    <TaskStatusBadge status={t.status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default Tasks;
