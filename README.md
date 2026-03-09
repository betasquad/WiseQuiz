# OWS Quiz 🧠

A web-based **One Word Substitution** quiz app built with Flask and Google Sheets. Questions and scores are stored live in a Google Sheet — no database needed.

## How It Works

- Questions and answers are pulled from a Google Sheet
- Each phrase is shown with 4 multiple-choice options and a 10-second timer
- Correct answers increment the **Corrects** counter; every attempt increments **Attempts**
- Once a phrase reaches **10 correct answers**, it's retired from the quiz
- When all phrases are mastered, a completion screen is shown

## Tech Stack

- **Python / Flask** — web server
- **Google Sheets (gspread)** — question bank and score storage
- **OAuth2 / Service Account** — Google Sheets authentication
- **Render** — deployment

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Add credentials

Create a `credentials.json` file with your Google Service Account key (do **not** commit this).

Set environment variables:

```bash
export SECRET_KEY=your_random_secret
```

### 4. Google Sheet format

Your sheet must have these columns:

| Phrases | One Word | Corrects | Attempts |
|---------|----------|----------|----------|
| A person who can't read | Illiterate | 0 | 0 |

Share the sheet with your service account email (`client_email` in `credentials.json`).

### 5. Run locally

```bash
python ows.py
```

Visit `http://localhost:5000`

## Deployment (Render)

1. Push to GitHub
2. Create a new **Web Service** on [render.com](https://render.com)
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `python ows.py`
5. Add `SECRET_KEY` as an environment variable
6. Upload `credentials.json` as a secret file

## Security Notes

> ⚠️ Never commit `credentials.json` or `.env` to GitHub.

Add to `.gitignore`:
```
.env
credentials.json
```

