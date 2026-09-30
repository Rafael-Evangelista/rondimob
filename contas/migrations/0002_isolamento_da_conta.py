from django.db import migrations


def _executar(schema_editor, sql):
    schema_editor.execute(sql)


def aplicar_isolamento(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    _executar(
        schema_editor,
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'rondimob_web') THEN
                CREATE ROLE rondimob_web LOGIN PASSWORD 'dev-only-web';
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'rondimob_worker') THEN
                CREATE ROLE rondimob_worker LOGIN PASSWORD 'dev-only-worker';
            END IF;
        END
        $$;
        """,
    )
    _executar(
        schema_editor,
        """
        ALTER ROLE rondimob_web
            WITH LOGIN NOSUPERUSER NOBYPASSRLS PASSWORD 'dev-only-web'
        """,
    )
    _executar(
        schema_editor,
        """
        ALTER ROLE rondimob_worker
            WITH LOGIN NOSUPERUSER NOBYPASSRLS PASSWORD 'dev-only-worker'
        """,
    )
    _executar(schema_editor, "GRANT USAGE ON SCHEMA public TO rondimob_web, rondimob_worker")
    _executar(
        schema_editor,
        """
        GRANT SELECT, INSERT, UPDATE, DELETE
            ON TABLE public.contas_conta
            TO rondimob_web, rondimob_worker
        """,
    )
    _executar(
        schema_editor,
        """
        GRANT SELECT, INSERT, UPDATE, DELETE
            ON TABLE public.django_session
            TO rondimob_web
        """,
    )
    _executar(
        schema_editor,
        """
        GRANT SELECT ON TABLE public.django_migrations
            TO rondimob_web, rondimob_worker
        """,
    )
    _executar(
        schema_editor,
        "ALTER TABLE public.contas_conta ENABLE ROW LEVEL SECURITY",
    )
    _executar(
        schema_editor,
        "ALTER TABLE public.contas_conta FORCE ROW LEVEL SECURITY",
    )
    _executar(
        schema_editor,
        "DROP POLICY IF EXISTS conta_isola ON public.contas_conta",
    )
    _executar(
        schema_editor,
        """
        CREATE POLICY conta_isola ON public.contas_conta
        USING (
            id::text = current_setting('app.conta_id', true)
            OR (
                current_setting('app.login_email', true) <> ''
                AND email = current_setting('app.login_email', true)
            )
        )
        WITH CHECK (
            id::text = current_setting('app.conta_id', true)
        )
        """,
    )


def reverter_isolamento(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    _executar(schema_editor, "DROP POLICY IF EXISTS conta_isola ON public.contas_conta")
    _executar(
        schema_editor,
        "ALTER TABLE public.contas_conta NO FORCE ROW LEVEL SECURITY",
    )
    _executar(
        schema_editor,
        "ALTER TABLE public.contas_conta DISABLE ROW LEVEL SECURITY",
    )
    _executar(
        schema_editor,
        "REVOKE ALL ON TABLE public.contas_conta FROM rondimob_web, rondimob_worker",
    )
    _executar(
        schema_editor,
        "REVOKE ALL ON TABLE public.django_session FROM rondimob_web",
    )
    _executar(
        schema_editor,
        "REVOKE ALL ON TABLE public.django_migrations FROM rondimob_web, rondimob_worker",
    )


class Migration(migrations.Migration):
    dependencies = [
        ("contas", "0001_initial"),
        ("sessions", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(aplicar_isolamento, reverter_isolamento),
    ]
