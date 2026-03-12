import feedparser
import requests

DEFAULT_RSS_URL = "https://www.gelonghui.com/api/live-channels/all/lives/v4?category=important&limit=15"

def fetch_rss_feed(url: str = DEFAULT_RSS_URL) -> str:
    """
    Fetches an RSS feed or JSON API and returns the extracted articles as text.
    If no URL is provided, defaults to the Gelonghui important news live feed.
    """
    print(f"Fetching data from: {url}")
    
    all_articles = ""
    
    # 1. Try finding entries via standard RSS (feedparser)
    feed = feedparser.parse(url)
    if feed.entries:
        for entry in feed.entries[:10]:
            title = entry.get("title", "No Title")
            summary = entry.get("summary", "No Summary")
            all_articles += f"Title: {title}\nContent Snippet: {summary}\n\n"
    else:
        # 2. Add fallback for JSON APIs (like Gelonghui live channels)
        print("No RSS entries found, attempting to fetch and parse as JSON API...")
        try:
            # Add comprehensive headers to mimic browser in case of 403 Forbidden or WAF blocking
            headers = {
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7,zh-TW;q=0.6",
                "Client-Lang": "zh-cn",
                "DNT": "1",
                "Origin": "https://www.gelonghui.com",
                "Referer": "https://www.gelonghui.com/live/",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
                "platform": "web",
                "sec-ch-ua": '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"macOS"',
                "shortVersion": "10.7.0"
            }
            # Increased timeout since some APIs (especially overseas) can be slow
            response = requests.get(url, headers=headers, timeout=20)
            response.raise_for_status()
            data = response.json()
            
            # Check for Gelonghui specific structure
            if "result" in data and isinstance(data["result"], list):
                for item in data["result"][:10]:
                    title = item.get("title", "No Title (Live Update)")
                    content = item.get("content", "No Content")
                    all_articles += f"Title: {title}\nContent Snippet: {content}\n\n"
            else:
                return f"Parsed JSON, but format is unrecognized. Keys found: {list(data.keys())}"
        except Exception as e:
            return f"Could not parse the URL as RSS or JSON. Error: {e}"

    if not all_articles.strip():
        return "No text content could be extracted from this URL."
        
    return all_articles
