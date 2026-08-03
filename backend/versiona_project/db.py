"""
Database configuration, shared by settings.py and settings_prod.py.

It lives in its own module because both settings files used to carry a
byte-identical copy of the DATABASES block. A driver-specific OPTIONS dict
duplicated in two places drifts; this one cannot.
"""

import os

# MySQL 8 defaults for utf8mb4. Identity columns (hashes, tokens, storage keys)
# opt out per-field with db_collation='utf8mb4_bin' — see docs/methodology.
CHARSET = 'utf8mb4'
COLLATION = 'utf8mb4_0900_ai_ci'

# init_command REPLACES sql_mode wholesale, so the full MySQL 8 default set has
# to be restated. A shorter form would silently drop ONLY_FULL_GROUP_BY and the
# NO_ZERO_* guards.
SQL_MODE = (
    'STRICT_TRANS_TABLES,'
    'ERROR_FOR_DIVISION_BY_ZERO,'
    'NO_ENGINE_SUBSTITUTION,'
    'ONLY_FULL_GROUP_BY,'
    'NO_ZERO_IN_DATE,'
    'NO_ZERO_DATE'
)


def build_db_config(base_dir):
    """Builds DATABASES['default'] from the environment.

    The engine is env-driven so a throwaway sqlite run stays possible, but the
    deployed engine is MySQL 8 (docs/plan/07 §2.1).
    """
    engine = os.getenv('DJANGO_DB_ENGINE', 'django.db.backends.mysql')
    config = {
        'ENGINE': engine,
        'NAME': os.getenv('DJANGO_DB_NAME', os.getenv('DB_NAME', 'versiona_project_db')),
    }

    if 'sqlite3' in engine:
        config['NAME'] = os.getenv('DJANGO_DB_NAME', str(base_dir / 'db.sqlite3'))
        return config

    config.update({
        'USER': os.getenv('DB_USER', 'versiona_project_user'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', '127.0.0.1'),
        'PORT': os.getenv('DB_PORT', '3306'),
    })

    if 'mysql' in engine:
        config['OPTIONS'] = {
            'charset': CHARSET,
            'init_command': f"SET sql_mode='{SQL_MODE}'",
            # Already Django's default for MySQL, pinned on purpose: at
            # REPEATABLE READ the token lookup in orgs/invitations.py would take
            # a gap lock on every miss, which is that endpoint's common case.
            'isolation_level': 'read committed',
        }
        # Without TEST the test database inherits the SERVER collation, so CI
        # could stay green on a schema that does not behave like staging.
        config['TEST'] = {'CHARSET': CHARSET, 'COLLATION': COLLATION}

    return config
