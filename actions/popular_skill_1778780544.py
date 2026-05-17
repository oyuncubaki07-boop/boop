import requests
from bs4 import BeautifulSoup

def run_action(params):
    """
    Fetches content from a URL and extracts data using CSS selectors.

    Args:
        params (dict): A dictionary containing:
            'url' (str): The URL to scrape.
            'selectors' (dict): A dictionary where keys are desired data fields
                                and values are CSS selectors.
                                Example: {"title": "h1", "paragraphs": "p", "links": "a.nav-link"}

    Returns:
        dict: A dictionary where keys are data fields and values are lists of
              extracted data. Each item in the list will be:
              - A string (text content) if the element is not an 'a' tag.
              - A dictionary {'text': '...', 'href': '...'} if the element is an 'a' tag.
              Returns {'error': '...'} on failure.
    """
    url = params.get('url')
    selectors = params.get('selectors', {})
    
    if not url:
        return {"error": "URL is missing in parameters."}
    if not selectors:
        return {"error": "Selectors are missing in parameters."}

    try:
        # User-Agent header to mimic a browser and avoid some basic blocks
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
    except requests.exceptions.Timeout:
        return {"error": f"Request timed out after 15 seconds for URL: {url}"}
    except requests.exceptions.TooManyRedirects:
        return {"error": f"Too many redirects for URL: {url}"}
    except requests.exceptions.HTTPError as e:
        return {"error": f"HTTP Error for URL {url}: {e.response.status_code} - {e.response.reason}"}
    except requests.exceptions.RequestException as e:
        return {"error": f"An unexpected error occurred while fetching URL {url}: {e}"}

    soup = BeautifulSoup(response.text, 'html.parser')
    results = {}

    for field, selector in selectors.items():
        found_elements = soup.select(selector)
        extracted_data = []
        for element in found_elements:
            if element.name == 'a' and element.has_attr('href'):
                # For 'a' tags, return both text and href
                extracted_data.append({
                    'text': element.get_text(strip=True),
                    'href': element['href']
                })
            else:
                # For other tags, just return the text content
                extracted_data.append(element.get_text(strip=True))
        results[field] = extracted_data
            
    return results