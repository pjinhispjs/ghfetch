#!/bin/env python3
import colorsys
import hashlib
import sys

import requests

display_elements = [
    # ("login", "Username"),
    # ("name", "Name"),
    ("bio", "Bio"),
    ("company", "Company"),
    ("location", "Location"),
    ("blog", "Website"),
    ("public_repos", "Respositories"),
    ("followers", "Follows"),
    ("following", "Following"),
]

# ascii scaling values
hScale = 4
vScale = int(hScale / 2)


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
    ascii_art = ""
    for row in icon:
        rowString = " "
        for i in range(0, 5):
            if row[i]:
                rowString += "\u2588" * hScale
            else:
                rowString += " " * hScale
        ascii_art += (rowString + " \n") * vScale
    return ascii_art


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


def get_displayed_name(user_info):
    nl = []
    name = user_info["login"]
    if user_info["name"]:
        name = user_info["name"]
        if user_info["email"]:
            name += f" ({user_info["email"]})"
        nl.append(user_info["login"])
    nl.insert(0, name)
    return nl


def get_displayed_info(user_info):
    info_list = get_displayed_name(user_info)
    info_list.append("-" * max(len(s) for s in info_list))
    for item, desc in display_elements:
        if item in user_info:
            if user_info[item] is not None and user_info[item] != "":
                info_list.append(f"{desc}: {user_info[item]}")
    return info_list


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} username")
        sys.exit(1)

    username = sys.argv[1]
    user_info = get_user_info(username)
    if user_info is not None:
        color, icon = get_identicon(user_info["id"])
        ascii_art = display_identicon(color, icon).split("\n")
        info_list = get_displayed_info(user_info)

        for i in range(max(len(ascii_art), len(info_list))):
            if i < len(ascii_art) - 1:
                sys.stdout.write(f"\x1b[38;2;{color[0]};{color[1]};{color[2]}m")
                sys.stdout.write(ascii_art[i])
                sys.stdout.write("\x1b[0m")
            else:
                sys.stdout.write(" " * int(5 * hScale + 2))
            if i < len(info_list):
                if i == 0:
                    sys.stdout.write(f"\x1b[1m{info_list[i]}\x1b[0m")
                else:
                    sys.stdout.write(info_list[i])
            sys.stdout.write("\n")
