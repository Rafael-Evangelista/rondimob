from celery import shared_task


@shared_task
def preparar_link_de_recuperacao(conta_id):
    from django.contrib.auth.tokens import PasswordResetTokenGenerator
    from django.utils.encoding import force_bytes
    from django.utils.http import urlsafe_base64_encode

    from contas.models import Conta

    conta = Conta.objects.get(pk=conta_id)
    uidb64 = urlsafe_base64_encode(force_bytes(conta.pk))
    token = PasswordResetTokenGenerator().make_token(conta)
    link = f"/recuperar-senha/{uidb64}/{token}/"
    print(f"recuperacao de senha conta={conta.pk} link={link}", flush=True)
    return link
