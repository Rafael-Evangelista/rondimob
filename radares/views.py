from django.shortcuts import redirect, render

from radares.forms import RadarForm


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
    return render(request, "radares/novo.html", {"form": form})
