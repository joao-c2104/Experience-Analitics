from django.shortcuts import render
from cursos.models import Curso


def buscar_cursos(request):
    """
    View responsável pela busca de cursos.
    Filtra o catálogo de cursos com base no termo digitado pelo usuário.
    """
    query = request.GET.get('q', '').strip()
    cursos = Curso.objects.all()

    if query:
        cursos = cursos.filter(nome__icontains=query)

    return render(request, 'cursos/lista_cursos.html', {
        'cursos': cursos,
        'query': query,
        'total_resultados': cursos.count(),
    })
