from django.conf import settings
from google import genai


def gerar_relatorio_com_gemini(usuario, curso, categorias, comentario, nota=None):
    if not settings.GEMINI_API_KEY:
        raise ValueError("A variável de ambiente GEMINI_API_KEY não foi configurada.")

    categorias_texto = ", ".join(categorias)

    prompt = f"""
Você é um assistente de análise educacional.

Sua tarefa é transformar o feedback de um estudante em um relatório administrativo
claro, organizado e útil para o administrador da plataforma.

Dados do feedback:

Aluno:
{usuario.username}

Curso:
{curso.nome}

Nota dada pelo aluno:
{nota if nota is not None else "Não informada"}

Categorias escolhidas:
{categorias_texto}

Comentário original do aluno:
{comentario}

Gere um relatório em português do Brasil com esta estrutura:

RELATÓRIO DE FEEDBACK DO ALUNO

1. Identificação
- Aluno:
- Curso:
- Nota:
- Categorias analisadas:

2. Comentário original do aluno
Reescreva o comentário original de forma fiel e resumida, sem inventar informações.

3. Pontos positivos identificados
Liste apenas pontos positivos que possam ser percebidos no comentário.
Se não houver pontos positivos claros, escreva que o aluno não mencionou pontos positivos diretamente.

4. Pontos de melhoria identificados
Caso o aluno mencione problemas,liste esses problemas, críticas ou dificuldades mencionadas pelo aluno.

5. Sugestões para melhoria
Dê sugestões práticas relacionadas às categorias escolhidas pelo aluno.

6. Resumo final para o administrador
Faça um resumo objetivo explicando o que o administrador deve observar nesse feedback.

7. Possíveis ações futuras
Liste possíveis ações que o administrador pode tomar com base na avaliação do aluno.
As ações devem ser práticas, específicas e relacionadas aos pontos mencionados no feedback.
Se o feedback não indicar nenhuma ação clara, escreva que não há ações específicas sugeridas.
Organize as ações em ordem de prioridade, da mais importante para a menos importante.

Regras:
- Não invente informações.
- Não diga que algo aconteceu se não estiver no comentário.
- Seja claro, organizado e profissional.
- O relatório deve ajudar o administrador a melhorar o curso e a plataforma.
- Não use Markdown, asteriscos, negrito, bullets com * ou formatação especial.
- Use texto simples, com títulos e linhas curtas.
"""

    with genai.Client(api_key=settings.GEMINI_API_KEY) as client:
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
        )

    if not response.text:
        raise ValueError("O Gemini não retornou texto.")

    return response.text.strip()
