import os
import requests
import json

# Replace with your Slack and Kumu API tokens
SLACK_TOKEN = 'xoxb-your-slack-token-here'
KUMU_API_TOKEN = 'your-kumu-api-token-here'
KUMU_PROJECT_ID = 'your-kumu-project-id-here'  # Replace with your Kumu project ID
PICTURE_DIR = 'slack_user_pictures'  # Directory where images will be saved

# Slack API URL
SLACK_URL = "https://slack.com/api/users.list"

# Headers for Slack API
slack_headers = {
    "Authorization": f"Bearer {SLACK_TOKEN}"
}

# Step 1: Get all users from Slack workspace
def fetch_slack_users():
    response = requests.get(SLACK_URL, headers=slack_headers)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch users from Slack. Status code: {response.status_code}")
    
    data = response.json()
    if not data['ok']:
        raise Exception(f"Error fetching Slack users: {data['error']}")
    
    users = data['members']
    return users

# Step 2: Download Slack profile pictures and save them to a directory
def download_profile_picture(url, user_id):
    if not os.path.exists(PICTURE_DIR):
        os.makedirs(PICTURE_DIR)

    picture_path = os.path.join(PICTURE_DIR, f"{user_id}.jpg")
    response = requests.get(url)
    if response.status_code == 200:
        with open(picture_path, 'wb') as file:
            file.write(response.content)
        return picture_path
    else:
        print(f"Failed to download image for {user_id}")
        return None

# Step 3: Upload image to Kumu and return the Kumu image URL
def upload_image_to_kumu(image_path):
    kumu_image_url = f"https://kumu.io/api/projects/{KUMU_PROJECT_ID}/uploads"
    
    headers = {
        'Authorization': f'Bearer {KUMU_API_TOKEN}'
    }

    with open(image_path, 'rb') as image_file:
        files = {'file': image_file}
        response = requests.post(kumu_image_url, headers=headers, files=files)
        
        if response.status_code == 200:
            image_data = response.json()
            return image_data.get('url')  # Return the URL of the uploaded image
        else:
            print(f"Failed to upload image {image_path}: {response.text}")
            return None

# Step 4: Format Slack user data for Kumu and associate it with the uploaded image URL
def format_for_kumu(slack_users):
    formatted_users = []
    for user in slack_users:
        if user.get('deleted'):
            continue  # Skip deactivated users
        
        slack_id = user.get('id', 'Unknown')
        real_name = user.get('real_name', 'Unknown')
        display_name = user.get('profile', {}).get('display_name', 'Unknown')
        email = user.get('profile', {}).get('email', 'Unknown')
        title = user.get('profile', {}).get('title', 'Unknown')
        image_72 = user.get('profile', {}).get('image_72', None)  # Slack user's profile image

        # Download and get the image path
        image_path = None
        if image_72:
            image_path = download_profile_picture(image_72, slack_id)

        # If the image was successfully downloaded, upload it to Kumu
        image_url = None
        if image_path:
            image_url = upload_image_to_kumu(image_path)

        # Format the user data for Kumu
        formatted_user = {
            "name": real_name,
            "description": f"Slack ID: {slack_id}\nDisplay Name: {display_name}\nEmail: {email}\nTitle: {title}",
            "type": "element",
            "image": image_url  # Associate the Kumu URL for the image
        }
        
        formatted_users.append(formatted_user)
    
    return formatted_users

# Step 5: Create a new Kumu diagram (project) and add users as elements (including images and descriptions)
def create_kumu_elements(kumu_data):
    kumu_url = f"https://kumu.io/api/projects/{KUMU_PROJECT_ID}/elements"
    
    headers = {
        'Authorization': f'Bearer {KUMU_API_TOKEN}',
        'Content-Type': 'application/json'
    }

    for element in kumu_data:
        response = requests.post(kumu_url, headers=headers, json=element)
        if response.status_code != 200:
            print(f"Failed to create element for {element['name']}: {response.text}")
        else:
            print(f"Created element: {element['name']}")

# Main function to fetch Slack users, download images, upload them to Kumu, and create elements
def main():
    # Fetch users from Slack
    slack_users = fetch_slack_users()
    print(f"Fetched {len(slack_users)} users from Slack.")
    
    # Format users for Kumu
    kumu_data = format_for_kumu(slack_users)
    print(f"Formatted {len(kumu_data)} users for Kumu.")
    
    # Create elements in Kumu.io
    create_kumu_elements(kumu_data)

if __name__ == "__main__":
    main()
