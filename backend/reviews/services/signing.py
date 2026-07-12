"""
Seal signature — Ed25519 (docs/plan/08 §3.2, invariant I6).

HMAC was discarded: verification would require sharing the secret, so it
proves nothing to a third party. Ed25519 gives offline public verification —
the requirement behind the exportable certificate (E4).

The canonical payload (sorted keys, no whitespace) binds the act to the exact
binary through `version_sha256` and to the exact content through each covered
section's `body_hash`.
"""

import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from django.conf import settings
from django.utils import timezone


def _key_path() -> Path:
    configured = getattr(settings, 'SEAL_SIGNING_KEY_PATH', '')
    if configured:
        return Path(configured)
    return Path(settings.BASE_DIR) / '.seal_signing_key.pem'


def load_private_key() -> Ed25519PrivateKey:
    """Loads the PEM key; in non-production it is created on first use so a
    fresh dev/CI environment can sign without manual setup (docs/plan/08 DP-24
    still governs production custody)."""
    path = _key_path()
    if not path.exists():
        if getattr(settings, 'IS_PRODUCTION', False):
            raise RuntimeError(
                f'SEAL_SIGNING_KEY_PATH no existe ({path}): la clave de sellos es obligatoria.'
            )
        key = Ed25519PrivateKey.generate()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(
            key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )
        path.chmod(0o600)
        return key
    return serialization.load_pem_private_key(path.read_bytes(), password=None)


def public_key_b64(key_id: str | None = None) -> str:
    raw = load_private_key().public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return base64.b64encode(raw).decode()


def key_id() -> str:
    """Stable id derived from the public key: rotation keeps old signatures
    verifiable against their historical key."""
    return hashlib.sha256(base64.b64decode(public_key_b64())).hexdigest()[:16]


def canonical_payload(*, seal_public_id, version, reviewer, covers_all, sections) -> dict:
    """sections: [(stable_key, body_hash)] — sorted for canonicity."""
    document = version.document
    project = document.project
    return {
        'v': 1,
        'seal_id': str(seal_public_id),
        'org': str(project.organization.public_id),
        'project': str(project.public_id),
        'document': str(document.public_id),
        'version_number': version.number,
        'version_sha256': version.sha256,
        'reviewer': {
            'id': str(reviewer.pk),
            'email': reviewer.email,
            'role': 'reviewer',
        },
        'covers_all': covers_all,
        'sections': [
            {'stable_key': key, 'body_hash': body_hash}
            for key, body_hash in sorted(sections)
        ],
        'config_version': version.config_version.number,
        'signed_at': timezone.now().replace(microsecond=0).isoformat().replace('+00:00', 'Z'),
    }


def canonical_bytes(payload: dict) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()


def sign(payload: dict) -> str:
    signature = load_private_key().sign(canonical_bytes(payload))
    return base64.b64encode(signature).decode()


def verify(payload: dict, signature_b64: str, public_b64: str | None = None) -> bool:
    """Offline-verifiable: needs only payload + signature + public key."""
    raw_public = base64.b64decode(public_b64 or public_key_b64())
    public_key = Ed25519PublicKey.from_public_bytes(raw_public)
    try:
        public_key.verify(base64.b64decode(signature_b64), canonical_bytes(payload))
        return True
    except Exception:
        return False
