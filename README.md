# Experience Analytics

Plataforma inteligente de cursos focada em análise comportamental dos usuários e processamento de feedbacks automatizado via Inteligência Artificial.

---

## O Desafio
O principal desafio enfrentado hoje no mercado educacional digital é a **baixa taxa de resposta** às pesquisas tradicionais de satisfação (como NPS e CSAT), o que limita drasticamente a obtenção de feedbacks relevantes e representativos. 

O modelo atual de avaliação depende de ações diretas e manuais do usuário, que tende a evitar interações longas ou desconectadas da sua jornada de aprendizado. Isso cria um ponto cego, dificultando a identificação de problemas reais e travando a melhoria contínua dos serviços oferecidos.

---

## Nossa Solução
O **Experience Analytics** capta a experiência do usuário de forma orgânica e inteligente. Nossa plataforma vai além de apenas hospedar conteúdos: ela fornece inteligência ativa sobre o comportamento dos alunos.

Analisamos dados de uso em tempo real e aplicamos Inteligência Artificial para extrair valor das interações naturais que o usuário já possui com o ecossistema do curso.

### Funcionalidades Principais

* ** Monitoramento de Engajamento (Streak Diária):** Acompanhamento automático da frequência de acesso, identificando padrões de uso e níveis de comprometimento dos alunos através de ofensivas diárias.
* ** Sistema Automático Antiautenticidade (Strikes):** Varredura em background que monitora inscrições ativas. Caso o aluno fique sem interagir por **15 dias ou mais**, o sistema atualiza seu status automaticamente para `Abandonado`, gerando métricas precisas de evasão.
* ** Regra de Negócio para Reembolsos:** Proteção financeira integrada onde solicitações de reembolso só podem ser efetuadas pelo aluno enquanto o curso estiver estritamente `Em Andamento`. Uma vez concluído, o acesso à funcionalidade é revogado na interface e bloqueado via backend.
* ** Resumos Automatizados com IA:** Sistema inteligente de avaliações e comentários. Todos os feedbacks deixados pelos usuários são lidos e resumidos automaticamente pela API do Gemini, destacando de forma categorizada:
  * Principais pontos positivos
  * Pontos críticos e negativos
  * Sugestões estruturadas de melhoria

---

## Tecnologias e Dependências

O projeto foi construído utilizando as seguintes tecnologias de mercado:

* **Backend:** Python 3.12+ & Django 6.0.5
* **Banco de Dados:** SQLite (Desenvolvimento)
* **Inteligência Artificial:** Google GenAI SDK (`google-genai`)
* **Servidor de Produção:** Gunicorn 26.0.0
* **Gerenciamento de Arquivos Estáticos:** WhiteNoise 6.12.0
* **Gerenciamento de Variáveis de Ambiente:** Python-Dotenv 1.2.2

---

## Configuração do Ambiente e Instalação

Para rodar este projeto localmente na sua máquina, siga os passos abaixo:

#### Crie e ative o ambiente virtual (venv):

   python -m venv venv
   # No Windows:
   .\venv\Scripts\activate
   # No Linux/Mac:
   source venv/bin/activate
   
#### Instale as dependências:

   pip install -r requirements.txt

#### Rode as migrações e ligue o servidor:

   python manage.py migrate
   python manage.py runserver
Acesse o site localmente em http://127.0.0.1:8000/.

#### Estrutura de Implantação (Deploy no Render)
O site está configurado para deploy contínuo integrado ao Render Web Services.

Ambiente de Runtime: Python 3.14.3 com Poetry 2.1.3

#### Build Command (Comando de Construção):

  pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
  
#### Start Command (Comando de Inicialização):

  gunicorn plataforma.wsgi
