import { useEffect, useState } from "react";

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

const POLLING_STATUSES = new Set(["uploaded", "transcribing"]);

const STATUS_LABELS: Record<string, string> = {
  uploaded: "Wgrano, oczekuje na przetwarzanie",
  transcribing: "Transkrypcja w toku…",
  analyzing: "Transkrypcja gotowa (analiza — etap 5)",
  awaiting_review: "Oczekuje na weryfikację",
  approved: "Zatwierdzone",
  failed: "Błąd",
};

function MeetingDetail({ meetingId }: { meetingId: string }) {
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | undefined;

    const load = () => {
      fetch(`/meetings/${meetingId}`)
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
    </div>
  );
}

export default MeetingDetail;
