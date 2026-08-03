/**
 * The message a failed API call should show the user.
 *
 * Every DRF view in this project reports a domain failure as
 * `{ "error": "..." }` (see `DomainError` on the backend), and axios nests that
 * under `response.data`. Reading it used to be written inline as
 * `catch (err: any) { err.response?.data?.error }` — which is why eight call
 * sites carried an explicit `any`, and ten more repeated the cast by hand.
 *
 * `unknown` is the correct type for a caught value; this narrows it in one
 * place so no caller has to opt out of type-checking to read a message.
 */
export function apiErrorMessage(err: unknown, fallback: string): string {
  const detail = (err as { response?: { data?: { error?: unknown } } })?.response?.data?.error;
  return typeof detail === 'string' && detail ? detail : fallback;
}
