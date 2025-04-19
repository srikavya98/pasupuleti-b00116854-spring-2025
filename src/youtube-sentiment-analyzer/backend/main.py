from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import os
import requests
import re
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from bs4 import BeautifulSoup
from textblob import TextBlob
from urllib.parse import urlparse, parse_qs

# Load environment variables
load_dotenv()

# Download necessary NLTK data
nltk.download("punkt")
nltk.download("wordnet")
nltk.download("vader_lexicon")

# Initialize FastAPI app
app = FastAPI()

# Allow frontend (localhost:5173) to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize VADER analyzer
analyzer = SentimentIntensityAnalyzer()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# Request body model
class AnalyzeRequest(BaseModel):
    url: str



# --- Cleaning Functions ---



def remove_emojis(text):
    """Remove all emojis from the given text."""
    emoji_pattern = re.compile(
        "[" 
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002700-\U000027BF"  # Dingbats
        u"\U000024C2-\U0001F251"  # Enclosed characters
        "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text)

def remove_urls(text):
    return re.sub(r'http[s]?://\S+', '', text)

def remove_html_tags(text):
    return BeautifulSoup(text, "html.parser").get_text()

def lemmatize_text(text):
    lemmatizer = WordNetLemmatizer()
    words = word_tokenize(text)
    lemmatized_words = [lemmatizer.lemmatize(word) for word in words]
    return " ".join(lemmatized_words)

def correct_spelling(text):
    return str(TextBlob(text).correct())

def clean_comment(text: str):
    text = text.strip()
    text = text.lower()
    text = remove_html_tags(text)
    text = remove_urls(text)
    text = remove_emojis(text)
    text = correct_spelling(text)
    # text = lemmatize_text(text) # Optional
    return text

# --- NEW: LibreTranslate Function ---
def translate_to_english(text: str) -> str:
    try:
        response = requests.post("https://libretranslate.com/translate", data={
            "q": text,
            "source": "auto",
            "target": "en",
            "format": "text"
        })
        result = response.json()
        return result.get("translatedText", text)
    except Exception as e:
        print(f"Translation failed: {e}")
        return text  # fallback: return original text if API fails

# --- Helper Functions ---
def extract_video_id(url: str):
    parsed_url = urlparse(url)
    if parsed_url.hostname in ["www.youtube.com", "youtube.com"]:
        query_params = parse_qs(parsed_url.query)
        return query_params.get("v", [None])[0]
    elif parsed_url.hostname == "youtu.be":
        return parsed_url.path.lstrip("/")
    return None

def analyze_sentiment(text: str):
    scores = analyzer.polarity_scores(text)
    compound = scores['compound']
    if compound >= 0.05:
        return "Positive"
    elif compound <= -0.05:
        return "Negative"
    else:
        return "Neutral"

# --- Main Route ---
@app.post("/analyze")
async def analyze_comments(request: AnalyzeRequest):
    video_id = extract_video_id(request.url)

    if not video_id:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")

    try:
        youtube_api_url = "https://www.googleapis.com/youtube/v3/commentThreads"
        params = {
            "part": "snippet",
            "videoId": video_id,
            "key": YOUTUBE_API_KEY,
            "maxResults": 10
        }
        response = requests.get(youtube_api_url, params=params)
        response.raise_for_status()

        comments = [
            item['snippet']['topLevelComment']['snippet']['textDisplay']
            for item in response.json().get('items', [])
        ]

        sentiments = []
        for comment in comments:
            cleaned_comment = clean_comment(comment)
            
            translated_comment = translate_to_english(cleaned_comment)

            if translated_comment.strip() == "":
                continue
            else:
                sentiment = analyze_sentiment(translated_comment)
            sentiment = analyze_sentiment(translated_comment)
            sentiments.append({
                "comment": translated_comment,
                "sentiment": sentiment
                # "original_comment": comment,
                # "cleaned_comment": cleaned_comment,
                # "translated_comment": translated_comment,
                # "sentiment": sentiment
            })

        return {
            "videoId": video_id,
            "total_comments": len(sentiments),
            "sentiments": sentiments
        }

    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Failed to analyze comments")
