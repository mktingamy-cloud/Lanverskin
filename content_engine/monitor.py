import requests
import json
import os

# Keywords mapped to topic categories
TOPICS = {
    "CRT": ["crt", "cathode ray tube", "monochrome", "phosphor", "scanline", "scanlines", "degauss"],
    "COBOL": ["cobol", "legacy code", "mainframe", "mainframes", "y2k", "grace hopper", "fortran", "assembly"],
    "RETRO_HARDWARE": ["nes", "snes", "sega", "console", "commodore", "amiga", "atari", "cartridge", "gameboy", "lockout chip", "6502"],
    "NETSCAPE_90S_WEB": ["netscape", "dial-up", "dialup", "modem", "90s web", "web 1.0", "web1", "comet trail", "handshake tone"],
    "MECHANICAL_KEYBOARDS": ["mechanical keyboard", "keycap", "keycaps", "cherry mx", "buckling spring", "model m", "mx blue", "key switch"],
    "LINUX_UNIX": ["linux", "unix", "linus torvalds", "kernel", "terminal", "bash", "command line", "open source history"],
    "THINKPAD": ["thinkpad", "ibm laptop", "trackpoint", "clit mouse", "vintage laptop"],
    "RETRO_GAMING": ["retro game", "retro gaming", "arcade", "8-bit", "16-bit", "coin-op", "high score", "joystick", "quarter pusher"]
}

def fetch_hacker_news_stories(limit=30):
    """Fetch top stories from Hacker News API."""
    print("Fetching top stories from Hacker News...")
    try:
        r = requests.get('https://hacker-news.firebaseio.com/v0/topstories.json', timeout=10)
        if r.status_code != 200:
            print(f"HN API Error: {r.status_code}")
            return []
        
        story_ids = r.json()[:limit]
        stories = []
        for sid in story_ids:
            try:
                detail_r = requests.get(f'https://hacker-news.firebaseio.com/v0/item/{sid}.json', timeout=5)
                if detail_r.status_code == 200:
                    stories.append(detail_r.json())
            except Exception as e:
                print(f"Error fetching HN item {sid}: {e}")
        return stories
    except Exception as e:
        print(f"Error calling HN API: {e}")
        return []

def fetch_dev_to_articles(limit=30):
    """Fetch recent articles from Dev.to API."""
    print("Fetching recent articles from Dev.to...")
    try:
        r = requests.get('https://dev.to/api/articles', timeout=10)
        if r.status_code != 200:
            print(f"Dev.to API Error: {r.status_code}")
            return []
        return r.json()[:limit]
    except Exception as e:
        print(f"Error calling Dev.to API: {e}")
        return []

def match_topic(text):
    """Match text against keywords and return the best fitting topic name or None."""
    text_lower = text.lower()
    best_topic = None
    max_matches = 0
    
    for topic, keywords in TOPICS.items():
        matches = sum(1 for kw in keywords if kw in text_lower)
        if matches > max_matches:
            max_matches = matches
            best_topic = topic
            
    return best_topic if max_matches > 0 else None

def scan_for_trends():
    """Scan HN and Dev.to for high-engagement retro/tech-culture matches."""
    matched_items = []
    
    # Process Hacker News
    hn_stories = fetch_hacker_news_stories()
    for story in hn_stories:
        title = story.get('title', '')
        url = story.get('url', f"https://news.ycombinator.com/item?id={story.get('id')}")
        score = story.get('score', 0)
        
        # Combine title and text if present
        full_text = title + " " + story.get('text', '')
        topic = match_topic(full_text)
        if topic:
            matched_items.append({
                "source": "Hacker News",
                "title": title,
                "url": url,
                "topic": topic,
                "score": score,
                "author": story.get('by', 'Anonymous')
            })
            
    # Process Dev.to
    dev_articles = fetch_dev_to_articles()
    for article in dev_articles:
        title = article.get('title', '')
        desc = article.get('description', '')
        tags = " ".join(article.get('tag_list', []))
        url = article.get('url', '')
        
        full_text = f"{title} {desc} {tags}"
        topic = match_topic(full_text)
        if topic:
            matched_items.append({
                "source": "Dev.to",
                "title": title,
                "url": url,
                "topic": topic,
                "score": article.get('public_reactions_count', 0),
                "author": article.get('user', {}).get('name', 'Anonymous')
            })
            
    # Sort matched items by engagement score (descending)
    matched_items.sort(key=lambda x: x['score'], reverse=True)
    return matched_items

if __name__ == "__main__":
    matches = scan_for_trends()
    print(f"\nScan complete. Found {len(matches)} matching trends.")
    for idx, item in enumerate(matches, 1):
        print(f"{idx}. [{item['topic']}] {item['title']} ({item['source']}, Score: {item['score']})")
