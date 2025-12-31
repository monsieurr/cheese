import os
import sys
import datetime
import requests

IG_USER_ID = os.getenv("IG_USER_ID")
ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN")
BASE_URL = "https://graph.facebook.com/v18.0"

def post_image(image_url, caption):
    # 1. Create Container
    url = f"{BASE_URL}/{IG_USER_ID}/media"
    payload = {
        'image_url': image_url,
        'caption': caption,
        'access_token': ACCESS_TOKEN
    }
    r = requests.post(url, data=payload)
    if r.status_code != 200:
        print(f"Error creating container: {r.text}")
        sys.exit(1)
    container_id = r.json()['id']

    # 2. Publish
    url = f"{BASE_URL}/{IG_USER_ID}/media_publish"
    payload = {
        'creation_id': container_id,
        'access_token': ACCESS_TOKEN
    }
    r = requests.post(url, data=payload)
    print(f"Published status: {r.status_code} - {r.text}")

def main():
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    filename = f"{today}.jpg"
    
    # CHANGE THIS to your actual repo details
    repo_user = "YOUR_GITHUB_USER"
    repo_name = "YOUR_REPO_NAME"
    
    # Construct raw URL
    image_url = f"https://raw.githubusercontent.com/{repo_user}/{repo_name}/main/ready_to_post/{filename}"
    
    # Check if file exists
    if requests.head(image_url).status_code != 200:
        print(f"No image scheduled for today ({filename}). Exiting.")
        sys.exit(0)
    
    # Calculate Day Number for Caption
    dt = datetime.datetime.strptime(today, "%Y-%m-%d")
    day_num = dt.timetuple().tm_yday
    
    caption = f"Day {day_num} of 365. {today} \n#365project #dailyphoto"
    
    post_image(image_url, caption)

if __name__ == "__main__":
    main()