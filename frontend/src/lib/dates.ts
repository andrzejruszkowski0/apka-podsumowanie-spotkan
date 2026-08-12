/** Dzisiejsza data jako YYYY-MM-DD w strefie przeglądarki.
 *
 * `toISOString().slice(0, 10)` liczy datę w UTC — wieczorem czasu polskiego
 * (UTC+1/+2) zwracał jeszcze poprzedni dzień, więc domyślna data spotkania i
 * próg „po terminie" rozjeżdżały się z backendem, który liczy dni w
 * Europe/Warsaw (patrz TIMEZONE w backend/app/config.py).
 */
export function todayIso(): string {
  const now = new Date();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${now.getFullYear()}-${month}-${day}`;
}
