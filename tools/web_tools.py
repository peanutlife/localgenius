# tools/web_tools.py

import json
import subprocess
import tempfile
from urllib.parse import urlparse

def fetch_url(url, method="GET", headers=None, data=None):
    """
    Fetch content from a URL using curl.

    Args:
        url (str): The URL to fetch
        method (str, optional): HTTP method (GET, POST, etc.). Defaults to "GET".
        headers (dict, optional): HTTP headers to include. Defaults to None.
        data (str, optional): Data to send with the request. Defaults to None.

    Returns:
        dict: A dictionary containing response status, headers, and body
    """
    cmd = ["curl", "-s", "-i", "-X", method]

    # Add headers if provided
    if headers:
        for key, value in headers.items():
            cmd.extend(["-H", f"{key}: {value}"])

    # Add data if provided
    if data:
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp:
            temp.write(data)
            temp.flush()
            cmd.extend(["--data-binary", f"@{temp.name}"])

    # Add URL and execute
    cmd.append(url)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        output = result.stdout

        # Parse response
        headers_end = output.find("\r\n\r\n")
        if headers_end == -1:
            # Try Unix-style line endings
            headers_end = output.find("\n\n")
            header_text = output[:headers_end].strip()
            body = output[headers_end+2:].strip()
        else:
            header_text = output[:headers_end].strip()
            body = output[headers_end+4:].strip()

        # Parse status line
        status_line = header_text.split("\n")[0]
        status_parts = status_line.split(" ", 2)
        if len(status_parts) >= 3:
            status_code = int(status_parts[1])
            status_message = status_parts[2]
        else:
            status_code = 0
            status_message = "Unknown"

        # Parse headers
        header_lines = header_text.split("\n")[1:]
        headers = {}
        for line in header_lines:
            if ":" in line:
                key, value = line.split(":", 1)
                headers[key.strip()] = value.strip()

        return {
            "status": {
                "code": status_code,
                "message": status_message
            },
            "headers": headers,
            "body": body
        }
    except Exception as e:
        return {
            "error": str(e)
        }

def download_file(url, output_path):
    """
    Download a file from a URL to a specified path.

    Args:
        url (str): The URL to download from
        output_path (str): The local path to save the file

    Returns:
        dict: A dictionary containing status and file info
    """
    try:
        cmd = ["curl", "-s", "-L", "-o", output_path, url]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            return {
                "success": False,
                "error": result.stderr
            }

        # Get file size
        file_info_cmd = ["ls", "-l", output_path]
        file_info = subprocess.run(file_info_cmd, capture_output=True, text=True)

        return {
            "success": True,
            "path": output_path,
            "url": url,
            "file_info": file_info.stdout.strip() if file_info.returncode == 0 else "Unknown"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def scrape_page(url, selector=None):
    """
    Scrape content from a webpage using curl and optional CSS selector.

    Args:
        url (str): The URL to scrape
        selector (str, optional): CSS selector to extract specific content.
                                 If None, returns the full page.

    Returns:
        dict: A dictionary containing the scraped content
    """
    # First, fetch the page
    response = fetch_url(url)

    if "error" in response:
        return {
            "success": False,
            "error": response["error"]
        }

    html_content = response["body"]

    # If no selector is provided, return the full HTML
    if not selector:
        return {
            "success": True,
            "content": html_content
        }

    # For selector-based extraction, use grep and sed for simple cases
    # This is a basic implementation and won't work for complex selectors
    try:
        # Create a temporary file with the HTML content
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp:
            temp.write(html_content)
            temp.flush()

            # Use grep to find the selector, very basic implementation
            # Note: This is not a proper HTML parser and will only work for simple cases
            grep_cmd = ["grep", "-A", "10", "-B", "10", selector, temp.name]
            grep_result = subprocess.run(grep_cmd, capture_output=True, text=True)

            extracted = grep_result.stdout.strip()

            return {
                "success": True,
                "content": extracted if extracted else "No content found matching the selector"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def validate_url(url):
    """
    Validate if a string is a properly formatted URL.

    Args:
        url (str): The URL to validate

    Returns:
        dict: A dictionary with validation results
    """
    try:
        result = urlparse(url)
        valid = all([result.scheme, result.netloc])

        return {
            "valid": valid,
            "parsed": {
                "scheme": result.scheme,
                "netloc": result.netloc,
                "path": result.path,
                "params": result.params,
                "query": result.query,
                "fragment": result.fragment
            } if valid else {}
        }
    except Exception as e:
        return {
            "valid": False,
            "error": str(e)
        }

def register_web_tools(registry):
    """Register all web tools with the given registry."""
    registry.register(
        "fetch_url",
        fetch_url,
        "Fetch content from a URL with optional method, headers, and data"
    )

    registry.register(
        "download_file",
        download_file,
        "Download a file from a URL to a specified local path"
    )

    registry.register(
        "scrape_page",
        scrape_page,
        "Scrape content from a webpage, optionally with a selector"
    )

    registry.register(
        "validate_url",
        validate_url,
        "Validate if a string is a properly formatted URL"
    )

    return registry
