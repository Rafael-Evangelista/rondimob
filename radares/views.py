from django.shortcuts import get_object_or_404, redirect, render

from radares.forms import RadarForm
from radares.models import Radar


def novo(request):
    if not request.user.is_authenticated:
        return redirect("entrar")
    if request.method == "POST":
        form = RadarForm(request.POST)
        if form.is_valid():
            form.save(request.user)
            return redirect("area")
    else:
        form = RadarForm()
    return render(
        request,
        "radares/novo.html",
        {"form": form, "titulo": "Novo radar", "acao": "/area/radares/novo/"},
    )


def editar(request, radar_id):
    if not request.user.is_authenticated:
        return redirect("entrar")
    radar = get_object_or_404(Radar, pk=radar_id, conta=request.user)
    if request.method == "POST":
        form = RadarForm(request.POST, instance=radar)
        if form.is_valid():
            form.save(request.user)
            return redirect("area")
    else:
        form = RadarForm(instance=radar)
    return render(
        request,
        "radares/novo.html",
        {
            "form": form,
            "titulo": "Editar radar",
            "acao": f"/area/radares/{radar.id}/",
        },
    )
