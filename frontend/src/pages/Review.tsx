import { useCallback, useEffect, useMemo, useState } from "react";
import { apiFetch } from "../lib/api";

type Person = { id: string; full_name: string; email: string; aliases: string[]; org: string | null };

type RaciField = { person_id: string | null; raw: string | null };
type RaciMultiField = { person_ids: string[]; raw: string[] };

type ReviewTask = {
  id: string;
  description: string;
  deadline: string | null;
  ai_confidence: number | null;
  quote: string | null;
  edited_by_user: boolean;
  unresolved: boolean;
  raci: { R: RaciField; A: RaciField; C: RaciMultiField; I: RaciMultiField };
};

type ReviewDecision = {
  id: string;
  statement: string;
  decided_on: string;
  category: string | null;
  ai_confidence: number | null;
  quote: string | null;
  unresolved: boolean;
  decided_by: RaciField;
};

type ReviewPayload = { tasks: ReviewTask[]; decisions: ReviewDecision[] };

type Meeting = { id: string; title: string; status: string };

type State =
  | { kind: "loading" }
  | { kind: "not_reviewable"; status: string }
  | { kind: "ok" }
  | { kind: "error"; message: string };

async function errorDetail(res: Response): Promise<string> {
  const body = await res.json().catch(() => null);
  return body?.detail ?? `HTTP ${res.status}`;
}

function computeTaskUnresolved(t: ReviewTask): boolean {
  if (t.raci.R.raw && !t.raci.R.person_id) return true;
  if (t.raci.A.raw && !t.raci.A.person_id) return true;
  if (t.raci.C.raw.length > t.raci.C.person_ids.length) return true;
  if (t.raci.I.raw.length > t.raci.I.person_ids.length) return true;
  return false;
}

function computeDecisionUnresolved(d: ReviewDecision): boolean {
  return Boolean(d.decided_by.raw) && !d.decided_by.person_id;
}

const inputClass =
  "rounded-md border border-gray-300 px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500";

function ConfidenceBadge({ value }: { value: number | null }) {
  if (value === null) return null;
  const low = value < 0.7;
  return (
    <span
      className={
        "rounded px-1.5 py-0.5 text-xs font-medium " +
        (low ? "bg-amber-100 text-amber-800" : "bg-gray-100 text-gray-500")
      }
    >
      pewność: {Math.round(value * 100)}%
    </span>
  );
}

function PersonSelect({
  value,
  onChange,
  people,
  rawLabel,
}: {
  value: string | null;
  onChange: (v: string | null) => void;
  people: Person[];
  rawLabel: string | null;
}) {
  return (
    <select
      value={value ?? ""}
      onChange={(e) => onChange(e.target.value || null)}
      className={inputClass}
    >
      <option value="">
        {rawLabel ? `— nierozwiązane: „${rawLabel}” —` : "— brak —"}
      </option>
      {people.map((p) => (
        <option key={p.id} value={p.id}>
          {p.full_name}
        </option>
      ))}
    </select>
  );
}

function PersonChecklist({
  selected,
  onChange,
  people,
  rawNames,
}: {
  selected: string[];
  onChange: (ids: string[]) => void;
  people: Person[];
  rawNames: string[];
}) {
  const toggle = (id: string) => {
    onChange(selected.includes(id) ? selected.filter((x) => x !== id) : [...selected, id]);
  };
  return (
    <div className="flex flex-col gap-1">
      {rawNames.length > 0 && (
        <p className="text-xs text-gray-500">AI wskazało: {rawNames.join(", ")}</p>
      )}
      <div className="flex flex-wrap gap-2">
        {people.map((p) => (
          <label
            key={p.id}
            className="flex items-center gap-1 rounded border border-gray-200 px-2 py-1 text-xs"
          >
            <input
              type="checkbox"
              checked={selected.includes(p.id)}
              onChange={() => toggle(p.id)}
              className="focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {p.full_name}
          </label>
        ))}
      </div>
    </div>
  );
}

function TaskCard({
  task,
  people,
  onChange,
  onDelete,
}: {
  task: ReviewTask;
  people: Person[];
  onChange: (t: ReviewTask) => void;
  onDelete: () => void;
}) {
  const unresolved = computeTaskUnresolved(task);
  return (
    <div
      className={
        "rounded-lg border px-4 py-3 " +
        (unresolved ? "border-red-300 bg-red-50" : task.ai_confidence !== null && task.ai_confidence < 0.7 ? "border-amber-300 bg-amber-50" : "border-gray-200 bg-white")
      }
    >
      <div className="flex items-start justify-between gap-3">
        <textarea
          value={task.description}
          onChange={(e) => onChange({ ...task, description: e.target.value })}
          rows={2}
          className={inputClass + " flex-1"}
        />
        <button
          onClick={onDelete}
          className="shrink-0 rounded-md border border-gray-300 px-2 py-1 text-xs text-gray-600 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          Usuń
        </button>
      </div>

      <div className="mt-2 flex flex-wrap items-center gap-3">
        <label className="flex items-center gap-1 text-xs text-gray-600">
          Deadline
          <input
            type="date"
            value={task.deadline ?? ""}
            onChange={(e) => onChange({ ...task, deadline: e.target.value || null })}
            className={inputClass}
          />
        </label>
        <ConfidenceBadge value={task.ai_confidence} />
        {unresolved && (
          <span className="rounded bg-red-100 px-1.5 py-0.5 text-xs font-medium text-red-700">
            nierozwiązane nazwisko
          </span>
        )}
      </div>

      <div className="mt-3 grid grid-cols-2 gap-3">
        <label className="flex flex-col gap-1 text-xs text-gray-600">
          R (wykonawca)
          <PersonSelect
            value={task.raci.R.person_id}
            onChange={(v) => onChange({ ...task, raci: { ...task.raci, R: { ...task.raci.R, person_id: v } } })}
            people={people}
            rawLabel={task.raci.R.raw}
          />
        </label>
        <label className="flex flex-col gap-1 text-xs text-gray-600">
          A (odpowiedzialny)
          <PersonSelect
            value={task.raci.A.person_id}
            onChange={(v) => onChange({ ...task, raci: { ...task.raci, A: { ...task.raci.A, person_id: v } } })}
            people={people}
            rawLabel={task.raci.A.raw}
          />
        </label>
      </div>

      <div className="mt-3 grid grid-cols-2 gap-3">
        <div>
          <span className="text-xs text-gray-600">C (konsultowani)</span>
          <PersonChecklist
            selected={task.raci.C.person_ids}
            onChange={(ids) => onChange({ ...task, raci: { ...task.raci, C: { ...task.raci.C, person_ids: ids } } })}
            people={people}
            rawNames={task.raci.C.raw}
          />
        </div>
        <div>
          <span className="text-xs text-gray-600">I (informowani)</span>
          <PersonChecklist
            selected={task.raci.I.person_ids}
            onChange={(ids) => onChange({ ...task, raci: { ...task.raci, I: { ...task.raci.I, person_ids: ids } } })}
            people={people}
            rawNames={task.raci.I.raw}
          />
        </div>
      </div>

      {task.quote && (
        <details className="mt-2">
          <summary className="cursor-pointer text-xs text-gray-500 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500">
            Cytat uzasadniający
          </summary>
          <p className="mt-1 text-xs italic text-gray-600">„{task.quote}”</p>
        </details>
      )}
    </div>
  );
}

function DecisionCard({
  decision,
  people,
  onChange,
  onDelete,
}: {
  decision: ReviewDecision;
  people: Person[];
  onChange: (d: ReviewDecision) => void;
  onDelete: () => void;
}) {
  const unresolved = computeDecisionUnresolved(decision);
  return (
    <div
      className={
        "rounded-lg border px-4 py-3 " +
        (unresolved ? "border-red-300 bg-red-50" : decision.ai_confidence !== null && decision.ai_confidence < 0.7 ? "border-amber-300 bg-amber-50" : "border-gray-200 bg-white")
      }
    >
      <div className="flex items-start justify-between gap-3">
        <textarea
          value={decision.statement}
          onChange={(e) => onChange({ ...decision, statement: e.target.value })}
          rows={2}
          className={inputClass + " flex-1"}
        />
        <button
          onClick={onDelete}
          className="shrink-0 rounded-md border border-gray-300 px-2 py-1 text-xs text-gray-600 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          Usuń
        </button>
      </div>

      <div className="mt-2 flex flex-wrap items-center gap-3">
        <label className="flex items-center gap-1 text-xs text-gray-600">
          Data
          <input
            type="date"
            value={decision.decided_on}
            onChange={(e) => onChange({ ...decision, decided_on: e.target.value })}
            className={inputClass}
          />
        </label>
        <label className="flex items-center gap-1 text-xs text-gray-600">
          Kategoria
          <input
            type="text"
            value={decision.category ?? ""}
            onChange={(e) => onChange({ ...decision, category: e.target.value || null })}
            className={inputClass}
          />
        </label>
        <ConfidenceBadge value={decision.ai_confidence} />
        {unresolved && (
          <span className="rounded bg-red-100 px-1.5 py-0.5 text-xs font-medium text-red-700">
            nierozwiązane nazwisko
          </span>
        )}
      </div>

      <label className="mt-3 flex flex-col gap-1 text-xs text-gray-600">
        Kto zdecydował
        <PersonSelect
          value={decision.decided_by.person_id}
          onChange={(v) => onChange({ ...decision, decided_by: { ...decision.decided_by, person_id: v } })}
          people={people}
          rawLabel={decision.decided_by.raw}
        />
      </label>

      {decision.quote && (
        <details className="mt-2">
          <summary className="cursor-pointer text-xs text-gray-500 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500">
            Cytat uzasadniający
          </summary>
          <p className="mt-1 text-xs italic text-gray-600">„{decision.quote}”</p>
        </details>
      )}
    </div>
  );
}

function Review({ meetingId, navigate }: { meetingId: string; navigate: (to: string) => void }) {
  const [state, setState] = useState<State>({ kind: "loading" });
  const [people, setPeople] = useState<Person[]>([]);
  const [tasks, setTasks] = useState<ReviewTask[]>([]);
  const [decisions, setDecisions] = useState<ReviewDecision[]>([]);
  const [deletedTaskIds, setDeletedTaskIds] = useState<string[]>([]);
  const [deletedDecisionIds, setDeletedDecisionIds] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      apiFetch(`/meetings/${meetingId}`).then(async (res) => {
        if (!res.ok) throw new Error(await errorDetail(res));
        return res.json() as Promise<Meeting>;
      }),
      apiFetch("/people").then(async (res) => {
        if (!res.ok) throw new Error(await errorDetail(res));
        return res.json() as Promise<Person[]>;
      }),
    ])
      .then(async ([meeting, peopleList]) => {
        if (cancelled) return;
        setPeople(peopleList);
        if (meeting.status !== "awaiting_review") {
          setState({ kind: "not_reviewable", status: meeting.status });
          return;
        }
        const res = await apiFetch(`/meetings/${meetingId}/review`);
        if (!res.ok) throw new Error(await errorDetail(res));
        const payload: ReviewPayload = await res.json();
        setTasks(payload.tasks);
        setDecisions(payload.decisions);
        setState({ kind: "ok" });
      })
      .catch((err) => {
        if (!cancelled) setState({ kind: "error", message: String(err.message ?? err) });
      });
    return () => {
      cancelled = true;
    };
  }, [meetingId]);

  const anyUnresolved = useMemo(
    () => tasks.some(computeTaskUnresolved) || decisions.some(computeDecisionUnresolved),
    [tasks, decisions],
  );

  const deleteTask = useCallback((id: string) => {
    setTasks((prev) => prev.filter((t) => t.id !== id));
    setDeletedTaskIds((prev) => [...prev, id]);
  }, []);

  const deleteDecision = useCallback((id: string) => {
    setDecisions((prev) => prev.filter((d) => d.id !== id));
    setDeletedDecisionIds((prev) => [...prev, id]);
  }, []);

  const approve = useCallback(async () => {
    setSaving(true);
    setSaveError(null);
    try {
      const putRes = await apiFetch(`/meetings/${meetingId}/review`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tasks: tasks.map((t) => ({
            id: t.id,
            description: t.description,
            deadline: t.deadline,
            raci: {
              r_person_id: t.raci.R.person_id,
              a_person_id: t.raci.A.person_id,
              c_person_ids: t.raci.C.person_ids,
              i_person_ids: t.raci.I.person_ids,
            },
          })),
          decisions: decisions.map((d) => ({
            id: d.id,
            statement: d.statement,
            category: d.category,
            decided_on: d.decided_on,
            decided_by_person_id: d.decided_by.person_id,
          })),
          deleted_task_ids: deletedTaskIds,
          deleted_decision_ids: deletedDecisionIds,
        }),
      });
      if (!putRes.ok) throw new Error(await errorDetail(putRes));

      const approveRes = await apiFetch(`/meetings/${meetingId}/approve`, { method: "POST" });
      if (!approveRes.ok) throw new Error(await errorDetail(approveRes));

      navigate(`/meetings/${meetingId}`);
    } catch (err) {
      setSaveError(String((err as Error).message ?? err));
    } finally {
      setSaving(false);
    }
  }, [meetingId, tasks, decisions, deletedTaskIds, deletedDecisionIds, navigate]);

  if (state.kind === "loading") return <p className="text-gray-500">Wczytywanie…</p>;
  if (state.kind === "error") return <p className="text-red-600">Błąd: {state.message}</p>;
  if (state.kind === "not_reviewable") {
    return (
      <p className="text-gray-600">
        To spotkanie nie jest w trakcie weryfikacji (status: {state.status}).{" "}
        <a
          href={`/meetings/${meetingId}`}
          onClick={(e) => {
            e.preventDefault();
            navigate(`/meetings/${meetingId}`);
          }}
          className="text-blue-600 hover:underline"
        >
          Wróć do spotkania
        </a>
        .
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-medium text-gray-900">Weryfikacja</h1>
        <button
          onClick={approve}
          disabled={saving || anyUnresolved}
          className="rounded-md bg-blue-600 px-4 py-2 text-white font-medium hover:bg-blue-700 disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
          title={anyUnresolved ? "Rozwiąż wszystkie nazwiska przed zatwierdzeniem" : undefined}
        >
          {saving ? "Zapisywanie…" : "Zatwierdź i zapisz"}
        </button>
      </div>
      {saveError && <p className="text-sm text-red-600">Błąd: {saveError}</p>}

      <section>
        <h2 className="mb-2 font-medium text-gray-900">Zadania ({tasks.length})</h2>
        <div className="flex flex-col gap-3">
          {tasks.length === 0 && <p className="text-sm text-gray-500">Brak zadań.</p>}
          {tasks.map((t) => (
            <TaskCard
              key={t.id}
              task={t}
              people={people}
              onChange={(nt) => setTasks((prev) => prev.map((x) => (x.id === nt.id ? nt : x)))}
              onDelete={() => deleteTask(t.id)}
            />
          ))}
        </div>
      </section>

      <section>
        <h2 className="mb-2 font-medium text-gray-900">Decyzje ({decisions.length})</h2>
        <div className="flex flex-col gap-3">
          {decisions.length === 0 && <p className="text-sm text-gray-500">Brak decyzji.</p>}
          {decisions.map((d) => (
            <DecisionCard
              key={d.id}
              decision={d}
              people={people}
              onChange={(nd) => setDecisions((prev) => prev.map((x) => (x.id === nd.id ? nd : x)))}
              onDelete={() => deleteDecision(d.id)}
            />
          ))}
        </div>
      </section>
    </div>
  );
}

export default Review;
