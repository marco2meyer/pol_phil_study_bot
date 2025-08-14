import streamlit as st
from pymongo import MongoClient
import os
from pathlib import Path
from dotenv import load_dotenv
import json
from datetime import datetime
from bson import ObjectId
import random
import string
from config import SYSTEM_PROMPT
from supabase import create_client
import extra_streamlit_components as stx
import time

# Load environment variables: root .env, then bot-local .env.local (override)
ROOT = Path(__file__).resolve().parents[2]
load_dotenv(dotenv_path=ROOT / ".env")
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env.local", override=True)
AUTH_DEBUG = os.getenv("AUTH_DEBUG", "false").lower() in {"1", "true", "yes"}

# MongoDB setup
@st.cache_resource
def init_connection():
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
    client = MongoClient(MONGODB_URI)
    return client

client = init_connection()
db = client['study_chatbot']
conversations = db['conversations']
feedback = db['feedback']
users = db['users']

# Supabase setup
@st.cache_resource
def get_supabase_client():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL oder SUPABASE_ANON_KEY fehlen in der Umgebungskonfiguration")
    return create_client(url, key)

supabase = None
try:
    supabase = get_supabase_client()
except Exception as e:
    st.error(f"Supabase-Initialisierung fehlgeschlagen: {e}")

# Cookie manager for 1-day session persistence
cookie_manager = stx.CookieManager()
_ = cookie_manager.get_all()

# Try to restore session from cookies when not authenticated.
# CookieManager may need a rerun to fetch cookies; calling get_all() each run is fine.
try:
    if supabase and not st.session_state.get('supabase_session'):
        cookies = cookie_manager.get_all()
        at = cookies.get('sb_access_token')
        rt = cookies.get('sb_refresh_token')
        if at and rt:
            try:
                resp = supabase.auth.set_session(access_token=at, refresh_token=rt)
                session = getattr(resp, 'session', None) or (resp.get('session') if isinstance(resp, dict) else None)
                user = getattr(resp, 'user', None) or (resp.get('user') if isinstance(resp, dict) else None)
                if session and user:
                    email = (getattr(user, 'email', None) or user.get('email') or '').lower()
                    st.session_state.supabase_session = session
                    st.session_state.user_email = email
                    st.session_state.user = email
                    upsert_user_profile(email)
            except Exception:
                pass
except Exception:
    pass

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'current_conversation_id' not in st.session_state:
    st.session_state.current_conversation_id = None
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'user' not in st.session_state:
    st.session_state.user = None
if 'user_email' not in st.session_state:
    st.session_state.user_email = None
if 'supabase_session' not in st.session_state:
    st.session_state.supabase_session = None

# Email allow/whitelist check
def is_allowed_email(email: str) -> bool:
    email = (email or '').strip().lower()
    if email.endswith('@uni-hamburg.de') or email.endswith('@studium.uni-hamburg.de'):
        return True
    try:
        # optional whitelist collection
        whitelisted = db.get_collection('whitelist_emails')
        if whitelisted.find_one({"email": email}):
            return True
    except Exception:
        pass
    return False

# User profile upsert in Mongo
def upsert_user_profile(email: str):
    now = datetime.now()
    users.update_one(
        {"email": email},
        {"$setOnInsert": {"created_at": now},
         "$set": {"email": email, "last_login_at": now}},
        upsert=True,
    )

# --- Authentication UI (replaces URL parameter auth) ---
def render_auth_ui():
    st.title("Nomos AI")
    # Persist auth view across reruns to keep error messages visible
    st.session_state.setdefault('auth_view', 'Anmelden')
    auth_view = st.radio(
        "Authentifizierung",
        options=["Anmelden", "Registrieren", "Passwort zurücksetzen"],
        horizontal=True,
        label_visibility="collapsed",
        key="auth_view",
    )

    if auth_view == "Anmelden":
        st.subheader("Anmeldung")
        with st.form("login_form", clear_on_submit=False):
            # Use common keys and English labels to help password managers
            login_email = st.text_input("Email", key="email", placeholder="name@uni-hamburg.de")
            login_password = st.text_input("Password", type="password", key="password", placeholder="••••••••")
            submitted = st.form_submit_button("Anmelden")
        if submitted and supabase:
            try:
                if not is_allowed_email(login_email):
                    st.error("Nur E-Mail-Adressen der Universität Hamburg oder auf der Whitelist sind zugelassen.")
                else:
                    resp = supabase.auth.sign_in_with_password({"email": login_email, "password": login_password})
                    session = getattr(resp, 'session', None) or (resp.get('session') if isinstance(resp, dict) else None)
                    user = getattr(resp, 'user', None) or (resp.get('user') if isinstance(resp, dict) else None)
                    if session and user:
                        st.session_state.supabase_session = session
                        st.session_state.user_email = (getattr(user, 'email', None) or user.get('email')).lower()
                        st.session_state.user = st.session_state.user_email
                        upsert_user_profile(st.session_state.user_email)
                        # Persist tokens for 1 day
                        try:
                            at = getattr(session, 'access_token', None) or (session.get('access_token') if isinstance(session, dict) else None)
                            rt = getattr(session, 'refresh_token', None) or (session.get('refresh_token') if isinstance(session, dict) else None)
                            if at and rt:
                                cookie_manager.set('sb_access_token', at, key='set_at', path='/', max_age=86400, same_site='lax', secure=False)
                                cookie_manager.set('sb_refresh_token', rt, key='set_rt', path='/', max_age=86400, same_site='lax', secure=False)
                                cookie_manager.get_all()  # sync
                                time.sleep(0.2)  # give browser time to persist cookies before rerun
                        except Exception:
                            pass
                        st.success("Erfolgreich angemeldet.")
                        st.rerun()
                    else:
                        st.error("Anmeldung fehlgeschlagen. Bitte prüfen Sie Ihre Zugangsdaten.")
            except Exception as e:
                st.error(f"Anmeldung fehlgeschlagen: {e}")

    elif auth_view == "Registrieren":
        st.subheader("Registrierung")
        with st.form("signup_form", clear_on_submit=False):
            signup_email = st.text_input("Email", key="signup_email", placeholder="name@studium.uni-hamburg.de")
            signup_password = st.text_input("Password (min. 8 chars)", type="password", key="signup_password", placeholder="••••••••")
            submitted = st.form_submit_button("Konto erstellen")
        if submitted and supabase:
            try:
                if not is_allowed_email(signup_email):
                    st.error("Nur E-Mail-Adressen der Universität Hamburg oder auf der Whitelist sind zugelassen.")
                elif len(signup_password) < 8:
                    st.error("Das Passwort muss mindestens 8 Zeichen lang sein.")
                else:
                    # Use Supabase default UI for email confirmation
                    supabase.auth.sign_up({"email": signup_email, "password": signup_password})
                    st.info("Vielen Dank! Bitte bestätigen Sie Ihre E-Mail-Adresse über den Link, den wir Ihnen gesendet haben.")
            except Exception as e:
                st.error(f"Registrierung fehlgeschlagen: {e}")

    else:  # Passwort zurücksetzen
        st.subheader("Passwort zurücksetzen")
        with st.form("reset_form", clear_on_submit=False):
            reset_email = st.text_input("Email", key="pwreset_email", placeholder="name@uni-hamburg.de")
            submitted = st.form_submit_button("E-Mail zum Zurücksetzen senden")
        if submitted and supabase:
            try:
                if not is_allowed_email(reset_email):
                    st.error("E-Mail-Adresse nicht zugelassen.")
                else:
                    # Use Supabase default UI for password reset
                    supabase.auth.reset_password_for_email(reset_email)
                    st.success("Falls ein Konto existiert, wurde eine E-Mail zum Zurücksetzen des Passworts gesendet.")
            except Exception as e:
                st.error(f"Fehler beim Senden der Reset-E-Mail: {e}")

def ensure_consent(email: str) -> bool:
    """Returns True if consent was recorded (yes or no). Shows dialog if missing."""
    doc = users.find_one({"email": email})
    consent = (doc or {}).get("consent_research")
    if consent is None:
        st.warning("Zustimmung zur Forschungsauswertung")
        st.write(
            "Wir verbessern den Tutor-Chatbot durch anonyme Auswertung der Gesprächsdaten. "
            "Dabei werden keine personenbezogenen oder identifizierbaren Informationen weitergegeben. "
            "Stimmen Sie zu, dass Ihre Unterhaltung zu Forschungs- und Verbesserungszwecken anonymisiert ausgewertet wird?"
        )
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Ja, einverstanden", key="consent_yes"):
                users.update_one({"email": email}, {"$set": {"consent_research": True}})
                st.success("Danke für Ihre Zustimmung.")
                return True
        with col2:
            if st.button("Nein, ablehnen", key="consent_no"):
                users.update_one({"email": email}, {"$set": {"consent_research": False}})
                st.info("Ihre Entscheidung wurde gespeichert.")
                return True
        return False
    return True

# Gate app behind authentication and consent
with st.sidebar:
    if st.session_state.user_email:
        st.write(f"Angemeldet als: {st.session_state.user_email}")
        if AUTH_DEBUG:
            with st.expander("Auth Debug"):
                st.write("Cookies:", cookie_manager.get_all())
                st.write("Has session:", bool(st.session_state.get('supabase_session')))
        if st.button("Abmelden"):
            try:
                if supabase:
                    supabase.auth.sign_out()
            except Exception:
                pass
            # Clear auth cookies
            try:
                cookie_manager.delete('sb_access_token', key='del_at')
                cookie_manager.delete('sb_refresh_token', key='del_rt')
            except Exception:
                pass
            st.session_state.user_email = None
            st.session_state.user = None
            st.session_state.supabase_session = None
            st.session_state.messages = []
            st.session_state.current_conversation_id = None
            st.session_state.conversation_history = []
            st.success("Abgemeldet.")
            st.rerun()
    else:
        if AUTH_DEBUG:
            with st.expander("Auth Debug"):
                st.write("Cookies:", cookie_manager.get_all())
                st.write("Has session:", bool(st.session_state.get('supabase_session')))
        # Render authentication UI in the sidebar (single instance)
        render_auth_ui()

if not st.session_state.user_email:
    st.stop()

if not ensure_consent(st.session_state.user_email):
    st.stop()

# MongoDB helpers
def create_conversation():
    conversation = {
        'user': st.session_state.user,
        'messages': [],
        'created_at': datetime.now(),
        'last_updated': datetime.now(),
        'title': f"Unterhaltung {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    }
    result = conversations.insert_one(conversation)
    return str(result.inserted_id)

def get_conversations():
    return list(conversations.find({'user': st.session_state.user}).sort('last_updated', -1))

def switch_conversation(conversation_id):
    st.session_state.current_conversation_id = conversation_id
    conv = conversations.find_one({'_id': ObjectId(conversation_id)})
    if conv:
        st.session_state.messages = conv['messages']
        st.session_state.conversation_history = conv['messages']
        st.session_state.conversation_title = conv.get('title', '')

def log_message(role, content):
    if st.session_state.current_conversation_id:
        conversations.update_one(
            {'_id': ObjectId(st.session_state.current_conversation_id)},
            {'$push': {'messages': {'role': role, 'content': content}},
             '$set': {'last_updated': datetime.now()}}
        )

def update_conversation(conversation_id, messages):
    if conversation_id:
        conversations.update_one(
            {'_id': ObjectId(conversation_id)},
            {'$set': {
                'messages': messages,
                'last_updated': datetime.now()
            }}
        )

def chat_with_ai(messages):
    from openai import OpenAI

    # Initialize OpenAI client
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    # Compose input with system prompt
    input_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages

    # Configure file_search tool
    vector_store_id = os.getenv("OPENAI_VECTOR_STORE_ID")
    tools = []
    if vector_store_id:
        tools = [{
            "type": "file_search",
            "vector_store_ids": [vector_store_id]
        }]

    model = os.getenv("OPENAI_MODEL", "gpt-5")

    try:
        # Helper to read either dicts or SDK objects
        def g(obj, key, default=None):
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)

        # Stream response deltas, then enrich citations after completion
        # Suppress noisy Pydantic serialization warnings originating from SDK internals
        import warnings
        warnings.filterwarnings(
            "ignore",
            message="PydanticSerializationUnexpectedValue",
            category=UserWarning,
            module="pydantic",
        )
        with client.responses.stream(
            model=model,
            input=input_messages,
            tools=tools,
            reasoning={"effort": "low"},
            include=["file_search_call.results"],
        ) as stream:
            # Stream only textual deltas
            for event in stream:
                if g(event, "type") == "response.output_text.delta":
                    delta = g(event, "delta", "") or ""
                    if delta:
                        yield delta

            final = stream.get_final_response()

        # After full text streamed, compute and emit citation footer
        citations = []
        used_file_search = False
        for item in getattr(final, "output", []) or []:
            if g(item, "type") == "file_search_call":
                used_file_search = True
            if g(item, "type") == "message" and g(item, "role") == "assistant":
                for part in (g(item, "content") or []):
                    if g(part, "type") == "output_text":
                        for ann in (g(part, "annotations") or []):
                            if g(ann, "type") == "file_citation":
                                citations.append({
                                    "file_id": g(ann, "file_id"),
                                    "filename": g(ann, "filename"),
                                })

        footer = ""
        if used_file_search and citations:
            unique = []
            seen = set()
            for c in citations:
                key = (c.get("file_id"), c.get("filename"))
                if key not in seen:
                    seen.add(key)
                    unique.append(c)

            try:
                file_ids = [c.get("file_id") for c in unique if c.get("file_id")]
                meta_map = {}
                if file_ids:
                    cursor = db["literature_sources"].find({
                        "openai_file_id": {"$in": file_ids}
                    }, {"attributes": 1, "openai_file_id": 1})
                    for doc in cursor:
                        meta_map[doc.get("openai_file_id")] = doc.get("attributes", {})

                def fmt_entry(c):
                    fid = c.get("file_id")
                    meta = meta_map.get(fid, {})
                    title = meta.get("title") or c.get("filename") or "unbekannt"
                    author = meta.get("author")
                    session_num = meta.get("session_number")
                    category = meta.get("category")
                    parts = [title]
                    det = []
                    if author:
                        det.append(author)
                    if session_num is not None:
                        det.append(f"Sitzung {session_num}")
                    if category:
                        det.append(str(category))
                    if det:
                        parts.append("(" + "; ".join(det) + ")")
                    return " ".join(parts)

                enriched_list = ", ".join(fmt_entry(c) for c in unique)
                footer = "\n\n— 📚 Kursmaterial: " + enriched_list
            except Exception:
                footer = "\n\n— 📚 Kursmaterial (Dateien): " + ", ".join(
                    f"{c.get('filename','unbekannt')}" for c in unique
                )
        elif vector_store_id:
            footer = "\n\n— Hinweis: Keine Kursmaterialien zitiert (Allgemeines Wissen)."

        if footer:
            yield footer
    except Exception as e:
        st.error(f"Error generating response: {str(e)}")
        yield ""

# Sidebar - Conversation Management
with st.sidebar:
    st.header("Unterhaltungen")
    
    # Create new conversation
    if st.button("Neue Unterhaltung", key='new_conv'):
        conversation_id = create_conversation()
        switch_conversation(conversation_id)
    
    # List existing conversations
    convs = get_conversations()
    for conv in convs:
        conv_id = str(conv['_id'])
        if st.button(f"{conv.get('title', 'Untitled')} ({len(conv['messages'])} messages)", 
                    key=f'conv_{conv_id}'):
            switch_conversation(conv_id)

    # Conversation title
    if st.session_state.current_conversation_id:
        new_title = st.text_input("Titel", 
                                value=st.session_state.get('conversation_title', ''),
                                key='conv_title')
        if new_title != st.session_state.get('conversation_title', ''):
            conversations.update_one(
                {'_id': ObjectId(st.session_state.current_conversation_id)},
                {'$set': {'title': new_title}}
            )
            st.session_state.conversation_title = new_title

    # Disclaimer section

# Main chat interface
st.title("Nomos AI")

# Inject custom CSS for larger font in chat
st.markdown("""
<style>
div[data-testid="stChatMessage"] p {
    font-size: 1.1rem;
}
</style>
""", unsafe_allow_html=True)

if not st.session_state.current_conversation_id:
    conversation_id = create_conversation()
    switch_conversation(conversation_id)
    # Assistant starts the conversation
    initial_message = "Hallo! Woran arbeitest du gerade im Kurs ›Einführung in die politische Philosophie‹? Ich kann dir helfen, Deinen Essay zu entwickeln, Feedback auf einen Essay-Entwurf geben, Verständnisfragen klären, oder ein Quiz erstellen, um Dein Verständnis zu prüfen."
    st.session_state.messages.append({"role": "assistant", "content": initial_message})
    log_message('assistant', initial_message)



# Display messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
if prompt := st.chat_input("""Stelle irgendeine Frage."""):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Log user message
    log_message('user', prompt)

    # Get AI response
    with st.chat_message("assistant"):
        response_generator = chat_with_ai(st.session_state.messages)
        full_response = st.write_stream(response_generator)
        
        # Add the complete response to session state and database
        if full_response:
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            log_message('assistant', full_response)

# Feedback section
with st.expander("Bewerte diese Unterhaltung"):
    st.write("Wie hilfreich war diese Unterhaltung?")
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        st.write("<div style='text-align: left;'>Gar nicht hilfreich</div>", unsafe_allow_html=True)
    with col2:
        st.slider(
            "Bewertung",
            1, 5, key='rating',
            label_visibility="collapsed"
        )
    with col3:
        st.write("<div style='text-align: right;'>Sehr hilfreich</div>", unsafe_allow_html=True)
    feedback_text = st.text_area("Zusätzliches Feedback", key='feedback_text', placeholder="Dein Feedback hier...")
    if st.button("Feedback absenden", key='submit_feedback'):
        feedback.insert_one({
            'conversation_id': st.session_state.current_conversation_id,
            'user': st.session_state.user,
            'rating': st.session_state.rating,
            'feedback': feedback_text,
            'created_at': datetime.now()
        })
        st.success("Danke für dein Feedback!")

with st.expander("ℹ️ Wichtige Hinweise", expanded=False):
    st.markdown("""
    **Disclaimer:**
    
    Dieser Chatbot ist ein experimentelles System zu Studienzwecken.
    Die bereitgestellten Informationen können unvollständig oder fehlerhaft sein.
    Bei Prüfungen kann kein Anspruch auf Richtigkeit oder Vollständigkeit der Antworten geltend gemacht werden.
    Eingegebene Daten können mit OpenAI geteilt und zu Trainingszwecken verwendet werden. Bitte gib keine sensiblen oder persönlichen Informationen ein.
    """, unsafe_allow_html=True)
