'use client';

import { useEffect, useState } from 'react';

/**
 * `false` on the server and on the first client render, `true` afterwards.
 *
 * State that only exists in the browser — the auth cookie, the theme, the
 * locale — makes the server and the first client render disagree, and React
 * treats that as a hydration failure: it discards the server HTML and re-renders
 * the tree. Gating on this flag makes both renders agree and turns the swap into
 * a deliberate second render instead.
 *
 * This was copied into five components before it lived here. It is also the ONE
 * place the project suppresses `react-hooks/set-state-in-effect`: the extra
 * render the rule warns about is precisely the mechanism, not an oversight. The
 * rule's preferred alternative, `useSyncExternalStore` with a server snapshot,
 * belongs at each store rather than here, and is a larger change than the bug it
 * would buy back.
 */
export function useMounted(): boolean {
  const [mounted, setMounted] = useState(false);
  // eslint-disable-next-line react-hooks/set-state-in-effect -- see above: the
  // post-mount render IS the point, and it is confined to this single hook.
  useEffect(() => setMounted(true), []);
  return mounted;
}
