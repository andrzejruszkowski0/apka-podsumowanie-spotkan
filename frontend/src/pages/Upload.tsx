import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "../lib/api";

type Topic = { id: string; name: string; kind: string; notes: string | null };

type SubmitState =
  | { kind: "idle" }
  | { kind: "submitting" }
  | { kind: "error"; message: string };

async function errorDetail(res: Response): Promise<string> {
  const body = await res.json().catch(() => null);
  return body?.detail ?? `HTTP ${res.status}`;
}

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

const inputClass = "rounded-md border border-zinc-700 bg-zinc-950 px-3 py-2 text-zinc-100";

function Upload({ onCreated }: { onCreated: (meetingId: string) => void }) {
  const [topics, setTopics] = useState<Topic[]>([]);
  const [title, setTitle] = useState("");
  const [meetingDate, setMeetingDate] = useState(todayIso());
  const [topicId, setTopicId] = useState("");
  const [sourceType, setSourceType] = useState<"audio" | "text">("audio");
  const [files, setFiles] = useState<File[]>([]);
  const [text, setText] = useState("");
  const [submit, setSubmit] = useState<SubmitState>({ kind: "idle" });

  useEffect(() => {
    apiFetch("/topics")
      .then((res) => (res.ok ? res.json() : Promise.reject(new Error(`HTTP ${res.status}`))))
      .then(setTopics)
      .catch(() => setTopics([]));
  }, []);

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      setSubmit({ kind: "submitting" });
      try {
        if (!title.trim()) throw new Error("Podaj tytuł spotkania.");
        if (sourceType === "audio" && files.length === 0) {
          throw new Error("Wybierz co najmniej jeden plik audio.");
        }
        if (sourceType === "text" && !text.trim()) {
          throw new Error("Wklej treść spotkania.");
        }

        const createRes = await apiFetch("/meetings", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            title,
            meeting_date: meetingDate,
            topic_id: topicId || null,
            source_type: sourceType,
          }),
        });
        if (!createRes.ok) throw new Error(await errorDetail(createRes));
        const created: { id: string } = await createRes.json();

        if (sourceType === "audio") {
          const fd = new FormData();
          files.forEach((f, i) => {
            fd.append("files", f);
            fd.append("part_index", String(i + 1));
          });
          const audioRes = await apiFetch(`/meetings/${created.id}/audio`, {
            method: "POST",
            body: fd,
          });
          if (!audioRes.ok) throw new Error(await errorDetail(audioRes));
        } else {
          const textRes = await apiFetch(`/meetings/${created.id}/text`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ content: text }),
          });
          if (!textRes.ok) throw new Error(await errorDetail(textRes));
        }

        const processRes = await apiFetch(`/meetings/${created.id}/process`, { method: "POST" });
        if (!processRes.ok) throw new Error(await errorDetail(processRes));

        onCreated(created.id);
      } catch (err) {
        setSubmit({ kind: "error", message: String((err as Error).message ?? err) });
      }
    },
    [title, meetingDate, topicId, sourceType, files, text, onCreated],
  );

  return (
    <form
      onSubmit={handleSubmit}
      className="flex flex-col gap-4 rounded-xl border border-zinc-800 bg-zinc-900 px-8 py-6"
    >
      <h1 className="text-2xl font-semibold tracking-tight text-white">Nowe spotkanie</h1>

      <label className="flex flex-col gap-1.5">
        <span className="text-sm font-medium text-zinc-400">Tytuł</span>
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className={inputClass}
          required
        />
      </label>

      <div className="flex gap-4">
        <label className="flex flex-1 flex-col gap-1.5">
          <span className="text-sm font-medium text-zinc-400">Data spotkania</span>
          <input
            type="date"
            value={meetingDate}
            onChange={(e) => setMeetingDate(e.target.value)}
            className={inputClass}
            required
          />
        </label>
        <label className="flex flex-1 flex-col gap-1.5">
          <span className="text-sm font-medium text-zinc-400">Temat / dostawca</span>
          <select
            value={topicId}
            onChange={(e) => setTopicId(e.target.value)}
            className={inputClass}
          >
            <option value="">— brak —</option>
            {topics.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="flex gap-4">
        <label className="flex items-center gap-2 text-zinc-200">
          <input
            type="radio"
            checked={sourceType === "audio"}
            onChange={() => setSourceType("audio")}
          />
          <span>Nagranie audio</span>
        </label>
        <label className="flex items-center gap-2 text-zinc-200">
          <input
            type="radio"
            checked={sourceType === "text"}
            onChange={() => setSourceType("text")}
          />
          <span>Wklejony tekst</span>
        </label>
      </div>

      {sourceType === "audio" ? (
        <label className="flex flex-col gap-1.5">
          <span className="text-sm font-medium text-zinc-400">
            Pliki audio (.mp3 .m4a .wav .aac .ogg .flac) — dla sesji &gt; 1h wybierz kilka
            plików w kolejności chronologicznej
          </span>
          <input
            type="file"
            multiple
            accept=".mp3,.m4a,.wav,.aac,.ogg,.flac"
            onChange={(e) => setFiles(Array.from(e.target.files ?? []))}
            className={inputClass + " text-zinc-300 file:mr-3 file:rounded file:border-0 file:bg-zinc-800 file:px-3 file:py-1.5 file:text-zinc-100"}
          />
          {files.length > 0 && (
            <ul className="mt-1 text-sm text-zinc-500">
              {files.map((f, i) => (
                <li key={f.name + i}>
                  część {i + 1}: {f.name}
                </li>
              ))}
            </ul>
          )}
        </label>
      ) : (
        <label className="flex flex-col gap-1.5">
          <span className="text-sm font-medium text-zinc-400">Treść spotkania</span>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={10}
            className={inputClass + " font-mono text-sm"}
          />
        </label>
      )}

      {submit.kind === "error" && <p className="text-sm text-red-400">Błąd: {submit.message}</p>}

      <button
        type="submit"
        disabled={submit.kind === "submitting"}
        className="self-start rounded-md bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-500 disabled:opacity-50"
      >
        {submit.kind === "submitting" ? "Wysyłanie…" : "Prześlij i rozpocznij transkrypcję"}
      </button>
    </form>
  );
}

export default Upload;
