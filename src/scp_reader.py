# Native lib.
import os
import sys
import re
import shutil
import textwrap
import argparse
import threading
import multiprocessing
from random import randint
from time import sleep, time

# 3rd Party lib.
import requests
from bs4 import BeautifulSoup
import pyttsx3
import keyboard


DESTINATION = r""
HEADERINFO = {}

LINE_WIDTH = 90  # Affects text wrapping & '=' text seperators
# INDENTATION = 0  # Has no effect when CENTRED_TEXT is True
CENTRED_TEXT = True

MAX_SCP_NUMBER = 7999


def main():
    args = parse_args()

    # Will atempt to read from existing .txt if URL is None
    URL = fetch_url(args)

    if URL:
        html_content = get_html_content(URL)

    if html_content:
        soup = BeautifulSoup(html_content, "html.parser")  # Parse HTML content

        if check_contents(soup):
            soup = soup.find("div", id="page-content")  # Look only at SCP entry
            formatted_text = "".join(format_text(soup))
            output_text = wrap_lines(
                formatted_text
            )  # Pretty print for readibility

            if not args.audio:
                print(auto_indent(output_text))

            if args.show_url:
                show_url(URL, args)

            if args.text:
                print(f"{auto_indent('=' * (LINE_WIDTH))}")
                download_page(
                    formatted_text
                )  # Less awk. pauses for text to speech
                print(f"{auto_indent('=' * (LINE_WIDTH))}\n")

            if args.audio or args.audio_text:
                text_to_speech(formatted_text)

        else:
            print(f"\n! Error: Page has no contents\n")


def parse_args():
    parser = argparse.ArgumentParser(
        description="CLI Browser for SCP Wiki Entries"
    )
    parser.add_argument(
        "number",
        nargs="?",  # Optional positional arg.
        type=int,
        help=f"The SCP number to extract. (001 - {MAX_SCP_NUMBER})",
    )
    parser.add_argument(
        "-d",
        "--destination",
        action="store_true",
        help="Open DESTINATION folder (where downloaded text files are kept)",
    )
    parser.add_argument(
        "-a",
        "--audio",
        action="store_true",
        help="Computer reads the file for you (no accompanying SCP entry text)",
    )
    parser.add_argument(
        "-at",
        "--audio_text",
        action="store_true",
        help="Computer reads the file for you & shows you the SCP entry text",
    )
    parser.add_argument(
        "-t",
        "--text",
        action="store_false",
        help="Don't save the retrieved page as a .txt file; won't save the page if the .txt file already exists",
    )
    parser.add_argument(
        "-r",
        "--random",
        action="store_true",
        help="Retrieve a random SCP page number",
    )
    parser.add_argument(
        "-g",
        "--get-all",
        action="store_true",
        help="Download all SCP pages & save as .txt files",
    )
    parser.add_argument(
        "-o",
        "--overwrite",
        action="store_true",
        help="Download the .txt file if it already exists",
    )
    parser.add_argument(
        "-u",
        "--show-url",
        action="store_false",
        help="Don't show the SCP Wiki URL for the entry",
    )

    args = parser.parse_args()

    if args.destination:
        check_DESTINATION_exists()

        if os.name == "posix":  # Unix/Linux/MacOS
            os.system(f'open "{DESTINATION}"')
        elif os.name == "nt":  # Windows
            os.system(f'explorer "{DESTINATION}"')
        else:
            print(f"\nUnsupported operating system\n")
            sys.exit(1)
        sys.exit(0)

    if args.random and args.number is not None:
        print(
            f"\n! Error: pass -r/--random or a specific SCP number, but not both.\n"
        )
        sys.exit(1)

    if args.get_all:
        count = download_all_pages()
        print(
            f"\nDownloaded all SCP entries:\n\t{count} files saved to\n\t{DESTINATION}\n"
        )
        sys.exit(0)

    if args.random:
        args.number = randint(1, MAX_SCP_NUMBER)

    return args


def download_all_pages():
    check_DESTINATION_exists()

    count = 0
    print(f"\nAttempting download of all entries...\n")

    try:
        print(f"{auto_indent('=' * (LINE_WIDTH))}")

        for number in range(1, MAX_SCP_NUMBER, 1):
            url = make_url(number)

            if url:
                html_content = get_html_content(url)

                if html_content:
                    soup = BeautifulSoup(html_content, "html.parser")
                    if check_contents(soup):
                        soup = soup.find("div", id="page-content")
                        formatted_text = "".join(format_text(soup))
                        # output_text = wrap_lines(formatted_text)
                        count = download_page(formatted_text)
                        sleep(randint(5, 15))  # Please don't hammer the site
            else:
                continue

        print(f"{auto_indent('=' * (LINE_WIDTH))}\n")

    except Exception as e:
        print(f"\n! Error downloading all pages: {e}\n")
    return count


def pad_number(number):
    if number < 100:
        return f"{number:03d}"
    else:
        return number


def fetch_url(args):
    if args.number:
        number = int(args.number)
    else:
        print(f"\n! Error generating URL")
        sys.exit(1)

    if check_number(int(number)) and not args.overwrite:
        show_text_file(pad_number(int(number)), args)
        return None

    return make_url(number)


def make_url(number):
    return f"https://scp-wiki.wikidot.com/scp-{pad_number(int(number))}"


def check_number(number):
    check_DESTINATION_exists()

    filenames = os.listdir(DESTINATION)
    number_set = {extract_number(filename) for filename in filenames}

    return number in number_set


def check_DESTINATION_exists():
    if not os.path.exists(DESTINATION):
        raise ValueError(
            f"! Error: Cannot find DESTINATION folder at {DESTINATION}"
        )
        sys.exit(1)
    return


def check_contents(soup):
    text_to_find = "This page doesn't exist."
    span_tag = soup.find("span", string=text_to_find)
    if span_tag:  # If text is found
        print("= Skipped: No contents found")
        return False

    return True  # Page contents found


def get_html_content(url):
    response = requests.get(url, headers=HEADERINFO)
    if response.status_code == 200:
        return response.text
    elif response.status_code == 404:
        print(f"\n! Page not found (possibly no contents)\n")
    else:
        print(
            f"\n! Failed to fetch content from {url}: {response.status_code}\n"
        )
        return None


def download_page(contents, count=0):
    check_DESTINATION_exists()

    scp_number = extract_number(contents)

    if scp_number:
        scp_number = pad_number(scp_number)
        scp_filename = f"SCP-{scp_number}.txt"
    else:
        raise ValueError(f"\n! Error: Couldn't get SCP number from output text")
        scp_filename = "UNKNOWN SCP NUMBER.txt"

        counter = 1
        while os.path.exists(os.path.join(DESTINATION, scp_filename)):
            counter += 1
            scp_filename = f"{scp_filename} - {counter:0{len(MAX_SCP_NUMBER)}d}"

    try:
        with open(
            os.path.join(DESTINATION, scp_filename), "w", encoding="utf-8"
        ) as f:
            f.write(contents)
        print(auto_indent(f"+ Saved {scp_filename} to {DESTINATION}"))
        count += 1
    except Exception as e:
        print(f"\n! Error downloading: {e}\n")

    return count


def extract_number(input_string):
    pattern = re.compile(r"SCP-(\d+)", re.IGNORECASE)
    matches = pattern.findall(input_string)
    return int(matches[0]) if matches else None


def show_text_file(number, args):
    scp_filename = f"SCP-{number}.txt"
    with open(
        os.path.join(DESTINATION, scp_filename), "r", encoding="utf-8"
    ) as f:
        contents = f.read()

    if not args.audio:
        print_contents = auto_indent(wrap_lines(contents))
        print(print_contents)

    if args.show_url:
        show_url(make_url(int(number)), args)

    if args.audio or args.audio_text:
        text_to_speech(contents)

    sys.exit(0)


def show_url(URL, args):
    if not args.audio:
        print(f"{auto_indent(f'Entry source: {URL}')}\n")
    else:
        print(f"\nEntry source: {URL}\n")


def format_text(soup):
    formatted_text_parts = []
    blockquote_content = []
    box_content = []
    omit_set = set()
    blockquote_count = 0

    footnotes = {}

    for tag in soup.find_all(["blockquote", "p", "img", "div"]):
        if tag.find_parents(
            "div",
            class_=["licensebox", "page-rate-widget-box", "authorlink-wrapper"],
        ):
            continue
        if tag.find_parents("span", class_="printuser avatarhover"):
            continue

        if tag.name == "blockquote":
            blockquote_count += 1

            if blockquote_count == 1:
                formatted_text_parts.append(f"\n")
                for child in tag.find_all("p"):
                    formatted_child_text = format_paragraph(child)
                    if formatted_child_text.strip() not in omit_set:
                        blockquote_content.append(formatted_child_text)
                        omit_set.add(formatted_child_text.strip())
                blockquote_count += 1

            if blockquote_count == 2:
                blockquote_content_str = "\n".join(blockquote_content)
                wrapped_blockquote = wrap_lines(blockquote_content_str, 84)
                formatted_text_parts.append(
                    create_ascii_frame(wrapped_blockquote)
                )
                formatted_text_parts.append(f"\n")
                blockquote_content = []
                blockquote_count = 0

        elif tag.name == "img" and "image" in tag.get("class", []):
            image_info = extract_image_info(tag)
            if image_info:
                formatted_text_parts.append(image_info)
                omit_set.add(image_info)

        elif tag.name == "div" and any(
            "anom-bar" in class_name for class_name in tag.get("class", [])
        ):
            box_div = tag
            box_content = []

            for child_tag in box_div.find_all(recursive=False):
                child_text = child_tag.get_text(separator=" ").strip()
                if child_text:
                    box_content.append(child_text)

            div_text = " ".join(box_content)
            div_text = re.sub(r"\s{2,}", " ", div_text).strip()

            if div_text and div_text not in omit_set:
                formatted_text_parts.append(f"\n{div_text}\n")
                omit_set.add(div_text)

        elif tag.name == "div" and "footnotes-footer" in tag.get("class", []):
            formatted_text_parts.append(f"\n**Footnotes**\n")
            for footnote in tag.find_all("div", class_="footnote-footer"):
                formatted_text_parts.append(format_paragraph(footnote))

        else:
            if tag.name == "div":
                continue
            else:
                formatted_tag_text = format_paragraph(tag)
                if formatted_tag_text.strip() not in omit_set:
                    formatted_text_parts.append(formatted_tag_text)

    return formatted_text_parts


def format_paragraph(tag):
    tag_html = str(tag)  # Convert from bs4.element.Tag to str.

    replacements = {
        "&nbsp;": " ",
        "\xa0": " ",
        "¦": "|",
        "—": "--",
        "<em>": "*",
        "</em>": "*",
    }

    for old, new in replacements.items():
        tag_html = tag_html.replace(old, new)

    soup = BeautifulSoup(tag_html, "html.parser")  # Incl. changes made to HTML

    for footnote in soup.find_all("sup", class_="footnoteref"):
        a_tag = footnote.find("a")
        if a_tag:
            footnote_id = (
                a_tag.text
            )  # Using .get_text created inconsist. space issues
            a_tag.string = f"^[{footnote_id}]"

    tag_text = soup.text
    if not tag_text.strip():
        return ""

    return f"\n{tag_text}\n"


def extract_image_info(tag):
    image_src = tag.get("src", "")
    image_alt = tag.get("alt", "")

    if image_src:
        try:
            return f"\nIMAGE: ![{image_alt}]({image_src})\n"
        except Exception as e:
            print(f"! Error with image info.: {e}")
            return None


def wrap_lines(formatted_text, max_length=LINE_WIDTH):
    wrapped_lines = []
    for line in formatted_text.splitlines():
        if len(line) > max_length:
            wrapped_lines.extend(textwrap.wrap(line, width=max_length))
        else:
            wrapped_lines.append(line)
    # Add a newline only if the last line is not empty; mostly for ascii frames
    if wrapped_lines and not wrapped_lines[-1].isspace():
        wrapped_lines.append("")
    return "\n".join(wrapped_lines)


def auto_indent(text):
    if CENTRED_TEXT:
        terminal_width = shutil.get_terminal_size().columns
        return textwrap.indent(text, " " * ((terminal_width - LINE_WIDTH) // 2))

    return textwrap.indent(text, " " * INDENTATION)


def create_ascii_frame(content, padding=2):
    lines = content.split("\n")
    max_length = max(len(line) for line in lines)

    frame_edge = "+" + "-" * (max_length + 2 * padding) + "+"

    frame_middle = "\n".join(
        f'|{" " * padding}{line.ljust(max_length, " ")}{" " * padding}|'
        for line in lines
    )

    return f"{frame_edge}\n{frame_middle}\n{frame_edge}"


def text_to_speech(text, rate=175, voice_id=1):
    stop_event = (
        threading.Event()
    )  # Create an event to signal spinner thread to stop

    # Both multipro. & threading for interruptibility & to limit mem. use (respectively)
    speech = multiprocessing.Process(
        target=speak_text, args=(text, rate, voice_id)
    )
    spinner_thread = threading.Thread(target=spinner, args=(stop_event,))

    speech.start()
    spinner_thread.start()

    while speech.is_alive():
        if keyboard.is_pressed("q"):
            speech.terminate()
        else:
            sleep(
                0.2
            )  # Less CPU intensive; replace w/ continue for immed. response

    speech.join()  # Wait for the text-to-speech thread to finish
    stop_event.set()  # Set the event to stop the spinner
    spinner_thread.join()  # Gracefully finish spinner thread
    print(f"\nEnd of Audio\n")


def speak_text(text, rate, voice_id):
    engine = pyttsx3.init()
    engine.setProperty("rate", rate)

    if voice_id:
        voices = engine.getProperty("voices")
        engine.setProperty("voice", voices[voice_id].id)

    engine.say(text)
    engine.runAndWait()


def spinner(stop_event):
    while not stop_event.is_set():
        for char in "-\\|/":  # Simple spinner animation
            print(
                f"\r{char} Reading entry ('q' to quit)...", end="", flush=True
            )
            sleep(0.2)  # Slower speed to evoke tape turning


if __name__ == "__main__":
    main()
