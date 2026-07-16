import { useEffect, useState } from "react";

type HealthState =
  | { kind: "loading" }
  | { kind: "ok"; status: string }
  | { kind: "error"; message: string };

function App() {
  const [health, setHealth] = useState<HealthState>({ kind: "loading" });

  useEffect(() => {
    fetch("/health")
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data) => setHealth({ kind: "ok", status: data.status }))
      .catch((err) =>
        setHealth({ kind: "error", message: String(err.message ?? err) }),
      );
  }, []);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="rounded-lg border border-gray-200 bg-white px-8 py-6 shadow-sm text-center">
        <h1 className="text-xl font-medium text-gray-900 mb-2">
          Analiza spotkań
        </h1>
        {health.kind === "loading" && (
          <p className="text-gray-500">Sprawdzanie backendu…</p>
        )}
        {health.kind === "ok" && (
          <p className="text-green-600 font-semibold">{health.status}</p>
        )}
        {health.kind === "error" && (
          <p className="text-red-600">Błąd: {health.message}</p>
        )}
      </div>
    </div>
  );
}

export default App;
