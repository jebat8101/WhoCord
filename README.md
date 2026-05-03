# 🕵️‍♂️ WhoCord

**Turn any username or Discord ID into a full identity profile.**

WhoCord automatically scans Discord messages across mutual guilds for tracking links, resolves them to find connected social media accounts, cross‑references **700+ sites**, runs deep email intelligence, extracts EXIF data from avatars, and generates a polished AI‑powered OSINT report — all from a simple interactive menu or a **dark‑themed web dashboard**.

---

## ⚡ What makes WhoCord different?

Most OSINT tools stop at finding profiles. WhoCord goes further:

* **Discord‑native link resolution** – extracts and resolves Instagram, TikTok, Facebook, and Twitter tracking links shared by a target user.
* **Full identity pipeline** – names, emails, locations, breach data, GitHub history, and even avatar metadata are pulled together into one structured intelligence snapshot.
* **30+ integrated tools** – Sherlock, Maigret, Naminter, Blackbird, Holehe, h8mail, GitFive, GHunt, Scylla, Socialscan, and more, all controlled from a single interface.
* **AI‑generated reports** – LLaMA 3.3 (via Groq) produces a structured markdown summary with **relationship analysis** and **critical points of attention**.
* **Beautiful HTML report** – dark‑themed, responsive, with all intel displayed in collapsible sections (emails, breaches, Blackbird results, enriched profile data, timeline, and more).
* **Secure token storage** – API keys are stored in your operating system’s encrypted keyring, never in plain text.
* **Web dashboard** – run investigations from your browser with live progress streaming, tool toggles, token management, and in‑app report viewing.

---

## ✨ Features

### Discord link extraction
* Searches messages across **all mutual guilds** (or a specific guild) for shared links.
* Identifies tracking parameters (`igshid`, `fbclid`, `ttclid`, etc.) in Instagram, TikTok, Facebook, and Twitter URLs.
* Resolves those tracking links using ShareTrace to reveal the original sharer’s profile.

### Username discovery
* Scans **700+ websites** using Sherlock, Maigret, Naminter, Blackbird, and Social‑Analyzer.
* Spiders discovered URLs with Sociopath and Linkook to uncover even more related accounts.
* Filters false positives with Socialscan before scraping.
* **Blackbird** brings 600+ additional sites with email‑based search and avatar extraction.
* Blackbird results appear in their own dedicated HTML report section with avatars.

### ✉️ Manual email input
* You can optionally provide an email address in manual mode; it will be searched via Blackbird’s email detection and also forwarded to the email intelligence pipeline (Holehe, h8mail, etc.).
* No more automatic email guessing – only real, user‑supplied emails are processed.

### Profile scraping & enrichment
* Pulls public profile pages (GitHub, Twitter, Reddit, YouTube, etc.) with built‑in scrapers.
* Extracts display names, bios, avatars, follower counts, blog links, and embedded emails.
* Uses **Socid‑Extractor** to mine structured identity data from generic pages.
* Enriched profile data (account IDs, join dates, bios, avatar URLs) is displayed in a dedicated report section.

### ✉️ Email intelligence
* Runs each email through:
  * **Holehe** – checks which sites the email is registered on
  * **h8mail** – breach/compromise status
  * **HIBP** (HaveIBeenPwned) – known data breaches
  * **Emailrep.io** – reputation and risk score
  * **GHunt** – Google account information (requires `ghunt login` once)
  * **Scylla** – breach database lookup
* Breach results are presented in clean, readable cards with optional raw detail toggles.

### GitHub deep dive
* Collects public GitHub activity, pinned repositories, and profile details.
* Uses **GitFive** to dig up commit history, possible email addresses, and full name history.

### Avatar analysis
* Downloads avatar images and extracts **EXIF metadata** (GPS coordinates, camera model, date taken).
* Runs **reverse image search** via SauceNAO to find where else the image appears.

### Domain & history checks
* **WHOIS** lookups on blog domains found in profiles.
* **Wayback Machine** snapshot availability for all discovered URLs.

### Name analysis & identity scoring
* Predicts name origin, gender, and subregion using Nametrace.
* Computes fuzzy similarity between discovered names.
* Generates **confidence scores** to rank the most likely real‑world identity.

### AI report
With a Groq API key, WhoCord sends the collected evidence to LLaMA 3.3 and gets back a structured markdown report containing:
* Executive summary
* Identity assessment
* Digital footprint
* Risk indicators
* **Relationship analysis** – connections between data points (username reuse, email‑platform linking)
* **Critical points of attention** – most important findings requiring immediate action
* Recommended next steps

---

## 📦 Installation

### 1. Clone the repository
```bash
git clone https://github.com/Siv-nick/WhoCord.git
cd WhoCord
```
If you don’t have `git`, download the ZIP from the green **< > Code** button and extract it.

### 2. Create a Python virtual environment (highly recommended)
```bash
python3 -m venv venv
```
Activate the environment:
* **Linux / macOS**: `source venv/bin/activate`
* **Windows (Command Prompt)**: `venv\Scripts\activate`
* **Windows (PowerShell)**: `.\venv\Scripts\Activate`

### 3. Install WhoCord and its Python dependencies
```bash
pip install -e .
```
This installs WhoCord **and** all required Python libraries (`requests`, `beautifulsoup4`, `flask`, `keyring`, `jinja2`, `openai`, `socid-extractor`, etc.).

### 4. Install external command‑line tools
```bash
pip install sherlock-project maigret holehe h8mail gitfive naminter linkook sociopath
```

### 5. Install Blackbird (email & username search on 600+ sites)
```bash
git clone https://github.com/p1ngul1n0/blackbird
cd blackbird
pip install -r requirements.txt
cd ..
```
> **Note:** Blackbird's data file (`wmn-data.json`) is auto‑downloaded on first use. If that fails, download it manually from [WhatsMyName](https://raw.githubusercontent.com/WebBreacher/WhatsMyName/main/wmn-data.json) and place it in `blackbird/data/`.

### 6. Optional but powerful extras
```bash
# WHOIS lookups
sudo apt install whois    # Linux
brew install whois        # macOS

# GHunt for Google account info (requires `ghunt login` after install)
pip install ghunt
ghunt login
```

### 7. Launch WhoCord
```bash
discord-osint
```
The interactive menu will appear.

### 8. Launch the web dashboard (optional)
```bash
python3 web_app.py
```
Then open `http://127.0.0.1:5000`.  
Or use the one‑click launcher: `./run.sh` (starts server + opens browser, no terminal visible).

---

## 🚀 Usage

### Interactive menu (recommended)
```
==================================================
        OSINT IDENTITY PROFILING PIPELINE
==================================================
1. Toggle investigation tools
2. Set tokens / API keys
3. Start investigation
4. Save config and exit
5. Toggle debug mode
==================================================
```
* **Option 1** – Enable or disable any of the 33 tools with a single keypress.
* **Option 2** – Enter your API tokens (stored securely in your OS keyring).
  * Discord token (required for Discord mode)
  * GitHub token (increases API rate limits)
  * Groq API key (enables AI report)
  * Instagram session (optional, reserved for future Toutatis integration)
* **Option 3** – Choose `Manual` (investigate a username) or `Discord` (investigate a Discord user ID). In Manual mode you can optionally provide an email.
* **Option 4** – Save current configuration to `config.json` and exit.
* **Option 5** – Toggle debug mode for live subprocess output and debug logs.

### Command‑line mode
```bash
discord-osint --mode manual --target someusername --output html --debug
```

| Argument | Description |
|---|---|
| `--mode` | `discord` or `manual` |
| `--target` | username (manual) or Discord user ID (discord) |
| `--token` | Discord user token (overrides saved one) |
| `--guild` | Discord guild ID (for single‑guild search) |
| `--output` | `json`, `markdown`, or `html` |
| `--debug` | Enable debug logging |
| `--interactive` | Force the interactive menu |

### Web dashboard
* **Investigate tab** – enter username/email (manual mode) or user/guild IDs (Discord mode), start with one click, and view live streaming output.
* **Configuration tab** – set tokens and toggle tools right in the browser; badges update instantly.
* **Live Logs tab** – watch the investigation unfold in real time (SSE streaming).
* **Report tab** – view the generated HTML report inside the dashboard.
* **Stop button** – kill any running investigation immediately.

---

## 📁 Output files

All results are saved in the **`investigation_cache/`** folder:

| File | Description |
|---|---|
| `intel_*.json` | Complete intelligence snapshot (structured JSON) |
| `report_*.md` | AI‑generated markdown report (if Groq is enabled) |
| `report_*.html` | Interactive HTML report (if `--output html` is used) |

Raw outputs are archived in:
* `investigation_cache/blackbird_output/`
* `investigation_cache/socialscan_output/`

### HTML report sections
* 📱 Discord Identity
* 🌐 Discovered Social Profiles
* ✉️ Emails
* 🔓 Breach Intelligence
* 🧪 Enriched Profile Data
* 🧩 Identity Clues
* 🌍 WHOIS Information
* 📸 Media / EXIF
* 🔬 Name Analysis
* 🏆 Identity Confidence Scores
* 🕰️ Wayback Machine Snapshots
* 🐦 Blackbird Search Results
* ⏱️ Investigation Timeline

---

## 🛠️ Tools & technologies

WhoCord orchestrates these fantastic open‑source OSINT projects:

| Tool | Purpose |
|---|---|
| [Sherlock](https://github.com/sherlock-project/sherlock) | Username search across 400+ sites |
| [Maigret](https://github.com/soxoj/maigret) | Full‑spectrum username search with metadata |
| [Blackbird](https://github.com/p1ngul1n0/blackbird) | Email & username search on 600+ sites |
| [Holehe](https://github.com/megadose/holehe) | Checks which sites an email is registered on |
| [h8mail](https://github.com/khast3x/h8mail) | Email breach & compromise checker |
| [GitFive](https://github.com/mxrch/gitfive) | GitHub user intelligence |
| [Naminter](https://github.com/s0md3v/naminter) | Username search with smart filtering |
| [Linkook](https://github.com/JackJu1y/Linkook) | Deep URL discovery across platforms |
| [Sociopath](https://github.com/s0md3v/sociopath) | Profile spider & identity enrichment |
| [Socid‑Extractor](https://github.com/soxoj/socid-extractor) | Extracts structured identity data |
| [Socialscan](https://github.com/iojw/socialscan) | Validates social media profile availability |
| [ShareTrace](https://github.com/s0md3v/sharetrace) | Resolves social media tracking links |
| [Scylla](https://github.com/MandConsultingGroup/Scylla) | Leak database query |
| [NameTrace](https://github.com/s0md3v/nametrace) | Name origin & gender prediction |
| [ExifRead](https://github.com/ianare/exif-py) | EXIF metadata extraction from images |
| [SauceNAO](https://saucenao.com/) | Reverse image search (via API) |
| [Groq](https://groq.com) | LLaMA 3.3 AI report generation |

---

## 🔄 Updates

### 1.0.2
* **Web dashboard** – run investigations from your browser with live streaming.
* **Enhanced AI report** – now includes relationship analysis and critical points of attention.
* **Enriched profile data** – socid‑extractor results displayed in a dedicated report section.
* **Blackbird results** – dedicated report section with avatars for all discovered accounts.
* **Formatted breaches** – clean, readable cards with optional raw detail toggles.
* **Live log streaming** – SSE‑based real‑time output in the web dashboard.
* **One‑click launcher** – `run.sh` starts the dashboard without a terminal.
* **Stop button** – kill any running investigation from the web UI.
* **Token status** – dashboard badges update instantly when tokens are saved.
* **Centralised logging** – structured logging via `logger.py`.

### 1.0.1
* Blackbird integration – email‑based discovery and 600+ additional username sites.
* Email guesser removed.
* GHunt now requires one‑time `ghunt login`.

---

## 🔒 Security & privacy

* **Tokens are never stored in plain text.** They are kept in your OS keyring (Windows Credential Manager, macOS Keychain, or Linux Secret Service / KWallet).
* The `config.json` file only contains tool toggles and preferences – no secrets.
* All investigation data stays on your machine inside the `investigation_cache/` folder.

---

## ⚠️ Disclaimer

WhoCord is intended for **educational purposes** and **authorised security testing** only.  
Do not use it to stalk, harass, or violate anyone’s privacy.  
The author assumes no liability for misuse.

---

## 📄 License

MIT License
