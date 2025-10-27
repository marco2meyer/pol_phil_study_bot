# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Nomos Chatbot is a multi-bot Streamlit application for educational AI tutoring. The primary bot (`phil_bot`) is a Socratic tutor for political philosophy students at Universität Hamburg. The architecture supports multiple independent bot instances sharing common infrastructure.

## Architecture

### Multi-Bot Structure
- **Bot-specific code**: Each bot lives in `bots/<bot_name>/` with its own:
  - `app.py` (Streamlit application)
  - `config.py` (system prompt and bot configuration)
  - `requirements.txt` (Python dependencies)
  - `.env.local` (local environment variables)
  - `.env.server` (production environment variables - not committed)
  - `rag/` directory (RAG ingestion scripts and literature files)

- **Shared infrastructure**:
  - MongoDB database (shared container, separate DBs per bot)
  - Generic Streamlit Dockerfile (`docker/Streamlit.Dockerfile`)
  - Deployment scripts (`scripts/deploy.sh`)

### Key Components

**Authentication & User Management** (`bots/phil_bot/app.py`):
- Supabase email/password authentication with university domain validation
- Cookie-based session persistence (1-day expiration)
- MongoDB stores user profiles, consent preferences, and session history
- Email whitelist support via `whitelist_emails` MongoDB collection

**RAG System** (`bots/phil_bot/rag/`):
- OpenAI Vector Store for course literature (PDFs)
- `rag_manifest.csv` maps files to metadata (title, author, session_number, category)
- `ingest_literature.py` uploads files with attributes to vector store
- Literature sources tracked in MongoDB `literature_sources` collection
- Citations enriched with metadata and displayed as formatted footnotes

**Chat System**:
- OpenAI Responses API with streaming deltas
- File search tool integrated with vector store
- Low reasoning effort for faster responses
- Citation extraction and enrichment post-streaming

**Data Storage**:
- MongoDB collections: `conversations`, `feedback`, `users`, `literature_sources`, `whitelist_emails`
- Conversations stored with messages array, timestamps, and user-defined titles

## Development Commands

### Local Development

**Run a bot locally**:
```bash
# Set up Python environment
python -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows
pip install -r bots/phil_bot/requirements.txt

# Ensure .env (root) and bots/phil_bot/.env.local are configured
streamlit run bots/phil_bot/app.py --server.baseUrlPath=/phil_bot
```

**Test RAG ingestion** (run from project root):
```bash
cd bots/phil_bot/rag
python ingest_literature.py
# Requires OPENAI_API_KEY and OPENAI_VECTOR_STORE_ID (or creates new one)
```

**Run with Docker Compose**:
```bash
docker compose up --build
# Access at http://localhost:8511/phil_bot/
```

### Deployment

**Deploy to production server**:
```bash
./scripts/deploy.sh <server_ip> phil_bot
# Copies .env and bots/phil_bot/.env.server to server
# Builds and starts containers via docker-compose.yml
```

## Environment Variables

### Root `.env` (MongoDB credentials, shared across bots):
- `MONGO_INITDB_ROOT_USERNAME`
- `MONGO_INITDB_ROOT_PASSWORD`

### Bot-specific `.env.local` / `.env.server`:
- `BASE_URL_PATH` - Sub-URL path (e.g., `phil_bot`) without leading slash
- `MONGODB_URI` - MongoDB connection string (use Docker service name `mongo` in production)
- `SUPABASE_URL`, `SUPABASE_ANON_KEY` - Supabase authentication
- `OPENAI_API_KEY` - OpenAI API key
- `OPENAI_MODEL` - Model name (default: `gpt-5`)
- `OPENAI_VECTOR_STORE_ID` - Vector store ID for RAG
- `OPENAI_VECTOR_STORE_NAME` - Vector store name (used if creating new)
- `AUTH_DEBUG` - Set to `true` to show authentication debug info in sidebar

## Critical Implementation Details

### RAG Citation Workflow
1. Stream text deltas immediately for responsive UX
2. After stream completes, extract file citations from `response.output`
3. Query MongoDB `literature_sources` collection for metadata using `openai_file_id`
4. Format enriched citations as footer: "📚 Kursmaterial: Title (Author; Sitzung N; Category)"
5. Append footer to streamed response

### Authentication Flow
1. Check session state for existing `supabase_session`
2. If none, attempt to restore from cookies (`sb_access_token`, `sb_refresh_token`)
3. Call `supabase.auth.set_session()` to validate tokens
4. On successful login, set cookies with 1-day expiration
5. Validate email domain (`.uni-hamburg.de`, `.studium.uni-hamburg.de`) or whitelist
6. Require consent dialog on first use (stored in `users` collection)

### System Prompt Architecture
The bot's behavior is defined in `bots/phil_bot/config.py` as `SYSTEM_PROMPT`. This is a comprehensive prompt (~5000+ words) that:
- Defines the bot's role as a Socratic tutor
- Specifies strict rules (no ghostwriting, argument reconstruction guidance only)
- Includes the complete course syllabus with reading lists
- Details teaching methods (argument reconstruction, essay coaching, quizzing)
- Is prepended to every conversation sent to OpenAI

### Docker Architecture
- Generic `Streamlit.Dockerfile` accepts `BOT_REQ` build arg for per-bot requirements
- `APP_PATH` and `BASE_URL_PATH` set via environment in `docker-compose.yml`
- Bot containers bind to `127.0.0.1:<port>` on host (Nginx handles external access)
- Nginx reverse proxy handles sub-URL routing and WebSocket upgrades

## Adding a New Bot

1. Copy `bots/phil_bot/` to `bots/<new_bot>/`
2. Update `config.py` with new system prompt
3. Create `.env.local` (local) and `.env.server` (production) with `BASE_URL_PATH=<new_bot>`
4. Update `docker-compose.yml` to add new service:
   ```yaml
   new_bot:
     build:
       args:
         BOT_REQ: bots/new_bot/requirements.txt
     env_file:
       - bots/new_bot/env
     environment:
       - APP_PATH=bots/new_bot/app.py
       - BASE_URL_PATH=new_bot
     ports:
       - "127.0.0.1:8512:8501"  # Next available port
   ```
5. Configure Nginx reverse proxy for sub-URL (see README.md deployment section)
6. Deploy: `./scripts/deploy.sh <server_ip> new_bot`

## Common Pitfalls

- **Cookie persistence issues**: Extra Streamlit Components `CookieManager` requires `get_all()` call each run and may need a rerun to populate
- **Path confusion**: RAG ingestion script must be run from project root for imports to work correctly
- **Environment variable precedence**: `.env.local` overrides root `.env` via `override=True` in `load_dotenv()`
- **MongoDB connection in Docker**: Use service name `mongo` (not `localhost`) in `MONGODB_URI` when running in containers
- **Nginx WebSocket support**: Both `/<path>/` and `/<path>/stream` locations need `Upgrade` and `Connection` headers for Streamlit
- **Citation extraction**: Citations only available after full response completion, not during streaming

## Testing & Debugging

**Check MongoDB data**:
```bash
docker exec -it polphil_mongo mongosh -u <username> -p <password>
use study_chatbot
db.conversations.find({user: "test@uni-hamburg.de"}).limit(5)
```

**View container logs**:
```bash
docker compose logs -f phil_bot
```

**Debug authentication**:
Set `AUTH_DEBUG=true` in `.env.local` to show cookie state and session info in sidebar expander.

## Technology Stack

- **Frontend**: Streamlit 1.47.1
- **Backend**: Python 3.11
- **Database**: MongoDB 7.0
- **Authentication**: Supabase Auth (email/password)
- **AI**: OpenAI API (Responses API with file_search tool)
- **Deployment**: Docker Compose, Nginx reverse proxy, Let's Encrypt SSL
- **Server**: Hetzner VPS (deployment details in README.md)
