#!/bin/env python3
import colorsys
import hashlib
import re
import sys

import requests

# ascii scaling values
hScale = 4
vScale = int(hScale / 2)


def visible_len(text):
    color_pattern = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")
    return len(color_pattern.sub("", text))


def get_user_repos(username):
    url = f"https://api.github.com/users/{username}/repos"
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2026-03-10",
    }
    all_repos = []
    page = 1
    while True:
        # GitHub's max per_page is 100
        params = {"per_page": 100, "page": page}
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            repos = response.json()
            if not repos:
                break
            all_repos.extend(repos)
            if "Link" in response.headers:
                if 'rel="next"' not in response.headers["Link"]:
                    break
            else:
                break
            page += 1
        else:
            print(f"Failed to retrieve repositories for {username}.")
            print(f"Status code: {response.status_code}")
            return None
    return all_repos


def get_repo_languages(owner, repo_name):
    url = f"https://api.github.com/repos/{owner}/{repo_name}/languages"
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2026-03-10",
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    print(f"Failed to retrieve languages for {owner}/{repo_name}.")
    print(f"Status code: {response.status_code}")
    return {}


def get_top_languages_with_percentage(username, top_n=5):
    all_repos = get_user_repos(username)
    if not all_repos:
        return []

    language_bytes = {}
    for repo in all_repos:
        owner = repo["owner"]["login"]
        repo_name = repo["name"]
        languages = get_repo_languages(owner, repo_name)
        for lang, bytes_count in languages.items():
            language_bytes[lang] = language_bytes.get(lang, 0) + bytes_count

    total_bytes = sum(language_bytes.values())
    if total_bytes == 0:
        return []

    language_percentages = {
        lang: (bytes_count / total_bytes) * 100
        for lang, bytes_count in language_bytes.items()
    }

    sorted_languages = sorted(
        language_percentages.items(), key=lambda item: item[1], reverse=True
    )

    return sorted_languages[:top_n]


def get_language_colors(languages):
    colors = {}
    num_languages = len(languages)
    if num_languages == 0:
        return colors

    for i, lang in enumerate(languages):
        hue = i / num_languages
        lightness = 0.5
        saturation = 0.7
        rgb_float = colorsys.hls_to_rgb(hue, lightness, saturation)
        rgb_int = tuple(int(x * 255) for x in rgb_float)
        colors[lang] = rgb_int
    return colors


def render_language_bar(top_languages, bar_width=50):
    if not top_languages:
        return "", []

    languages = [lang for lang, _ in top_languages]
    lang_colors = get_language_colors(languages)

    bar_string = ""
    legend_entries = []

    segment_widths = []
    total_percentage = sum(percent for _, percent in top_languages)

    scale_factor = 100 / total_percentage if total_percentage > 0 else 0

    for lang, percent in top_languages:
        scaled_percent = percent * scale_factor
        width = int(round((scaled_percent / 100) * bar_width))
        segment_widths.append((lang, width, lang_colors.get(lang, (255, 255, 255))))

    current_width = sum(w for _, w, _ in segment_widths)
    if current_width != bar_width:
        diff = bar_width - current_width
        for i in range(abs(diff)):
            idx_to_adjust = -1
            max_width_so_far = -1
            for j, (lang, width, color) in enumerate(segment_widths):
                if diff > 0:
                    if width > max_width_so_far:
                        max_width_so_far = width
                        idx_to_adjust = j
                else:
                    if width > 0 and width > max_width_so_far:
                        max_width_so_far = width
                        idx_to_adjust = j

            if idx_to_adjust != -1:
                lang, width, color = segment_widths[idx_to_adjust]
                segment_widths[idx_to_adjust] = (
                    lang,
                    width + (1 if diff > 0 else -1),
                    color,
                )

    for lang, width, rgb in segment_widths:
        r, g, b = rgb
        bar_string += f"\x1b[38;2;{r};{g};{b}m{'\u2582' * width}\x1b[0m"

    for lang, percent in top_languages:
        r, g, b = lang_colors.get(lang, (255, 255, 255))
        legend_entries.append(
            f"\x1b[38;2;{r};{g};{b}m{'\u25cf'}\x1b[0m {lang} ({percent:.0f}%)"
        )

    return bar_string, legend_entries


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

    display_map = {
        "bio": "Bio",
        "company": "Company",
        "location": "Location",
        "blog": "Website",
        "public_repos": "Repositories",
        "followers": "Followers",
        "following": "Following",
    }

    for item, desc in display_map.items():
        if item in user_info and user_info[item] is not None and user_info[item] != "":
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

        top_languages = get_top_languages_with_percentage(username)
        bar_width = 50
        if top_languages:
            bar_string, legend_entries = render_language_bar(top_languages, bar_width)
            print(" " + bar_string)
            p = 0
            for lang in legend_entries:
                if (p + visible_len(lang) + 1) > bar_width:
                    sys.stdout.write("\n")
                    p = 0
                p += visible_len(lang) + 1
                sys.stdout.write(" " + lang)
            sys.stdout.write("\n")
