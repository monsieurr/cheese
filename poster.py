import os
import sys
import datetime
import requests
import time
import argparse
from dotenv import load_dotenv

# Load .env file for local dev
load_dotenv()

# --- CONFIGURATION & SECRETS ---
IG_USER_ID = os.getenv("IG_USER_ID")
ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN")

# GitHub Repo Details
REPO_OWNER = os.getenv("GITHUB_REPOSITORY_OWNER")
REPO_NAME = os.getenv("GITHUB_REPOSITORY")
if REPO_NAME and "/" in REPO_NAME:
    REPO_NAME = REPO_NAME.split("/")[-1]

BASE_URL = "https://graph.facebook.com/v19.0"

def generate_auto_caption():
    """Helper to generate the dynamic Day X of 365 caption."""
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    dt = datetime.datetime.now()
    day_num = dt.timetuple().tm_yday
    return f"Day {day_num} of 365.\n{today}\n\n#2026 #project365 #dailyphoto"

def upload_media(image_url, caption, is_story=False):
    """
    Handles the upload process: Create Container -> Publish Container
    """
    media_type_str = "STORY" if is_story else "FEED"
    print(f"🚀 Starting upload for: {media_type_str}")

    # Step 1: Create Container
    url = f"{BASE_URL}/{IG_USER_ID}/media"
    params = {
        'image_url': image_url,
        'access_token': ACCESS_TOKEN,
    }
    
    if is_story:
        params['media_type'] = 'STORIES'
        # Stories generally don't use the caption field in the API the same way Feed does,
        # but the API accepts it without error.
    else:
        params['caption'] = caption

    # Retry logic (Meta API sometimes timeouts)
    container_id = None
    for attempt in range(3):
        r = requests.post(url, params=params)
        if r.status_code == 200:
            container_id = r.json()['id']
            break
        print(f"   ⚠️ Attempt {attempt+1} failed: {r.text}")
        time.sleep(5)
    
    if not container_id:
        print(f"   ❌ Failed to create {media_type_str} container.")
        return False 

    # Wait for Meta to process the image (Critical step)
    time.sleep(10) 

    # Step 2: Publish
    publish_url = f"{BASE_URL}/{IG_USER_ID}/media_publish"
    pub_params = {
        'creation_id': container_id,
        'access_token': ACCESS_TOKEN
    }
    r = requests.post(publish_url, params=pub_params)
    
    if r.status_code == 200:
        print(f"   ✅ Published to {media_type_str} successfully! ID: {r.json()['id']}")
        return True
    else:
        print(f"   ❌ Failed to publish {media_type_str}: {r.text}")
        return False

def main():
    # --- ARGUMENT PARSING ---
    parser = argparse.ArgumentParser(description="Post to Instagram")
    
    # Mode Argument
    parser.add_argument(
        '--mode', 
        choices=['both', 'feed', 'story'], 
        default='both', 
        help="Choose where to post: 'feed', 'story', or 'both' (default)"
    )
    
    # Caption Argument
    parser.add_argument(
        '--caption', 
        type=str, 
        default="", 
        help="Text for the post caption. Defaults to empty. Use 'AUTO' to generate 'Day X of 365'."
    )
    
    args = parser.parse_args()
    # ------------------------

    if not IG_USER_ID or not ACCESS_TOKEN:
        print("❌ Error: Missing Secrets (IG_USER_ID or IG_ACCESS_TOKEN)")
        sys.exit(1)

    today = datetime.datetime.now().strftime("%Y-%m-%d")
    filename = f"{today}.jpg"
    
    # Construct URL
    if not REPO_OWNER or not REPO_NAME:
        print("❌ Error: Missing Repo Details in .env or Env Vars")
        sys.exit(1)
        
    image_url = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/ready/{filename}"
    
    # Verify Image Exists
    print(f"🔎 Checking for image: {filename}")
    check = requests.head(image_url)
    if check.status_code != 200:
        print(f"⚠️ No image found for today ({today}). Skipping.")
        sys.exit(0)

    # Logic to handle Caption
    final_caption = args.caption
    if args.caption == "AUTO":
        final_caption = generate_auto_caption()
        print(f"📝 Generated Auto-Caption: {final_caption.splitlines()[0]}...")
    else:
        print(f"📝 Caption: '{final_caption}'")

    # Execution Logic based on --mode
    success = True
    
    if args.mode in ['both', 'feed']:
        if not upload_media(image_url, final_caption, is_story=False):
            success = False

    if args.mode in ['both', 'story']:
        # Note: Stories usually don't display the caption text visibly on the image
        if not upload_media(image_url, "", is_story=True):
            success = False

    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()