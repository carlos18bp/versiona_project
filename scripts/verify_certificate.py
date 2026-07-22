#!/usr/bin/env python3
"""
Standalone certificate verifier — NO Versiona code, no server, no database.

Give it the certificate snapshot (the JSON returned by the download endpoint
or embedded in the PDF annex) and it re-verifies every Ed25519 signature with
nothing but the `cryptography` library. This is the T6 promise made runnable:
a third party can audit a Versiona certificate offline.

Usage:
    python3 scripts/verify_certificate.py snapshot.json
    cat snapshot.json | python3 scripts/verify_certificate.py -
Exit code 0 = every signature verifies; 1 = at least one fails.
"""

import base64
import json
import sys

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


def canonical_bytes(payload: dict) -> bytes:
    return json.dumps(
        payload, sort_keys=True, separators=(',', ':'), ensure_ascii=False
    ).encode()


def verify_snapshot(snapshot: dict) -> list[dict]:
    public_key = Ed25519PublicKey.from_public_bytes(
        base64.b64decode(snapshot['public_key'])
    )
    results = []
    for seal in snapshot.get('seals', []):
        try:
            public_key.verify(
                base64.b64decode(seal['signature']),
                canonical_bytes(seal['payload']),
            )
            valid = True
        except Exception:
            valid = False
        results.append({
            'reviewer': seal.get('reviewer', '?'),
            'sealed_version': seal.get('sealed_version'),
            'valid': valid,
        })
    return results


def main() -> int:
    source = sys.argv[1] if len(sys.argv) > 1 else '-'
    raw = sys.stdin.read() if source == '-' else open(source).read()
    snapshot = json.loads(raw)

    print(f"Constancia: {snapshot.get('serial', '?')}")
    print(f"Versión: v{snapshot.get('version_number', '?')} · "
          f"sha256 {snapshot.get('version_sha256', '?')[:16]}…")
    results = verify_snapshot(snapshot)
    failures = 0
    for row in results:
        mark = 'VÁLIDA' if row['valid'] else 'INVÁLIDA ✗'
        print(f"  · {row['reviewer']} (selló v{row['sealed_version']}): firma {mark}")
        failures += 0 if row['valid'] else 1
    if not results:
        print('  (sin sellos en el snapshot)')
        return 1
    print('VEREDICTO:', 'TODAS LAS FIRMAS VERIFICAN' if failures == 0
          else f'{failures} FIRMA(S) NO VERIFICAN')
    return 0 if failures == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
