
# Orgst

Plataforma open-source (sem fins lucrativos) para organizar uma **comunidade de mentoria DEV**: perfis de membros (mentores/coaches/mentorados), acervo de documentação e gestão de projetos/tarefas (Kanban).

Co-founders: Tiago + Saphira.

---

## Visão do Produto

O Orgst nasce para ser a “casa” da comunidade:
- **Directory de membros** com perfis ricos e afinidades (skills, tecnologias, links).
- **Convites** (links/token) controlados pelos co-founders/admins.
- **Docs** em Markdown com histórico (versionamento do `body_md`).
- **Projetos e tarefas** com **Kanban** (colunas configuráveis por projeto).

---

## Stack (MVP)

### Backend
- **Python 3.12**
- **Django**
- **Django Ninja** (API + OpenAPI/Swagger)
- **PostgreSQL** (via Docker) ou **SQLite** (fallback local)

### Frontend (planejado)
- Next.js + Tailwind + shadcn/ui

---

> Apps Django (planejados):
- `apps.accounts`   → User/Profile/Roles/Invites
- `apps.community`  → Skills, directory, filtros
- `apps.docs`       → Document + DocumentVersion (body_md) + tags
- `apps.projects`   → Projects, membership
- `apps.boards`     → Boards/Columns (Kanban configurável)
- `apps.tasks`      → Tasks/Comments (ligadas ao Kanban)

---

## Pré-requisitos

- Python **3.12**
- Docker + Docker Compose (recomendado para Postgres)
- (Opcional) `uv` instalado

---

## Setup rápido (Backend)

### 1) Clonar e entrar no diretório
```bash
git clone <git@github.com:Tiago-Monteirox/orgst.git>
cd orgst
```

### 2) Criar ambiente virtual e instalar dependências (uv)
```bash
uv venv
source .venv/bin/activate
uv sync
```

### 3) Configurar variáveis de ambiente
Crie um arquivo .env na raiz do repo:

```env
DEBUG=true
SECRET_KEY=dev-secret-key-change-me
ALLOWED_HOSTS=localhost,127.0.0.1

# Postgres (dev via Docker)
DATABASE_URL=postgres://orgst:orgst@localhost:5432/orgst
```
---

### Banco de dados

Postgres via Docker

Subir o banco:
```bash
docker compose up -d db
```

Rodar migrations:
```
uv run python src/manage.py migrate
```
---

### Rodar o servidor
```bash
uv run python src/manage.py runserver
```

Acesse:

- Swagger / OpenAPI: http://127.0.0.1:8000/api/v1/docs
- Health check: http://127.0.0.1:8000/api/v1/health
- Admin Django: http://127.0.0.1:8000/admin

---

### Convenções do Projeto

- API base: /api/v1
- Padrão: router + schemas + services por app
- models.py → entidades (ORM)
- services.py → regras de negócio/use cases
- schemas.py → contrato da API (Ninja/Pydantic)
- api.py → endpoints (routers Ninja)

---

### Contribuindo

PRs são bem-vindos. Sugestão de fluxo:
- feature branch
- commits no padrão Conventional Commits (feat:, fix:, chore:)
- PR com descrição: objetivo, mudanças, como testar
