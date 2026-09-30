"""Transaction-local account context for PostgreSQL row-level security."""

from django.db import DEFAULT_DB_ALIAS, connections


def definir_conta(conta_id, *, using=None):
    """Set ``app.conta_id`` for the current transaction. Empty matches no row."""
    valor = "" if conta_id is None else str(conta_id)
    _definir("app.conta_id", valor, using=using)


def definir_email_de_login(email, *, using=None):
    """Set ``app.login_email`` for the current transaction. Empty matches no row."""
    valor = "" if email is None else str(email)
    _definir("app.login_email", valor, using=using)


def _definir(chave, valor, *, using=None):
    conn = connections[using or DEFAULT_DB_ALIAS]
    if conn.vendor != "postgresql":
        return
    with conn.cursor() as cursor:
        cursor.execute("SELECT set_config(%s, %s, true)", [chave, valor])
        cursor.fetchone()
