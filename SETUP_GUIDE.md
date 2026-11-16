# Beginner Setup Guide (Windows + VS Code)

## Part A – Run the project

### 1. Install the tools (one time)
- **Python 3.10 or newer**: https://www.python.org/downloads/ → during install tick **"Add python.exe to PATH"**.
- **VS Code**: https://code.visualstudio.com/ (install the **Python** extension from the Extensions tab).
- **Git**: https://git-scm.com/downloads
Check in PowerShell:
```powershell
python --version
git --version
```

### 2. Get the project folder
Unzip `smart-ai-chatbot.zip` (right-click → Extract All) to a place like `C:\Projects\`.

### 3. Open it in VS Code
- Open VS Code → **File → Open Folder…** → choose `smart-ai-chatbot`.
- Open the terminal: **Terminal → New Terminal** (make sure it says PowerShell).

### 4. Create and activate a virtual environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```
You should see `(venv)` at the start of the line. If you get a red "running scripts is disabled" error:
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```
(press `Y`), then activate again. If VS Code asks to use the new environment, click **Yes**.

### 5. Install the packages
```powershell
pip install -r requirements.txt
```

### 6. Get a Gemini API key
1. Go to https://aistudio.google.com/apikey and sign in.
2. Click **Create API key** → copy the key.

### 7. Put the key in `.env`
Open `.env` in VS Code and change it to:
```
GEMINI_API_KEY=AIzaSy...your-real-key...
```
No quotes, no spaces. Save with **Ctrl+S**.

### 8. Start the app
```powershell
streamlit run app.py
```
Your browser opens `http://localhost:8501`. (If asked for an email, press Enter to skip.)
Stop the app anytime with **Ctrl+C** in the terminal.

### 9. Test everything
Run the automated tests:
```powershell
python -m unittest discover -s tests -v
```
Then follow the 8 manual tests in `README.md` (name memory, follow-up, context limit, invalid key, network failure, clear chat).

To test the invalid-key case: change the key in `.env` to `abc123`, restart Streamlit, send a message, and watch for the friendly error. **Put your real key back afterwards.**

### 10. Fix common errors
| Problem | Fix |
|---|---|
| `python is not recognized` | Reinstall Python and tick **Add to PATH**; reopen VS Code |
| `streamlit is not recognized` | Activate the venv: `.\venv\Scripts\Activate.ps1`, then `pip install -r requirements.txt` |
| `ModuleNotFoundError: google` | Run `pip install -r requirements.txt` inside the activated venv |
| "No Gemini API key found" | `.env` must be in the project root and contain `GEMINI_API_KEY=...`; save, then restart |
| "API key is invalid" | Copy the key again from AI Studio; no quotes/spaces |
| "Rate limit reached" | Free tier limit; wait a minute and retry |
| "Model not found" | Google retired the model. Add `GEMINI_MODEL=<current model name>` to `.env` (see https://ai.google.dev/gemini-api/docs/models) |
| "Could not connect" | Check internet, VPN or firewall |
| Changed `.env` but nothing changed | Stop (Ctrl+C) and run `streamlit run app.py` again |

## Part B – Upload to GitHub (keeping the key private)

### 1. Confirm `.env` is ignored
`.gitignore` already contains `.env`. Never delete that line.

### 2. Create the repository
1. Sign in at https://github.com → click **+ → New repository**.
2. Name: `smart-ai-chatbot`. Choose **Public**.
3. Do **NOT** tick "Add a README" or ".gitignore" (we already have them). Click **Create repository**.

### 3. Push the project
In the VS Code terminal (inside the project folder):
```powershell
git init
git add .
git status
```
Look at the list: **`.env` must NOT appear**. (`.env.example` is fine.) Then:
```powershell
git commit -m "Initial commit: Smart AI Chatbot"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/smart-ai-chatbot.git
git push -u origin main
```
(Use your own username. Sign in when asked.)
If Git says "Please tell me who you are", run:
```powershell
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

### 4. Check it online
Refresh the GitHub page: you should see all files, a nicely formatted README, and **no `.env`**.

### 5. Add screenshots (optional but recommended)
Take screenshots, save them in a `screenshots` folder as `home.png`, `memory.png`, `error.png`, then:
```powershell
git add .
git commit -m "Add screenshots"
git push
```

### 6. Submit
Copy the repository URL from the browser (`https://github.com/YOUR-USERNAME/smart-ai-chatbot`) and submit it to Valentius Kryptix.

### If you accidentally uploaded your real key
Immediately delete the key at https://aistudio.google.com/apikey and create a new one. Removing the file from GitHub is not enough, because Git keeps history.
