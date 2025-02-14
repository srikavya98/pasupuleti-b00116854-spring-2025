import pandas as pd
import re
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from bs4 import BeautifulSoup
from textblob import TextBlob

# Download necessary NLTK data
nltk.download("punkt")
nltk.download("wordnet")

def remove_urls(text):
    """Removes URLs from the text."""
    return re.sub(r'http[s]?://\S+', '', text)  # Removes http and https links

def remove_html_tags(text):
    """Removes HTML tags from text."""
    return BeautifulSoup(text, "html.parser").get_text()

def lemmatize_text(text):
    """Lemmatizes each word in a text string."""
    lemmatizer = WordNetLemmatizer()
    words = word_tokenize(text)  # Tokenize text
    lemmatized_words = [lemmatizer.lemmatize(word) for word in words]
    return " ".join(lemmatized_words)  # Join words back into a sentence

def correct_spelling(text):
    """Corrects spelling mistakes in text."""
    return str(TextBlob(text).correct())

def clean_youtube_comments(input_file, output_file):
    # Load the CSV file
    df = pd.read_csv(input_file)

    # Remove duplicates
    df = df.drop_duplicates()

    # Remove empty or null comments
    df = df.dropna(subset=["text"])

    # Strip whitespace from all text fields
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

    # Normalize text encoding (handling special characters)
    df["text"] = df["text"].str.encode("utf-8", "ignore").str.decode("utf-8")

    # Convert text to lowercase
    df["text"] = df["text"].str.lower()

    # Remove HTML tags from text
    df["text"] = df["text"].apply(remove_html_tags)

    # Remove URLs from text
    df["text"] = df["text"].apply(remove_urls)

    # Correct spelling mistakes
    df["text"] = df["text"].apply(correct_spelling)

    # Apply lemmatization on the text field
    # df["text"] = df["text"].apply(lemmatize_text)

    # Convert 'likes' column to integers (handling any non-numeric values)
    df["likes"] = pd.to_numeric(df["likes"], errors="coerce").fillna(0).astype(int)

    # Standardize the 'time' format (simplifying text representation)
    df["time"] = df["time"].str.replace("minutes ago", "min", regex=False)
    df["time"] = df["time"].str.replace("hours ago", "hr", regex=False)
    df["time"] = df["time"].str.replace("hour ago", "1 hr", regex=False)

    # Remove '@' from author names
    df["author"] = df["author"].str.replace("@", "", regex=False)

    # Save cleaned data to a new CSV file
    df.to_csv(output_file, index=False, encoding="utf-8")
    print(f"Cleaned data saved to {output_file}")

# Example usage
input_file = "code\youtube_comments.csv"  # Replace with your actual file path
output_file = "cleaned_youtube_comments.csv"
clean_youtube_comments(input_file, output_file)
