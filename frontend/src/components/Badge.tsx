type Tone = "neutral" | "positive" | "warning" | "negative";

const toneClasses: Record<Tone, string> = {
  neutral: "bg-zinc-800 text-zinc-300",
  positive: "bg-emerald-500/15 text-emerald-400",
  warning: "bg-amber-500/15 text-amber-400",
  negative: "bg-red-500/15 text-red-400",
};

export function Badge({ tone, children }: { tone: Tone; children: React.ReactNode }) {
  return (
    <span
      className={
        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium " + toneClasses[tone]
      }
    >
      {children}
    </span>
  );
}

const TASK_STATUS: Record<string, { label: string; tone: Tone }> = {
  open: { label: "otwarte", tone: "warning" },
  done: { label: "zrobione", tone: "positive" },
  cancelled: { label: "anulowane", tone: "neutral" },
};

export function TaskStatusBadge({ status }: { status: string }) {
  const entry = TASK_STATUS[status] ?? { label: status, tone: "neutral" as Tone };
  return <Badge tone={entry.tone}>{entry.label}</Badge>;
}

const MEETING_STATUS: Record<string, { label: string; tone: Tone }> = {
  uploaded: { label: "wgrano", tone: "warning" },
  transcribing: { label: "transkrypcja", tone: "warning" },
  analyzing: { label: "analiza", tone: "warning" },
  awaiting_review: { label: "do weryfikacji", tone: "warning" },
  approved: { label: "zatwierdzone", tone: "positive" },
  failed: { label: "błąd", tone: "negative" },
};

export function MeetingStatusBadge({ status }: { status: string }) {
  const entry = MEETING_STATUS[status] ?? { label: status, tone: "neutral" as Tone };
  return <Badge tone={entry.tone}>{entry.label}</Badge>;
}
