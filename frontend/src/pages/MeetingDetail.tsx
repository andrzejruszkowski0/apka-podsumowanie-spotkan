import { ArrowRight, Eye, PaperPlaneTilt } from "@phosphor-icons/react";
import { useCallback, useEffect, useState } from "react";
import { apiFetch, errorDetail } from "../lib/api";
import { Badge } from "../components/Badge";
import { ErrorState, LoadingState } from "../components/States";
import { btnPrimary } from "../lib/styles";

type TranscriptPart = { part_index: number; content: string };

type Meeting = {
  id: string;
  topic_id: string | null;
  title: string;
  meeting_date: string;
  source_type: "audio" | "text";
  status: string;
  error_message: string | null;
  created_at: string;
  transcript_parts: TranscriptPart[];
  transcript: string;
};

type State =
  | { kind: "loading" }
  | { kind: "ok"; meeting: Meeting }
  | { kind: "error"; message: string };

const POLLING_STATUSES = new Set(["uploaded", "transcribing", "analyzing"]);

const STATUS_LABELS: Record<string, string> = {
  uploaded: "Wgrano, oczekuje na przetwarzanie",
  transcribing: "Transkrypcja w toku…",
  analyzing: "Ekstrakcja zadań i decyzji w toku…",
  awaiting_review: "Oczekuje na weryfikację",
  approved: "Zatwierdzone",
  failed: "Błąd",
};

// Ekran ma sens dopiero, gdy zadania/decyzje istnieją (SPEC.md §10.5, etap 10) —
// czyli po zakończonej ekstrakcji, niezależnie od tego, czy właściciel zdążył
// już zatwierdzić spotkanie.
const DRAFT_READY_STATUSES = new Set(["awaiting_review", "approved"]);

type Template = "formal_board" | "supplier" | "team_casual";

const TEMPLATE_LABELS: Record<Template, string> = {
  formal_board: "Raport dla zarządu",
  supplier: "Podsumowanie dla dostawcy",
  team_casual: "Wiadomość robocza dla zespołu",
};

type DraftPreview = { template: Template; subject: string; body: string };

type DraftState =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "ok"; draft: DraftPreview }
  | { kind: "error"; message: string };

type SendState =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "done" }
  | { kind: "error"; message: string };

const selectClass =
  "rounded-md border border-zinc-500 bg-zinc-950 px-2 py-1 text-sm text-zinc-100 focus:outline-none focus:ring-2 focus:ring-blue-500";

function DraftPanel({ meetingId }: { meetingId: string }) {
  const [template, setTemplate] = useState<Template>("formal_board");
  const [draft, setDraft] = useState<DraftState>({ kind: "idle" });
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [to, setTo] = useState("");
  const [cc, setCc] = useState("");
  const [send, setSend] = useState<SendState>({ kind: "idle" });

  const generatePreview = useCallback(() => {
    setDraft({ kind: "loading" });
    setSend({ kind: "idle" });
    apiFetch(`/meetings/${meetingId}/draft`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ template }),
    })
      .then(async (res) => {
        if (!res.ok) throw new Error(await errorDetail(res));
        const data: DraftPreview = await res.json();
        setDraft({ kind: "ok", draft: data });
        setSubject(data.subject);
        setBody(data.body);
      })
      .catch((err) => setDraft({ kind: "error", message: String(err.message ?? err) }));
  }, [meetingId, template]);

  const sendDraft = useCallback(() => {
    if (draft.kind !== "ok" || !to.trim()) return;
    setSend({ kind: "loading" });
    apiFetch(`/meetings/${meetingId}/draft/send`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        template: draft.draft.template,
        subject,
        body,
        to: to.trim(),
        cc: cc.trim() || null,
      }),
    })
      .then(async (res) => {
        if (!res.ok) throw new Error(await errorDetail(res));
        setSend({ kind: "done" });
      })
      .catch((err) => setSend({ kind: "error", message: String(err.message ?? err) }));
  }, [meetingId, draft, subject, body, to, cc]);

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900 px-4 sm:px-8 py-6">
      <h2 className="mb-3 font-medium text-zinc-100">Szkic maila podsumowującego</h2>

      <div className="flex flex-wrap items-end gap-4">
        <label className="flex flex-col gap-1.5 text-sm text-zinc-400">
          Szablon
          <select
            value={template}
            onChange={(e) => {
              setTemplate(e.target.value as Template);
              setDraft({ kind: "idle" });
              setSend({ kind: "idle" });
            }}
            className={selectClass}
          >
            {(Object.keys(TEMPLATE_LABELS) as Template[]).map((t) => (
              <option key={t} value={t}>
                {TEMPLATE_LABELS[t]}
              </option>
            ))}
          </select>
        </label>
        <button
          onClick={generatePreview}
          disabled={draft.kind === "loading"}
          className={"flex items-center gap-1.5 " + btnPrimary}
        >
          <Eye size={16} weight="bold" />
          {draft.kind === "loading" ? "Generuję…" : "Podgląd"}
        </button>
      </div>

      {draft.kind === "error" && <p className="mt-3 text-sm text-red-400">Błąd: {draft.message}</p>}

      {draft.kind === "ok" && (
        <div className="mt-4 flex flex-col gap-3">
          <label className="flex flex-col gap-1.5 text-sm text-zinc-400">
            Temat
            <input
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              className={selectClass + " text-zinc-100"}
            />
          </label>
          <label className="flex flex-col gap-1.5 text-sm text-zinc-400">
            Treść
            <textarea
              value={body}
              onChange={(e) => setBody(e.target.value)}
              rows={12}
              className={selectClass + " py-2 text-zinc-100"}
            />
          </label>

          <div className="flex flex-wrap items-end gap-4">
            <label className="flex flex-col gap-1.5 text-sm text-zinc-400">
              Do
              <input
                value={to}
                onChange={(e) => setTo(e.target.value)}
                placeholder="adres@przyklad.pl"
                className={selectClass + " w-64 text-zinc-100 placeholder-zinc-400"}
              />
            </label>
            <label className="flex flex-col gap-1.5 text-sm text-zinc-400">
              Dw (opcjonalnie)
              <input
                value={cc}
                onChange={(e) => setCc(e.target.value)}
                placeholder="adres@przyklad.pl"
                className={selectClass + " w-64 text-zinc-100 placeholder-zinc-400"}
              />
            </label>
            <button
              onClick={sendDraft}
              disabled={!to.trim() || send.kind === "loading" || send.kind === "done"}
              className={"flex items-center gap-1.5 " + btnPrimary}
            >
              <PaperPlaneTilt size={16} weight="bold" />
              {send.kind === "loading" ? "Wysyłam…" : send.kind === "done" ? "Wysłano" : "Wyślij"}
            </button>
          </div>
          {send.kind === "error" && <p className="text-sm text-red-400">Błąd: {send.message}</p>}
          {send.kind === "done" && <p className="text-sm text-emerald-400">Mail wysłany.</p>}
        </div>
      )}
    </div>
  );
}

function MeetingDetail({
  meetingId,
  navigate,
}: {
  meetingId: string;
  navigate: (to: string) => void;
}) {
  const [state, setState] = useState<State>({ kind: "loading" });
  // Wybija cały efekt na nowo bez zmiany innych zależności — jedyny czysty
  // sposób na retry, gdy `load` żyje wewnątrz efektu (rekurencyjny setTimeout
  // do pollingu musi widzieć świeże domknięcie `cancelled`/`timer`).
  const [retryTick, setRetryTick] = useState(0);

  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | undefined;

    const load = () => {
      apiFetch(`/meetings/${meetingId}`)
        .then(async (res) => {
          if (!res.ok) {
            const body = await res.json().catch(() => null);
            throw new Error(body?.detail ?? `HTTP ${res.status}`);
          }
          return res.json();
        })
        .then((data: Meeting) => {
          if (cancelled) return;
          setState({ kind: "ok", meeting: data });
          if (POLLING_STATUSES.has(data.status)) {
            timer = setTimeout(load, 2000);
          }
        })
        .catch((err) => {
          if (!cancelled) setState({ kind: "error", message: String(err.message ?? err) });
        });
    };

    load();
    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
    };
  }, [meetingId, retryTick]);

  if (state.kind === "loading") {
    return <LoadingState />;
  }
  if (state.kind === "error") {
    const retry = () => {
      setState({ kind: "loading" });
      setRetryTick((v) => v + 1);
    };
    return <ErrorState message={state.message} onRetry={retry} />;
  }

  const { meeting } = state;

  return (
    <div className="flex flex-col gap-4">
      <div className="rounded-xl border border-zinc-800 bg-zinc-900 px-4 sm:px-8 py-6">
        <h1 className="text-xl font-semibold tracking-tight text-white">{meeting.title}</h1>
        <p className="text-sm text-zinc-400">
          {meeting.meeting_date} · {meeting.source_type === "audio" ? "audio" : "tekst"}
        </p>
        <div className="mt-3 flex items-center gap-2">
          <span className="text-sm text-zinc-400">Status:</span>
          <Badge
            tone={
              meeting.status === "failed"
                ? "negative"
                : POLLING_STATUSES.has(meeting.status)
                  ? "warning"
                  : "positive"
            }
          >
            {STATUS_LABELS[meeting.status] ?? meeting.status}
          </Badge>
        </div>
        {meeting.error_message && (
          <p className="mt-2 text-sm text-red-400">{meeting.error_message}</p>
        )}
        {meeting.status === "awaiting_review" && (
          <a
            href={`/meetings/${meeting.id}/review`}
            onClick={(e) => {
              e.preventDefault();
              navigate(`/meetings/${meeting.id}/review`);
            }}
            className={"mt-4 inline-flex items-center gap-1.5 " + btnPrimary}
          >
            Przejdź do weryfikacji
            <ArrowRight size={16} weight="bold" />
          </a>
        )}
      </div>

      <div className="rounded-xl border border-zinc-800 bg-zinc-900 px-4 sm:px-8 py-6">
        <h2 className="mb-3 font-medium text-zinc-100">Transkrypt</h2>
        {meeting.transcript_parts.length === 0 ? (
          <p className="text-zinc-400">Transkrypt jeszcze niedostępny.</p>
        ) : (
          <pre className="whitespace-pre-wrap font-sans text-sm text-zinc-300">
            {meeting.transcript}
          </pre>
        )}
      </div>

      {DRAFT_READY_STATUSES.has(meeting.status) && <DraftPanel meetingId={meeting.id} />}
    </div>
  );
}

export default MeetingDetail;
