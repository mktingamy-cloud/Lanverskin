import os
import requests
import markdown
import re
import json

# Shopify API configurations
DOMAIN = 'pixelpulseapparel.myshopify.com'
BLOG_ID = 100973969566

def get_shopify_token():
    """Load Shopify Access Token from environment or ignored config.json."""
    # 1. Check environment variable
    token = os.environ.get("SHOPIFY_ACCESS_TOKEN")
    if token:
        return token
        
    # 2. Check local config.json in parent directory
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('shopify_access_token') or data.get('X-Shopify-Access-Token')
        except Exception as e:
            print(f"Error reading config.json: {e}")
            
    # Return placeholder or fallback
    return None

def parse_draft_file(filepath):
    """Parse title, meta description, body, and approval status from draft file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if approved
    approved = False
    approved_match = re.search(r'<!--\s*Approved:\s*(True|False|Processed)\s*-->', content, re.IGNORECASE)
    if approved_match and approved_match.group(1).lower() == 'true':
        approved = True
        
    lines = content.split('\n')
    title = ""
    meta_desc = ""
    body_lines = []
    found_separator = False
    
    for line in lines:
        if line.strip().startswith('<!--'):
            continue  # Skip comments/metadata headers
            
        if not found_separator:
            if line.startswith('# '):
                title = line[2:].strip()
            elif line.startswith('**Meta Description:**'):
                meta_desc = line[len('**Meta Description:**'):].strip()
            elif line.strip() == '---':
                found_separator = True
        else:
            body_lines.append(line)
            
    body_markdown = '\n'.join(body_lines).strip()
    return approved, title, meta_desc, body_markdown, content

def update_draft_status_to_processed(filepath, content):
    """Update approval status in file to Processed and save to both local and shared folders."""
    updated_content = re.sub(
        r'<!--\s*Approved:\s*True\s*-->',
        '<!-- Approved: Processed -->',
        content,
        flags=re.IGNORECASE
    )
    
    # Write back to current file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(updated_content)
        
    # Sync with shared folder equivalent if it exists
    filename = os.path.basename(filepath)
    shared_path = f"/home/team/shared/content_engine/review_queue/{filename}"
    if os.path.exists(shared_path):
        with open(shared_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
            
    print(f"Updated status to 'Processed' and synced for {filename}")

def publish_approved_articles():
    """Scan review queue and publish any approved drafts to Shopify blog."""
    token = get_shopify_token()
    if not token:
        print("ERROR: Shopify Access Token not found. Set SHOPIFY_ACCESS_TOKEN or configure config.json")
        return
        
    headers = {
        'X-Shopify-Access-Token': token,
        'Content-Type': 'application/json'
    }
    
    local_queue_dir = "/home/agent-automation-engineer/Lanverskin/review_queue"
    shared_queue_dir = "/home/team/shared/content_engine/review_queue"
    
    # Make sure local exists
    if not os.path.exists(local_queue_dir):
        print(f"Queue directory {local_queue_dir} does not exist yet. Run generator first.")
        return
        
    # Scan files in local queue
    files = [f for f in os.listdir(local_queue_dir) if f.endswith('.md')]
    print(f"Scanning {len(files)} drafts in queue...")
    
    published_count = 0
    
    for filename in files:
        filepath = os.path.join(local_queue_dir, filename)
        approved, title, meta_desc, body_markdown, raw_content = parse_draft_file(filepath)
        
        if not approved:
            # Also check the shared queue in case lead approved it there
            shared_filepath = os.path.join(shared_queue_dir, filename)
            if os.path.exists(shared_filepath):
                shared_approved, title, meta_desc, body_markdown, raw_content = parse_draft_file(shared_filepath)
                if shared_approved:
                    approved = True
                    filepath = shared_filepath  # Publish from shared file which has 'Approved: True'
                    
        if not approved:
            print(f"Draft '{filename}' is NOT approved yet. Skipping.")
            continue
            
        # Convert markdown to HTML
        body_html = markdown.markdown(body_markdown, extensions=['extra', 'codehilite'])
        
        print(f"\nPublishing '{title}' to Shopify blog...")
        
        payload = {
            "article": {
                "title": title,
                "author": "PixelPulse Team",
                "body_html": body_html,
                "summary_html": meta_desc,
                "published": True,
                "metafields": [
                    {
                        "key": "description_tag",
                        "value": meta_desc,
                        "type": "single_line_text_field",
                        "namespace": "global"
                    }
                ]
            }
        }
        
        pub_r = requests.post(
            f'https://{DOMAIN}/admin/api/2024-01/blogs/{BLOG_ID}/articles.json',
            headers=headers,
            json=payload
        )
        
        if pub_r.status_code == 201:
            created_art = pub_r.json().get('article', {})
            print(f"SUCCESS: Published article ID {created_art.get('id')} with handle '{created_art.get('handle')}'")
            published_count += 1
            # Mark as processed in local and shared files
            update_draft_status_to_processed(filepath, raw_content)
        else:
            print(f"FAILED to publish {filename}: {pub_r.status_code} - {pub_r.text}")
            
    print(f"\nPublishing run finished. Published {published_count} article(s).")

if __name__ == "__main__":
    publish_approved_articles()
