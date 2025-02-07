

import csv
from youtube_comment_downloader import YoutubeCommentDownloader

def scrape_youtube_comments(video_url, max_comments=100):
    downloader = YoutubeCommentDownloader()
    comments = []
    
    # Get comments and limit manually
    for idx, comment in enumerate(downloader.get_comments_from_url(video_url)):
        if idx >= max_comments:
            break
        comments.append({
            "author": comment["author"],
            "text": comment["text"],
            "likes": comment["votes"],
            "time": comment["time"],
        })
    
    return comments

def save_comments_to_csv(comments, filename="youtube_comments.csv"):
    """Save comments to a CSV file."""
    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["author", "text", "likes", "time"])
        writer.writeheader()
        writer.writerows(comments)
    print(f"Comments saved to {filename}")

# Example Usage
video_url = "https://www.youtube.com/watch?v=pMHpuTQFOQQ"  # Replace with your video URL
comments = scrape_youtube_comments(video_url, max_comments=50)

# Save comments to CSV
save_comments_to_csv(comments, "youtube_comments.csv")
