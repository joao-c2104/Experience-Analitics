from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Curso

@login_required
def lista_cursos(request):
    cursos = Curso.objects.all()
    return render(request, 'cursos/lista_cursos.html', {'cursos': cursos})
