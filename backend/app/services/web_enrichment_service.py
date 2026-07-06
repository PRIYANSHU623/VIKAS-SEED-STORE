import os
import json
import re
import requests
from typing import Dict, Any, List
from google import genai

TRUSTED_DOMAINS = [
    "bayer", "syngenta", "iffco", "upl-ltd", "godrejagrovet", "fmc", "corteva", "pioneer", "adama", "kribhco", "indofil",
    "gov.in", "gov", "edu", "icar.org.in", "kvk.icar.gov.in", "agricoop.nic.in", "dacfw.nic.in",
    "krishijagran", "agrowex", "agribusiness", "fertilizer-brochure", "catalog", "pdf", "brochure"
]

ENRICHMENT_PROMPT = """
You are an expert agricultural researcher.
We are onboarding a product but some details are missing or have low confidence from image scanning.
We ran an internet search on trusted sources for this product.

Search results:
{search_results}

Initial scanned product details:
{initial_details}

Fields that need enrichment:
{missing_fields}

For each field that needs enrichment, attempt to extract its true value from the trusted search results.
Rules:
- NEVER use random blogs, forum posts (like Quora, Reddit), or unverified user content. Only use manufacturer sites, government databases, official product brochures, and trusted agricultural distributors.
- If the search results do not contain high-confidence information for a field from a trusted source, do NOT make it up. Leave the value as null and confidence as 0.
- For each enriched field, provide:
  1. `value`: The enriched value (string or number/float for MRP).
  2. `confidence`: An integer percentage (0 to 100) representing your confidence based on the source's authority (e.g. 90-95% for official manufacturer sites, 80-85% for trusted distributors, 0% if not found).
  3. `source`: The name of the website or URL where you found the information (e.g. "Bayer CropScience Official Website" or "IFFCO Product Catalog").

Return ONLY a valid JSON object mapping each missing field to its enriched structure, like this:
{{
  "field_name_1": {{"value": "value", "confidence": 92, "source": "Official Manufacturer Website"}},
  "field_name_2": {{"value": null, "confidence": 0, "source": "Not Found"}}
}}
Do not write markdown backticks or any commentary. Return ONLY the raw JSON.
"""

def search_duckduckgo(query: str) -> List[Dict[str, str]]:
    """
    Performs a DuckDuckGo HTML search and returns search results (title, snippet, url).
    """
    url = "https://html.duckduckgo.com/html/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    results = []
    try:
        response = requests.post(url, data={"q": query}, headers=headers, timeout=10.0)
        if response.status_code == 200:
            html = response.text
            
            # Extract links, titles, snippets
            # DuckDuckGo HTML structure has result items with classes result__snippet and result__url
            raw_snippets = re.findall(r'<a class="result__snippet[^>]*>(.*?)</a>', html, re.DOTALL)
            raw_links = re.findall(r'<a class="result__url[^>]* href="([^"]+)"', html, re.DOTALL)
            raw_titles = re.findall(r'<a class="result__url[^>]*>(.*?)</a>', html, re.DOTALL)

            for i in range(min(len(raw_snippets), len(raw_links), len(raw_titles))):
                snip = raw_snippets[i]
                link = raw_links[i]
                title = raw_titles[i]

                # Decode HTML entities and clean tags
                clean_snip = re.sub(r'<[^>]+>', '', snip)
                clean_snip = clean_snip.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&quot;', '"').replace('&apos;', "'").replace('&#x27;', "'")
                
                clean_title = re.sub(r'<[^>]+>', '', title)
                clean_title = clean_title.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&quot;', '"').replace('&apos;', "'").replace('&#x27;', "'")

                # Clean URL redirect in DuckDuckGo HTML if it starts with /l/?kh=...
                # e.g., //duckduckgo.com/l/?kh=-1&uddg=https%3A%2F%2F...
                url_match = re.search(r'uddg=([^&]+)', link)
                clean_url = requests.utils.unquote(url_match.group(1)) if url_match else link

                results.append({
                    "title": clean_title.strip(),
                    "snippet": clean_snip.strip(),
                    "url": clean_url.strip()
                })
    except Exception as e:
        print(f"Error searching DuckDuckGo: {e}")
    return results

def is_trusted_source(url: str, title: str, snippet: str) -> bool:
    """
    Checks if a search result is from a trusted domain or mentions trusted entities.
    """
    combined = (url + " " + title + " " + snippet).lower()
    # If the domain matches any trusted domain keywords
    for domain in TRUSTED_DOMAINS:
        if domain in combined:
            return True
    return False

def enrich_missing_fields(
    product_name: str, 
    brand: str, 
    category: str, 
    missing_fields: List[str], 
    initial_details: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Searches the web for missing fields and uses Gemini to extract details from trusted results.
    """
    if not missing_fields:
        return {}

    # Perform a search for the product
    search_query = f"{brand} {product_name} {category} brochure catalog specifications pdf"
    print(f"Searching web for: '{search_query}' to enrich {missing_fields}...")
    
    raw_results = search_duckduckgo(search_query)
    
    # Filter for trusted sources
    trusted_results = []
    for res in raw_results:
        if is_trusted_source(res["url"], res["title"], res["snippet"]):
            trusted_results.append(res)
    
    # If we have no trusted results, fallback to using the first few DDG results but tell Gemini to be very critical
    if not trusted_results:
        print("No matches for highly-trusted list. Using general results but advising strict validation...")
        trusted_results = raw_results[:5]
    else:
        print(f"Found {len(trusted_results)} trusted search results.")
        trusted_results = trusted_results[:6]

    if not trusted_results:
        print("No search results found.")
        return {}

    # Format search results for Gemini
    search_context = ""
    for idx, res in enumerate(trusted_results):
        search_context += f"Result #{idx+1}:\nTitle: {res['title']}\nURL: {res['url']}\nSnippet: {res['snippet']}\n\n"

    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return {}
        client = genai.Client(api_key=api_key)

        prompt = ENRICHMENT_PROMPT.format(
            search_results=search_context,
            initial_details=json.dumps(initial_details, indent=2),
            missing_fields=", ".join(missing_fields)
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1
            )
        )

        text = response.text.strip()
        if text.startswith("```json"):
            text = text.replace("```json", "").replace("```", "").strip()
        elif text.startswith("```"):
            text = text.replace("```", "").strip()

        enriched_data = json.loads(text)
        print(f"Web Enrichment returned: {enriched_data}")
        return enriched_data

    except Exception as e:
        print(f"Error during Web Enrichment: {e}")
        return {}


def search_web_product_images(product_name: str, brand: str) -> List[str]:
    """
    Searches Bing Images for the product and returns a list of candidate web image URLs.
    """
    query = f"{brand} {product_name} agricultural product"
    url = f"https://www.bing.com/images/search?q={requests.utils.quote(query)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=8.0)
        if response.status_code != 200:
            return []
        
        # Extract murl values
        murls = re.findall(r'murl&quot;:&quot;([^&]+?)&quot;', response.text)
        
        # Filter for valid web image links
        valid_urls = []
        for link in murls:
            # Decode URL
            link = requests.utils.unquote(link)
            if link.startswith("http") and any(link.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp"]):
                if link not in valid_urls:
                    valid_urls.append(link)
        
        if not valid_urls:
            return []
            
        # Use Gemini to filter and select the 4 most relevant image URLs
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return valid_urls[:4]
            
        from google.genai import types
        client = genai.Client(api_key=api_key)
        
        prompt = f"""
        We searched the web for images of the agricultural product: "{brand} {product_name}".
        Here are the image URLs we found:
        {json.dumps(valid_urls[:15], indent=2)}
        
        Select the top 4 cleanest and most relevant image URLs that are likely to represent this product packaging or bottle/bag.
        Exclude irrelevant images (like cliparts, general scenery, unrelated events).
        Return ONLY a valid JSON list of strings, e.g. ["url1", "url2", "url3", "url4"].
        Do not write markdown backticks or any commentary.
        """
        
        res = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1
            )
        )
        
        text = res.text.strip()
        if text.startswith("```json"):
            text = text.replace("```json", "").replace("```", "").strip()
        elif text.startswith("```"):
            text = text.replace("```", "").strip()
            
        selected = json.loads(text)
        if isinstance(selected, list):
            return [u for u in selected if u in valid_urls]
        return valid_urls[:4]
    except Exception as e:
        print(f"Error searching web product images: {e}")
        return []

