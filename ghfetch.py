import colorsys
import hashlib
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


# adapted from https://github.com/joric/identicons
def get_identicon(id):
    h = hashlib.md5(str(id).encode("utf-8")).hexdigest()
    m = list(map(lambda c: int(c, 16), h))
    h, l, s = m[25] << 8 | m[26] << 4 | m[27], m[30] << 4 | m[31], m[28] << 4 | m[29]
    rgb = colorsys.hls_to_rgb(h / 16 / 256, (960 - l) / 5 / 256, (832 - s) / 5 / 256)
    c = tuple(map(lambda x: round(x * 255), rgb))
    grid = [
        [m[[2, 1, 0, 1, 2][y] * 5 + x] % 2 == 0 for y in range(5)] for x in range(5)
    ]
    return (c, grid)


def display_identicon(color, icon):
    print(f"\x1b[38;2;{color[0]};{color[1]};{color[2]}m")
    for row in icon:
        rowString = " "
        for i in range(0, 5):
            if row[i]:
                rowString += "\u2588"
            else:
                rowString += " "
        print(rowString)
    print("\x1b[0m")


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
    color, icon = get_identicon(user_info["id"])
    display_identicon(color, icon)

    if user_info is not None:
        for item, desc in display_elements:
            if item in user_info:
                print(f"{desc}: {user_info[item]}")
