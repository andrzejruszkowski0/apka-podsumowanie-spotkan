import { ArrowClockwise, Timer, WarningCircle } from "@phosphor-icons/react";
import type { Icon } from "@phosphor-icons/react";
import { useEffect, useState } from "react";
import { btnSecondarySm } from "../lib/styles";

/** Stan pusty: co tu będzie, po co to jest, jak zacząć. Bez własnej ramki —
 *  część wywołań stoi już wewnątrz karty, a karta w karcie to błąd. */
export function EmptyState({
  icon: IconGlyph,
  title,
  description,
  action,
}: {
  icon: Icon;
  title: string;
  description: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col items-start gap-2 py-6">
      {/* zinc-500 to najciemniejszy odcień, który utrzymuje wymagane dla grafiki
          3:1 na tle karty (zinc-600 daje 2.29:1 i ikona praktycznie znika). */}
      <IconGlyph size={24} weight="light" className="text-zinc-500" />
      <p className="text-sm font-medium text-zinc-100">{title}</p>
      <p className="max-w-md text-xs leading-relaxed text-zinc-400">{description}</p>
      {action && <div className="mt-1">{action}</div>}
    </div>
  );
}

// Backend demo na darmowym planie Render usypia po ~15 min bezczynności i budzi
// się 30-60 s. Dla osoby, która wchodzi pierwszy raz, jest to pierwsze
// doświadczenie z aplikacją — musi wiedzieć, że czeka, a nie że jest zepsute.
const COLD_START_AFTER_MS = 4000;

/** Licznik sekund zamiast spinnera: w tym systemie ruch jest dozwolony tylko
 *  wtedy, gdy niesie informację (DESIGN.md, „Sala kontrolna"). Upływający czas
 *  to informacja — obracające się kółko nie. */
export function LoadingState({ label = "Wczytywanie…" }: { label?: string }) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const started = Date.now();
    const id = setInterval(() => setElapsed(Math.floor((Date.now() - started) / 1000)), 1000);
    return () => clearInterval(id);
  }, []);

  if (elapsed * 1000 < COLD_START_AFTER_MS) {
    return <p className="text-sm text-zinc-400">{label}</p>;
  }

  return (
    <div className="flex flex-col items-start gap-2 py-2">
      <p className="flex items-center gap-2 text-sm text-zinc-300">
        <Timer size={16} weight="light" className="text-zinc-500" />
        Budzę serwer demo — {elapsed} s
      </p>
      <p className="max-w-md text-xs leading-relaxed text-zinc-400">
        Wersja demo działa na darmowym planie, który usypia po kwadransie
        bezczynności. Pierwsze wejście po przerwie trwa 30–60 sekund. Kolejne
        ekrany będą już natychmiastowe.
      </p>
    </div>
  );
}

// „Failed to fetch" i „Load failed" to komunikaty przeglądarki dla zerwanego
// połączenia — w tej aplikacji prawie zawsze znaczą uśpiony backend, a nie
// awarię. Pokazanie surowego tekstu zamieniłoby normalny stan w panikę.
function isNetworkFailure(message: string): boolean {
  return /failed to fetch|load failed|networkerror|err_/i.test(message);
}

/** Błąd nazywa problem i drogę wyjścia. Bez przycisku ponowienia jest to
 *  ślepy zaułek, a nie komunikat. */
export function ErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry?: () => void;
}) {
  const offline = isNetworkFailure(message);
  return (
    <div className="flex flex-col items-start gap-2 py-2">
      <p className="flex items-center gap-2 text-sm text-red-400">
        <WarningCircle size={16} weight="light" />
        {offline ? "Brak połączenia z serwerem demo" : "Nie udało się wczytać danych"}
      </p>
      <p className="max-w-md text-xs leading-relaxed text-zinc-400">
        {offline
          ? "Serwer mógł się uśpić albo właśnie wstaje. Spróbuj ponownie za chwilę — pierwsze wejście po przerwie potrafi zająć minutę."
          : message}
      </p>
      {onRetry && (
        <button onClick={onRetry} className={"mt-1 flex items-center gap-1.5 " + btnSecondarySm}>
          <ArrowClockwise size={14} weight="bold" />
          Spróbuj ponownie
        </button>
      )}
    </div>
  );
}
