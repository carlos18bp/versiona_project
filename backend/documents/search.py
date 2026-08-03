"""
Content search (flow B2) — the portable replacement for PostgreSQL's FTS.

PostgreSQL did this with a `spanish_unaccent` TEXT SEARCH CONFIGURATION
(`unaccent` chained into `spanish_stem`) feeding a `tsvector` column and a GIN
index. MySQL 8 has neither an unaccent filter nor a Spanish stemmer, so both
halves move into Python and MySQL keeps only what it is good at: the inverted
index (`FULLTEXT`) and the match operator (`MATCH ... AGAINST`).

The contract that survives the move is what the B2 tests assert: 'obligación'
finds a document that says 'obligaciones' — accent folding plus stemming
collapse both to the same token.
"""

import re
import unicodedata

import snowballstemmer
from django.db import models
from django.db.utils import NotSupportedError

_STEMMER = snowballstemmer.stemmer('spanish')
_WORD_RE = re.compile(r'\w+', re.UNICODE)

# MySQL's innodb_ft_min_token_size defaults to 3: shorter tokens never make it
# into the index, so indexing and querying them would only cost work.
MIN_TOKEN_LENGTH = 3

# BOOLEAN MODE reads these as operators, so they cannot reach the query intact.
_BOOLEAN_OPERATORS = re.compile(r'[+\-><()~*"@]')


def fold(text: str) -> str:
    """Strips accents and lowercases. Replaces PostgreSQL's `unaccent`."""
    decomposed = unicodedata.normalize('NFKD', text or '')
    return ''.join(c for c in decomposed if not unicodedata.combining(c)).lower()


def stem_tokens(text: str) -> list[str]:
    """Folded, stemmed tokens. Replaces to_tsvector('spanish_unaccent', ...)."""
    words = _WORD_RE.findall(fold(text))
    return [
        stem for stem in _STEMMER.stemWords(words) if len(stem) >= MIN_TOKEN_LENGTH
    ]


def build_search_text(text: str) -> str:
    """The indexed form of a section body, stored in SectionVersion.search_text."""
    return ' '.join(stem_tokens(text))


def boolean_query(query: str) -> str:
    """A sanitised BOOLEAN MODE query where every term is required.

    Operators are stripped before stemming, so a user typing `+` or `"` gets a
    literal search instead of an accidental operator (or a syntax error).
    """
    return ' '.join(f'+{term}' for term in stem_tokens(_BOOLEAN_OPERATORS.sub(' ', query)))


@models.TextField.register_lookup
class FullTextSearch(models.Lookup):
    """`search_text__fts=<boolean_query(...)>` → MATCH ... AGAINST.

    Django has no FULLTEXT expression of its own, and writing this as a lookup
    keeps the caller inside the ORM: it still composes with Exists()/OuterRef,
    which is what the board search needs.
    """

    lookup_name = 'fts'

    def as_mysql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        return f'MATCH ({lhs}) AGAINST ({rhs} IN BOOLEAN MODE)', (*lhs_params, *rhs_params)

    def as_sql(self, compiler, connection):
        """No silent fallback. The right-hand side is BOOLEAN MODE syntax, so any
        backend that cannot run MATCH ... AGAINST would quietly return wrong
        results — worse than refusing, given B2 answers "does this document say
        it?"."""
        raise NotSupportedError(
            f'{self.lookup_name} requires MySQL; {connection.vendor} has no FULLTEXT match.'
        )
