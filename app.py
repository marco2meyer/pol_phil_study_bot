import streamlit as st
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import json
from datetime import datetime
from bson import ObjectId
import random
import string
from config import SYSTEM_PROMPT

# Load environment variables
load_dotenv()

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

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'current_conversation_id' not in st.session_state:
    st.session_state.current_conversation_id = None
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'user' not in st.session_state:
    st.session_state.user = None

# --- Authentication via URL parameter ---
user_param = st.query_params.get('user', [None])

if not user_param:
    st.error("Bitte geben Sie einen Benutzernamen als URL-Parameter an (z.B. `?user=dein_name`)")
    st.stop()

# Check if user exists in the database
user_account = users.find_one({"username": user_param})
if not user_account:
    st.error(f"Benutzer '{user_param}' nicht gefunden. Zugriff verweigert.")
    st.stop()

# Set user in session state if validated
st.session_state.user = user_param

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
    import httpx

    # Explicitly initialize the OpenAI client, preventing Streamlit from passing a 'proxies' argument
    client = OpenAI(
        api_key=os.getenv('OPENAI_API_KEY'),
        http_client=httpx.Client(proxies="")
    )
    
    # Prepare messages for API call
    full_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages
    
    try:
        # Get response from OpenAI
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=full_messages,
            temperature=0.5,
            max_tokens=1000
        )
        bot_response = response.choices[0].message.content
        return bot_response
    except Exception as e:
        st.error(f"Error generating response: {str(e)}")
        return None

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
    initial_message = "Hallo! Woran arbeitest du gerade im Kurs ›Einführung in die politische Philosophie‹? Ich kann dir helfen, Deinen Essay zu entwickeln, Feedback auf einen Essay-Entwurf geben, oder Verständnisfragen klären."
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
        with st.spinner("Thinking..."):
            response = chat_with_ai(st.session_state.messages)
            if response:
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                log_message('assistant', response)

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

