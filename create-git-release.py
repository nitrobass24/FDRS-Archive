import requests
import os
import base64

# Constants
GITHUB_API = "https://api.github.com"
TOKEN = ""  # Replace with your GitHub token
REPO_OWNER = "nitrobass24"         # Replace with your username or organization
REPO_NAME = "FDRS-Archive"           # Replace with your repository name
DIRECTORY_PATH = "./releases/"  # Directory containing the binaries

# Headers for authorization
headers = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def create_release(tag, release_name):
    url = f"{GITHUB_API}/repos/{REPO_OWNER}/{REPO_NAME}/releases"
    payload = {
        "tag_name": tag,
        "name": release_name,
        "body": f"Release for version {release_name}",
        "draft": False,
        "prerelease": False
    }
    response = requests.post(url, json=payload, headers=headers)
    response_data = response.json()
    print(response_data)  # Print the response for debugging
    upload_url = response_data['upload_url'].split('{')[0]  # Removing the {?name,label} part
    return response_data, upload_url

def upload_asset(upload_url, release_id, file_path):
    params = {"name": os.path.basename(file_path)}
    local_headers = headers.copy()
    local_headers["Content-Type"] = "application/octet-stream"
    with open(file_path, 'rb') as f:
        response = requests.post(upload_url, headers=local_headers, params=params, data=f)
        print(response.text)  # Print the raw response for debugging
    return response.json()

def check_release_exists(tag):
    url = f"{GITHUB_API}/repos/{REPO_OWNER}/{REPO_NAME}/releases/tags/{tag}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return True, response.json()['upload_url'].split('{')[0], response.json()['id']
    return False, None, None

def update_readme(file_name, release_info):
    # Step 1: Fetch the current README content
    readme_url = f"{GITHUB_API}/repos/{REPO_OWNER}/{REPO_NAME}/contents/README.md"
    response = requests.get(readme_url, headers=headers)
    readme_data = response.json()
    current_content = base64.b64decode(readme_data['content']).decode('utf-8')
    
    # Step 2: Update the README content
    release_name = release_info['name']
    release_url = release_info['html_url']
    new_content = f"\n## {release_name}\n[Download {file_name}]({release_url})\n"
    updated_content = current_content + new_content

    # Step 3: Push the updated content back to GitHub
    update_payload = {
        "message": f"Update README for {release_name}",
        "content": base64.b64encode(updated_content.encode('utf-8')).decode('utf-8'),
        "sha": readme_data['sha']
    }
    update_response = requests.put(readme_url, json=update_payload, headers=headers)
    print(f"README update response: {update_response.json()}")

def parse_version(filename):
    # Extract version number from filename like 'FDRS_1.2.3.exe'
    version_str = filename.replace('FDRS_', '').replace('.exe', '')
    return tuple(map(int, version_str.split('.')))

def sort_files_by_version(files):
    return sorted(files, key=parse_version, reverse=True)

def process_directory(directory_path):
    def parse_version(filename):
        # Extract version number from filename like 'FDRS_1.2.3.exe'
        version_str = filename.replace('FDRS_', '').replace('.exe', '')
        return tuple(map(int, version_str.split('.')))

    def sort_files_by_version(files):
        return sorted(files, key=parse_version, reverse=True)

    files = [f for f in os.listdir(directory_path) if f.endswith(".exe") and "FDRS_" in f]
    sorted_files = sort_files_by_version(files)

    for file_name in sorted_files:
        version = file_name.replace("FDRS_", "").replace(".exe", "")
        tag = f"v{version}"
        release_name = f"Version {version}"

        print(f"Processing {file_name}")

        # Check if release already exists
        exists, upload_url, release_id = check_release_exists(tag)
        if exists:
            print(f"Release already exists for {tag}. Skipping creation.")
            continue
        else:
            release_info, upload_url = create_release(tag, release_name)
            if 'upload_url' not in release_info:
                print(f"Failed to create release for {tag}: {release_info}")
                continue

        release_id = release_info['id']

        # Upload the binary file as an asset to the release
        file_path = os.path.join(directory_path, file_name)
        upload_response = upload_asset(upload_url, release_id, file_path)
        print(f"Uploaded {file_name}: {upload_response}")

        # Update the README file
        if 'id' in release_info:  # Ensure release_info is valid
            update_readme(file_name, release_info)
            print(f"Updated README for {file_name}")

# Run the process
process_directory(DIRECTORY_PATH)

