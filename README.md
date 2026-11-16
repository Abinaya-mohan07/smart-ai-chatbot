# 🤖 Smart AI Chatbot with Multi-Turn Conversation Memory

A chatbot built with **Python**, **Streamlit** and the **Google Gemini API** that remembers
what you said earlier in the conversation. Created as an AI internship project at
**Valentius Kryptix**.

## Project Objectives
- Connect a real LLM (Google Gemini) to a web chat interface.
- Support multi-turn conversations (the bot remembers earlier messages).
- Manage the context window so history never grows without limit.
- Handle API and network errors gracefully.
- Keep the API key secure (`.env`, never uploaded to GitHub).

## Technologies Used
| Purpose | Tool |
|---|---|
| Language | Python 3.10+ |
| AI model | Google Gemini (default `gemini-2.5-flash`) |
| SDK | Google Gen AI Python SDK (`google-genai`) |
| Frontend | Streamlit |
| Secrets | python-dotenv |
| Editor | VS Code |

## Features
- ✅ Real Gemini API responses (no fake/predefined answers)
- ✅ Multi-turn memory ("My name is Abinaya" → "What is my name?" → "Abinaya")
- ✅ Context window management (latest 10 messages) + preserved key facts
- ✅ Optional AI summarization of older messages (advanced toggle)
- ✅ Friendly system prompt (helpful, clear, simple, context-aware)
- ✅ Streamlit chat UI, loading spinner, Clear Chat button, memory status sidebar
- ✅ Error handling: invalid key, no connection, timeout, rate limit, busy server, bad model name
- ✅ API key stored in `.env` and excluded by `.gitignore`

## Project Folder Structure
```
smart-ai-chatbot/
├── app.py              # Streamlit web interface (what the user sees)
├── chatbot.py          # Gemini connection, memory, context management, error handling
├── config.py           # Loads .env; API key, model, limits, system prompt
├── utils.py            # Helpers: trimming history, fact extraction, prompt building
├── requirements.txt    # Python packages to install
├── .env                # YOUR secret API key (never uploaded to GitHub)
├── .env.example        # Safe template showing which variables exist
├── .gitignore          # Tells Git to ignore .env, venv, caches
├── README.md           # This documentation
├── SETUP_GUIDE.md      # Step-by-step beginner guide (VS Code, GitHub, errors)
└── tests/
    └── test_chatbot.py # Automated tests (no API key needed)
```

## How Context Window Management Works
Every request to Gemini contains three things:

1. **System prompt** – always sent, never removed.
2. **Preserved context** – (a) *key facts* found in your messages (name, city, likes…) are
   saved and always re-sent; (b) optionally an AI-written *summary* of removed messages.
3. **The latest 10 messages** – the recent conversation, sent as proper user/model turns.

When the conversation goes beyond 10 messages, the oldest ones are removed from what is
sent to the API. Because key facts (and the optional summary) are kept, the bot can still
answer "What is my name?" even after the original message was cut off.
The full chat remains visible on screen; only the data sent to the API is limited.

You can change the limit with `MAX_CONTEXT_MESSAGES` in `.env`.

## Installation (Windows / PowerShell)
```powershell
cd smart-ai-chatbot
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
If activation is blocked, run once:
`Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`

## API Key Setup
1. Open https://aistudio.google.com/apikey and sign in with a Google account.
2. Click **Create API key** and copy it.
3. Open `.env` and set: `GEMINI_API_KEY=paste_your_key_here`
4. Save the file. **Never share or upload this key.**

## How to Run
```powershell
streamlit run app.py
```
The browser opens at http://localhost:8501. (Optional terminal mode: `python chatbot.py`.)

## Screenshots
Add your screenshots in a `screenshots/` folder and link them here:

![Home screen](screenshots/home.png)
![Memory test](screenshots/memory.png)
![Error handling](screenshots/error.png)

## Testing Instructions

### Automated tests (no API key needed)
```powershell
python -m unittest discover -s tests -v
```

### Manual tests in the app
| # | Test | Steps | Expected result |
|---|---|---|---|
| 1 | Normal question | Ask "What is Python?" | A real AI answer appears |
| 2 | Name memory | Say "My name is Abinaya." then ask "What is my name?" | "Your name is Abinaya." |
| 3 | Follow-up | Ask "What is an API?" then "Explain that more simply." | Answer refers to the API explanation |
| 4 | History kept | Send 4–5 messages | All appear on screen; sidebar count grows |
| 5 | Context limit | Send more than 10 messages | Sidebar shows "Older messages removed"; bot still knows your name |
| 6 | Invalid key | Put `abc123` as the key in `.env`, restart, send a message | Red message: API key invalid (no crash) |
| 7 | Network failure | Turn off Wi-Fi, send a message | Red message: could not connect (no crash) |
| 8 | Clear chat | Click **Clear Chat**, ask "What is my name?" | Bot no longer knows your name |

## License
For educational use as part of an internship project.
