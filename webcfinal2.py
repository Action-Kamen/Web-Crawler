import requests
from bs4 import BeautifulSoup
import argparse
from urllib.parse import urlparse, urljoin
import os

# Global variables
visited_links = set()
output_format = {
    'html': set(),
    'css': set(),
    'js': set(),
    'jpg': set(),
    'png': set(),
    'gif': set(),
    'ico': set(),
    'other': set(),
    'external': set()
}
links_to_crawl = set()

def get_links(url, current_iteration, max_iterations, base_url, download_extension):
    """
    Extracts links and file URLs from a given URL.
    """
    if current_iteration > max_iterations:
        return

    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all the <a> tags and extract the href attribute
        links = soup.find_all('a')
        for link in links:
            href = link.get('href')
            if href:
                full_url = urljoin(url, href)
                parsed_link = urlparse(full_url)
                parsed_base_url = urlparse(base_url)

                # Check if the link belongs to the same domain
                if parsed_link.netloc == parsed_base_url.netloc:
                    if full_url not in visited_links:
                        visited_links.add(full_url)
                        if current_iteration < max_iterations:
                            links_to_crawl.add(full_url)
                        file_extension = full_url.rsplit('.', 1)[-1].lower()

                        # Categorize URLs based on their file extension
                        if file_extension == 'html':
                            output_format['html'].add(full_url)
                        elif file_extension == 'css':
                            output_format['css'].add(full_url)
                        elif file_extension == 'js':
                            output_format['js'].add(full_url)
                        elif file_extension == 'jpg':
                            output_format['jpg'].add(full_url)
                        elif file_extension == 'png':
                            output_format['png'].add(full_url)
                        elif file_extension == 'gif':
                            output_format['gif'].add(full_url)
                        elif file_extension == 'ico':
                            output_format['ico'].add(full_url)
                        else:
                            output_format['other'].add(full_url)

                        # Download the file if specified
                        if download_extension and file_extension == download_extension:
                            download_file(full_url, base_url, download_extension)
                else:
                    output_format['external'].add(full_url)

        # Find all the <link> tags and extract the href attribute
        css_links = soup.find_all('link', {'rel': 'stylesheet'})
        for css_link in css_links:
            href = css_link.get('href')
            if href:
                full_url = urljoin(url, href)
                if full_url not in visited_links:
                    visited_links.add(full_url)
                    output_format['css'].add(full_url)

        # Find all the <script> tags and extract the src attribute
        js_links = soup.find_all('script', {'src': True})
        for js_link in js_links:
            src = js_link.get('src')
            if src:
                full_url = urljoin(url, src)
                if full_url not in visited_links:
                    visited_links.add(full_url)
                    output_format['js'].add(full_url)

        # Find all the <img> tags and extract the src attribute
        img_links = soup.find_all('img')
        for img_link in img_links:
            src = img_link.get('src')
            if src:
                full_url = urljoin(url, src)
                parsed_link = urlparse(full_url)
                parsed_base_url = urlparse(base_url)

                # Check if the image URL belongs to the same domain
                if parsed_link.netloc == parsed_base_url.netloc:
                    if full_url not in visited_links:
                        visited_links.add(full_url)
                        file_extension = full_url.rsplit('.', 1)[-1].lower()

                        # Categorize image URLs based on their file extension
                        if file_extension == 'jpg':
                            output_format['jpg'].add(full_url)
                        elif file_extension == 'png':
                            output_format['png'].add(full_url)
                        elif file_extension == 'gif':
                            output_format['gif'].add(full_url)

                        # Download the file if specified
                        if download_extension and file_extension == download_extension:
                            download_file(full_url, base_url, download_extension)
                else:
                    output_format['external'].add(full_url)

        # Find all other file types
        other_links = soup.find_all(['link', 'script', 'img'])
        for other_link in other_links:
            href = other_link.get('href') or other_link.get('src')
            if href:
                full_url = urljoin(url, href)
                parsed_link = urlparse(full_url)
                parsed_base_url = urlparse(base_url)
                file_extension = full_url.rsplit('.', 1)[-1].lower()

                # Check if the file URL belongs to the same domain and is not a known file type
                if parsed_link.netloc == parsed_base_url.netloc and file_extension not in ['css', 'js', 'jpg', 'png', 'gif']:
                    if full_url not in visited_links:
                        visited_links.add(full_url)
                        if current_iteration < max_iterations:
                            links_to_crawl.add(full_url)

                        # Categorize other file URLs based on their file extension
                        if file_extension == 'ico':
                            output_format['ico'].add(full_url)
                        else:
                            output_format['other'].add(full_url)

                        # Download the file if specified
                        if download_extension and file_extension == download_extension:
                            download_file(full_url, base_url, download_extension)

    except requests.exceptions.RequestException:
        pass

def write_output(file_name=None, file_sizes=False, recursion_level=None):
    """
    Writes the output to a file or prints it to the console.
    """
    if file_name:
        with open(file_name, 'w') as file:
            if recursion_level:
                file.write(f"At recursion level {recursion_level}\n")
            file.write(f"Total files found: {sum(len(links) for links in output_format.values() if links)}\n\n")
            for file_type, links in output_format.items():
                if file_type != 'external':
                    file.write(f"{file_type.capitalize()}:\n")
                    for link in links:
                        file.write(f"{link}\n")
                    file.write('\n')
            file.write("External Links:\n")
            for link in output_format['external']:
                file.write(f"{link}\n")
            if file_sizes:
                file.write("\nFile Sizes:\n")
                for file_type, links in output_format.items():
                    if file_type != 'external':
                        file.write(f"{file_type.capitalize()}: {sum(get_file_size(link) for link in links)} bytes\n")
    else:
        if recursion_level:
            print(f"At recursion level {recursion_level}")
        print(f"Total files found: {sum(len(links) for links in output_format.values() if links)}")
        print()
        for file_type, links in output_format.items():
            if file_type != 'external':
                print(f"{file_type.capitalize()}:")
                for link in links:
                    print(link)
                print()
        print("External Links:")
        for link in output_format['external']:
            print(link)
        if file_sizes:
            print("\nFile Sizes:")
            for file_type, links in output_format.items():
                if file_type != 'external':
                    print(f"{file_type.capitalize()}: {sum(get_file_size(link) for link in links)} bytes")

def download_file(url, base_url, download_extension):
    """
    Downloads the file from the given URL.
    """
    try:
        response = requests.get(url, stream=True)
        file_name = os.path.basename(url)
        file_path = os.path.join(base_url, file_name)
        with open(file_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    file.write(chunk)
    except requests.exceptions.RequestException:
        pass

def get_file_size(url):
    """
    Returns the file size of the given URL.
    """
    try:
        response = requests.get(url, stream=True)
        return int(response.headers.get('content-length', 0))
    except requests.exceptions.RequestException:
        return 0

def crawl_website(base_url, max_iterations, download_extension=None, file_name=None, file_sizes=False):
    """
    Crawls a website starting from the base URL.
    """
    visited_links.add(base_url)
    links_to_crawl.add(base_url)
    current_iteration = 1

    while links_to_crawl:
        current_links = links_to_crawl.copy()
        links_to_crawl.clear()
        for link in current_links:
            get_links(link, current_iteration, max_iterations, base_url, download_extension)
        current_iteration += 1
        if current_iteration == max_iterations + 1:
            break

    write_output(file_name, file_sizes)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Web Crawler')
    parser.add_argument('-u', help='The URL to crawl')
    parser.add_argument('-t', '--max', type=int, default=1, help='Maximum recursion level (default: 1)')
    parser.add_argument('-D', '--extension', help='Download files with the specified extension')
    parser.add_argument('-o', '--output', help='Save the output to the specified file')
    parser.add_argument('-S', '--sizes', action='store_true', help='Include file sizes in the output')

    args = parser.parse_args()

    if not args.url.startswith('http://') and not args.url.startswith('https://'):
        args.url = 'http://' + args.url

    if args.extension and not args.extension.startswith('.'):
        args.extension = '.' + args.extension

    if args.max < 1:
        args.max = 1

    crawl_website(args.url, args.max, args.extension, args.output, args.sizes)
