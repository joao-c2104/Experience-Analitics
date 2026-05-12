from django.shortcuts import render
from .models import Curso

def lista_cursos(request):
    query = request.GET.get('q', '').strip()
    cursos = Curso.objects.all()

    if query:
        cursos = cursos.filter(nome__icontains=query)

    return render(request, 'cursos/lista_cursos.html', {
        'cursos': cursos,
        'query': query,
        'total_resultados': cursos.count(),
    })
