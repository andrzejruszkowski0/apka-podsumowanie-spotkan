import { useCallback, useEffect, useState } from "react";

type Topic = { id: string; name: string; kind: string; notes: string | null };

type Preview = { topic_id: string; topic_name: string; subject: string; body: string };

type PreviewState =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "ok"; preview: Preview }
  | { kind: "error"; message: string };

type SendState =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "done" }
  | { kind: "error"; message: string };

async function errorDetail(res: Response): Promise<string> {
  const body = await res.json().catch(() => null);
  return body?.detail ?? `HTTP ${res.status}`;
}

function Briefing() {
  const [topics, setTopics] = useState<Topic[]>([]);
  const [topicId, setTopicId] = useState("");
  const [preview, setPreview] = useState<PreviewState>({ kind: "idle" });
  const [send, setSend] = useState<SendState>({ kind: "idle" });

  useEffect(() => {
    fetch("/topics")
      .then(async (res) => {
        if (!res.ok) throw new Error(await errorDetail(res));
        setTopics(await res.json());
      })
      .catch(() => {
        // Brak listy tematów uniemożliwia wybór — błąd i tak pojawi się przy próbie podglądu.
      });
  }, []);

  const generatePreview = useCallback(() => {
    if (!topicId) return;
    setPreview({ kind: "loading" });
    setSend({ kind: "idle" });
    fetch("/briefing/preview", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ topic_id: topicId }),
    })
      .then(async (res) => {
        if (!res.ok) throw new Error(await errorDetail(res));
        const data: Preview = await res.json();
        setPreview({ kind: "ok", preview: data });
      })
      .catch((err) => setPreview({ kind: "error", message: String(err.message ?? err) }));
  }, [topicId]);

  // Wysyła dokładnie to, co pokazał podgląd — bez ponownego wywołania Gemini
  // (SPEC.md §0/§8/§10.5: żadna treść AI nie idzie do skrzynki bez świadomego
  // kliknięcia po przeczytaniu; regeneracja mogłaby dać inny tekst niż przeczytany).
  const sendBriefing = useCallback(() => {
    if (preview.kind !== "ok") return;
    setSend({ kind: "loading" });
    fetch("/briefing/send", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        topic_id: preview.preview.topic_id,
        subject: preview.preview.subject,
        body: preview.preview.body,
      }),
    })
      .then(async (res) => {
        if (!res.ok) throw new Error(await errorDetail(res));
        setSend({ kind: "done" });
      })
      .catch((err) => setSend({ kind: "error", message: String(err.message ?? err) }));
  }, [preview]);

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-lg font-medium text-gray-900">Briefing przed spotkaniem</h1>

      <div className="flex flex-wrap items-end gap-4 rounded-lg border border-gray-200 bg-white px-4 py-3">
        <label className="flex flex-col gap-1 text-sm text-gray-600">
          Temat
          <select
            value={topicId}
            onChange={(e) => {
              setTopicId(e.target.value);
              setPreview({ kind: "idle" });
              setSend({ kind: "idle" });
            }}
            className="rounded-md border border-gray-300 px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">— wybierz —</option>
            {topics.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>
        </label>
        <button
          onClick={generatePreview}
          disabled={!topicId || preview.kind === "loading"}
          className="rounded-md bg-blue-600 px-4 py-2 text-white font-medium hover:bg-blue-700 disabled:opacity-50"
        >
          {preview.kind === "loading" ? "Generuję…" : "Podgląd"}
        </button>
      </div>

      {preview.kind === "error" && <p className="text-sm text-red-600">Błąd: {preview.message}</p>}

      {preview.kind === "ok" && (
        <div className="rounded-lg border border-gray-200 bg-white px-4 py-3">
          <p className="text-xs uppercase text-gray-500">Temat maila</p>
          <p className="mb-3 text-gray-900">{preview.preview.subject}</p>
          <p className="text-xs uppercase text-gray-500">Treść</p>
          <pre className="whitespace-pre-wrap font-sans text-sm text-gray-900">{preview.preview.body}</pre>

          <div className="mt-4 flex items-center gap-3">
            <button
              onClick={sendBriefing}
              disabled={send.kind === "loading" || send.kind === "done"}
              className="rounded-md bg-blue-600 px-4 py-2 text-white font-medium hover:bg-blue-700 disabled:opacity-50"
            >
              {send.kind === "loading" ? "Wysyłam…" : send.kind === "done" ? "Wysłano" : "Wyślij"}
            </button>
            {send.kind === "error" && <p className="text-sm text-red-600">Błąd: {send.message}</p>}
            {send.kind === "done" && <p className="text-sm text-green-600">Briefing wysłany.</p>}
          </div>
        </div>
      )}
    </div>
  );
}

export default Briefing;
