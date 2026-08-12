// Współdzielone klasy Tailwind dla przycisków — wydzielone, bo ten sam wariant
// (primary/secondary, pełny/kompaktowy) powtarzał się identycznie w 8+ miejscach.
export const btnPrimary =
  "rounded-md bg-blue-600 px-4 py-2 font-medium text-white transition-transform hover:bg-blue-500 active:scale-[0.98] disabled:opacity-50 disabled:active:scale-100";

export const btnPrimarySm =
  "rounded-md bg-blue-600 px-3 py-1 text-sm font-medium text-white transition-transform hover:bg-blue-500 active:scale-[0.98] disabled:opacity-50 disabled:active:scale-100";

export const btnSecondary =
  "rounded-md border border-zinc-700 px-4 py-2 font-medium text-zinc-300 transition-transform hover:bg-zinc-800 active:scale-[0.98] disabled:opacity-50 disabled:active:scale-100";

export const btnSecondarySm =
  "rounded-md border border-zinc-700 px-3 py-1 text-sm text-zinc-300 transition-transform hover:bg-zinc-800 active:scale-[0.98] disabled:opacity-50 disabled:active:scale-100";
