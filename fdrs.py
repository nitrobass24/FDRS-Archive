import requests

def download_file(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Will raise an HTTPError if the HTTP request returned an unsuccessful status code
        with open(url.split('/')[-1], 'wb') as f:
            f.write(response.content)
        print(f"Downloaded {url}")
    except requests.HTTPError:
        print(f"Failed to download {url}")

def main():
    base_url = "https://www.fordservicecontent.com/Ford_Content/IDS/FDRS/"
    for major in range(34, 39):
        for minor in range(0, 10):
            for patch in range(0, 10):
                if major == 38 and minor > 5: break
                if major == 38 and minor == 5 and patch > 7: break
                file_name = f"FDRS_{major}.{minor}.{patch}.exe"
                download_file(base_url + file_name)

if __name__ == "__main__":
    main()

