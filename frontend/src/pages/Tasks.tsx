import { useCallback, useEffect, useState } from "react";

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

async function errorDetail(res: Response): Promise<string> {
  const body = await res.json().catch(() => null);
  return body?.detail ?? `HTTP ${res.status}`;
}

function isOverdue(t: Task): boolean {
  if (t.status !== "open" || !t.deadline) return false;
  return t.deadline < new Date().toISOString().slice(0, 10);
}

function raciSummary(raci: TaskRaci): string {
  const parts: string[] = [];
  if (raci.R) parts.push(`R: ${raci.R}`);
  if (raci.A) parts.push(`A: ${raci.A}`);
  return parts.join(" · ");
}

function Tasks() {
  const [state, setState] = useState<State>({ kind: "loading" });
  const [tasks, setTasks] = useState<Task[]>([]);
  const [topics, setTopics] = useState<Topic[]>([]);
  const [statusFilter, setStatusFilter] = useState<"" | "open" | "done" | "cancelled">("open");
  const [topicFilter, setTopicFilter] = useState("");
  const [overdueOnly, setOverdueOnly] = useState(false);
  const [pendingIds, setPendingIds] = useState<string[]>([]);

  useEffect(() => {
    fetch("/topics")
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
    fetch(`/tasks?${params.toString()}`)
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

  const toggleDone = useCallback(async (t: Task) => {
    const nextStatus = t.status === "done" ? "open" : "done";
    setPendingIds((prev) => [...prev, t.id]);
    try {
      const res = await fetch(`/tasks/${t.id}`, {
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
      <h1 className="text-lg font-medium text-gray-900">Zadania</h1>

      <div className="flex flex-wrap items-center gap-4 rounded-lg border border-gray-200 bg-white px-4 py-3">
        <label className="flex items-center gap-1 text-sm text-gray-600">
          Status
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as typeof statusFilter)}
            className="rounded-md border border-gray-300 px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">wszystkie</option>
            <option value="open">otwarte</option>
            <option value="done">zrobione</option>
            <option value="cancelled">anulowane</option>
          </select>
        </label>
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
        <label className="flex items-center gap-2 text-sm text-gray-600">
          <input
            type="checkbox"
            checked={overdueOnly}
            onChange={(e) => setOverdueOnly(e.target.checked)}
            className="focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          tylko po terminie
        </label>
      </div>

      {state.kind === "loading" && <p className="text-gray-500">Wczytywanie…</p>}
      {state.kind === "error" && <p className="text-red-600">Błąd: {state.message}</p>}
      {state.kind === "ok" && tasks.length === 0 && (
        <p className="text-gray-500">Brak zadań spełniających filtry.</p>
      )}
      {state.kind === "ok" && tasks.length > 0 && (
        <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 text-left text-xs uppercase text-gray-500">
                <th className="px-4 py-2">Zrobione</th>
                <th className="px-4 py-2">Zadanie</th>
                <th className="px-4 py-2">Temat</th>
                <th className="px-4 py-2">RACI</th>
                <th className="px-4 py-2">Deadline</th>
                <th className="px-4 py-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {tasks.map((t) => (
                <tr key={t.id} className="border-b border-gray-100 last:border-0">
                  <td className="px-4 py-2">
                    <input
                      type="checkbox"
                      checked={t.status === "done"}
                      disabled={pendingIds.includes(t.id) || t.status === "cancelled"}
                      onChange={() => toggleDone(t)}
                      className="focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </td>
                  <td className="px-4 py-2 text-gray-900">{t.description}</td>
                  <td className="px-4 py-2 text-gray-600">{t.topic_name ?? "—"}</td>
                  <td className="px-4 py-2 text-gray-600">{raciSummary(t.raci) || "—"}</td>
                  <td
                    className={
                      "px-4 py-2 " + (isOverdue(t) ? "font-medium text-red-600" : "text-gray-600")
                    }
                  >
                    {t.deadline ?? "—"}
                  </td>
                  <td className="px-4 py-2 text-gray-600">{t.status}</td>
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
