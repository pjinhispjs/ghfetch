import sys

import requests

display_elements = [
    ("login", "Username"),
    ("name", "Name"),
    ("bio", "Bio"),
    ("public_repos", "Respositories"),
    ("followers", "Follows"),
    ("following", "Following"),
]


def get_user_info(username):
    url = f"https://api.github.com/users/{username}"
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2026-03-10",
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print("Failed to retrieve user info")
        return None


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} username")
        sys.exit(1)

    username = sys.argv[1]
    user_info = get_user_info(username)
    print(user_info)
    if user_info is not None:
        for item, desc in display_elements:
            if item in user_info:
                print(f"{desc}: {user_info[item]}")
