import re

from django import template


register = template.Library()


@register.filter
def limpar_markdown(texto):
    if not texto:
        return ""

    texto_limpo = str(texto)
    texto_limpo = re.sub(r"\*\*(.*?)\*\*", r"\1", texto_limpo)
    texto_limpo = re.sub(r"__(.*?)__", r"\1", texto_limpo)
    texto_limpo = re.sub(r"`([^`]*)`", r"\1", texto_limpo)
    texto_limpo = re.sub(r"^\s{0,3}#{1,6}\s*", "", texto_limpo, flags=re.MULTILINE)
    texto_limpo = re.sub(r"^\s*[-*]\s+", "", texto_limpo, flags=re.MULTILINE)
    texto_limpo = re.sub(r"\n{3,}", "\n\n", texto_limpo)

    return texto_limpo.strip()
