import { useCallback, useEffect, useState } from "react";
import { apiFetch, errorDetail } from "../lib/api";

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
    <div className="rounded-lg border border-gray-200 bg-white px-8 py-6 shadow-sm">
      <h2 className="mb-3 font-medium text-gray-900">Szkic maila podsumowującego</h2>

      <div className="flex flex-wrap items-end gap-4">
        <label className="flex flex-col gap-1 text-sm text-gray-600">
          Szablon
          <select
            value={template}
            onChange={(e) => {
              setTemplate(e.target.value as Template);
              setDraft({ kind: "idle" });
              setSend({ kind: "idle" });
            }}
            className="rounded-md border border-gray-300 px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
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
          className="rounded-md bg-blue-600 px-4 py-2 text-white font-medium hover:bg-blue-700 disabled:opacity-50"
        >
          {draft.kind === "loading" ? "Generuję…" : "Podgląd"}
        </button>
      </div>

      {draft.kind === "error" && <p className="mt-3 text-sm text-red-600">Błąd: {draft.message}</p>}

      {draft.kind === "ok" && (
        <div className="mt-4 flex flex-col gap-3">
          <label className="flex flex-col gap-1 text-sm text-gray-600">
            Temat
            <input
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              className="rounded-md border border-gray-300 px-2 py-1 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </label>
          <label className="flex flex-col gap-1 text-sm text-gray-600">
            Treść
            <textarea
              value={body}
              onChange={(e) => setBody(e.target.value)}
              rows={12}
              className="rounded-md border border-gray-300 px-2 py-2 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </label>

          <div className="flex flex-wrap items-end gap-4">
            <label className="flex flex-col gap-1 text-sm text-gray-600">
              Do
              <input
                value={to}
                onChange={(e) => setTo(e.target.value)}
                placeholder="adres@przyklad.pl"
                className="w-64 rounded-md border border-gray-300 px-2 py-1 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </label>
            <label className="flex flex-col gap-1 text-sm text-gray-600">
              Dw (opcjonalnie)
              <input
                value={cc}
                onChange={(e) => setCc(e.target.value)}
                placeholder="adres@przyklad.pl"
                className="w-64 rounded-md border border-gray-300 px-2 py-1 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </label>
            <button
              onClick={sendDraft}
              disabled={!to.trim() || send.kind === "loading" || send.kind === "done"}
              className="rounded-md bg-blue-600 px-4 py-2 text-white font-medium hover:bg-blue-700 disabled:opacity-50"
            >
              {send.kind === "loading" ? "Wysyłam…" : send.kind === "done" ? "Wysłano" : "Wyślij"}
            </button>
          </div>
          {send.kind === "error" && <p className="text-sm text-red-600">Błąd: {send.message}</p>}
          {send.kind === "done" && <p className="text-sm text-green-600">Mail wysłany.</p>}
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
  }, [meetingId]);

  if (state.kind === "loading") {
    return <p className="text-gray-500">Wczytywanie…</p>;
  }
  if (state.kind === "error") {
    return <p className="text-red-600">Błąd: {state.message}</p>;
  }

  const { meeting } = state;

  return (
    <div className="flex flex-col gap-4">
      <div className="rounded-lg border border-gray-200 bg-white px-8 py-6 shadow-sm">
        <h1 className="text-lg font-medium text-gray-900">{meeting.title}</h1>
        <p className="text-sm text-gray-500">
          {meeting.meeting_date} · {meeting.source_type === "audio" ? "audio" : "tekst"}
        </p>
        <p className="mt-3">
          Status:{" "}
          <span
            className={
              meeting.status === "failed"
                ? "font-medium text-red-600"
                : POLLING_STATUSES.has(meeting.status)
                  ? "font-medium text-amber-600"
                  : "font-medium text-green-600"
            }
          >
            {STATUS_LABELS[meeting.status] ?? meeting.status}
          </span>
        </p>
        {meeting.error_message && (
          <p className="mt-2 text-sm text-red-600">{meeting.error_message}</p>
        )}
        {meeting.status === "awaiting_review" && (
          <a
            href={`/meetings/${meeting.id}/review`}
            onClick={(e) => {
              e.preventDefault();
              navigate(`/meetings/${meeting.id}/review`);
            }}
            className="mt-4 inline-block rounded-md bg-blue-600 px-4 py-2 text-white font-medium hover:bg-blue-700"
          >
            Przejdź do weryfikacji
          </a>
        )}
      </div>

      <div className="rounded-lg border border-gray-200 bg-white px-8 py-6 shadow-sm">
        <h2 className="mb-3 font-medium text-gray-900">Transkrypt</h2>
        {meeting.transcript_parts.length === 0 ? (
          <p className="text-gray-500">Transkrypt jeszcze niedostępny.</p>
        ) : (
          <pre className="whitespace-pre-wrap font-sans text-sm text-gray-800">
            {meeting.transcript}
          </pre>
        )}
      </div>

      {DRAFT_READY_STATUSES.has(meeting.status) && <DraftPanel meetingId={meeting.id} />}
    </div>
  );
}

export default MeetingDetail;
