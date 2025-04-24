from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import os
import requests
import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

# Load env
load_dotenv()

# Download NLTK data
nltk.download("punkt")
nltk.download("wordnet")
nltk.download("vader_lexicon")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

analyzer = SentimentIntensityAnalyzer()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

class AnalyzeRequest(BaseModel):
    url: str

# Cleaners
def remove_emojis(text):
    emoji_pattern = re.compile(
        "["
        u"\U0001F600-\U0001F64F"
        u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF"
        u"\U0001F1E0-\U0001F1FF"
        u"\U00002700-\U000027BF"
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text)

def remove_urls(text):
    return re.sub(r'http[s]?://\S+', '', text)

def remove_html_tags(text):
    return BeautifulSoup(text, "html.parser").get_text()

def clean_comment(text: str):
    text = remove_html_tags(text)
    text = remove_urls(text)
    
    return text

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
        return text

def extract_video_id(url: str):
    parsed_url = urlparse(url)
    if parsed_url.hostname in ["www.youtube.com", "youtube.com"]:
        return parse_qs(parsed_url.query).get("v", [None])[0]
    elif parsed_url.hostname == "youtu.be":
        return parsed_url.path.lstrip("/")
    return None

def analyze_sentiment(text: str):
    compound = analyzer.polarity_scores(text)["compound"]
    if compound >= 0.05:
        return "Positive"
    elif compound <= -0.05:
        return "Negative"
    return "Neutral"

@app.post("/analyze")
async def analyze_comments(request: AnalyzeRequest, page: int = Query(1, ge=1), limit: int = Query(10, le=100)):
    video_id = extract_video_id(request.url)
    if not video_id:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")

    try:
        youtube_api_url = "https://www.googleapis.com/youtube/v3/commentThreads"
        comments = []
        next_page_token = None
        total_to_fetch = 100

        while len(comments) < total_to_fetch:
            params = {
                "part": "snippet",
                "videoId": video_id,
                "key": YOUTUBE_API_KEY,
                "maxResults": 100,
                "pageToken": next_page_token
            }
            response = requests.get(youtube_api_url, params=params)
            response.raise_for_status()
            data = response.json()

            for item in data.get("items", []):
                comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
                comments.append(comment)
                if len(comments) >= total_to_fetch:
                    break

            next_page_token = data.get("nextPageToken")
            if not next_page_token:
                break

        # Analyze all comments for chart
        all_sentiments = []
        for comment in comments:
            cleaned = clean_comment(comment)
            translated = translate_to_english(cleaned)
            if translated.strip():
                sentiment = analyze_sentiment(translated)
                all_sentiments.append(sentiment)

        # Analyze current page
        sentiments = []
        sentiment_summary = {"Positive": 0, "Neutral": 0, "Negative": 0}
        paginated = comments[(page - 1) * limit: page * limit]
        for comment in paginated:
            cleaned = clean_comment(comment)
            translated = translate_to_english(cleaned)
            if translated.strip():
                sentiment = analyze_sentiment(translated)
                sentiment_summary[sentiment] += 1
                sentiments.append({
                    "comment": translated,
                    "sentiment": sentiment
                })

        return {
            "videoId": video_id,
            "page": page,
            "limit": limit,
            "total_fetched": len(all_sentiments),
            "sentiments": sentiments,
            "sentiment_summary": sentiment_summary,
            "all_sentiments": all_sentiments
        }

    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Failed to analyze comments")
