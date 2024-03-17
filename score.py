from selenium import webdriver
from selenium.webdriver.common.by import By
from urllib.parse import urlparse, urljoin
import os

def is_internal_link(base_url, link):
    """Check if the link is an internal link."""
    return urlparse(link).netloc == urlparse(base_url).netloc

def initialize_browser():
    # Initialize the WebDriver. Ensure chromedriver is in your PATH or specify its location.
    options = webdriver.ChromeOptions()
    # Add options like headless mode if needed
    options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)
    return driver

def extract_links(driver, url):
    # Navigate to the given URL
    driver.get(url)
    
    # Find all <a> tags on the page
    links = driver.find_elements(By.TAG_NAME, 'a')
    
    # Extract href attributes and filter out None values
    hrefs = [link.get_attribute('href') for link in links if link.get_attribute('href') is not None]
    
    # Optionally, resolve relative URLs to absolute URLs
    absolute_hrefs = [urljoin(url, href) for href in hrefs]
    internal_links = [link for link in absolute_hrefs if is_internal_link(url, link)]
    
    return internal_links


def score_link(link_element, base_url, driver):
    # Extract features
    text = link_element.text.lower()
    href = link_element.get_attribute('href')
    classes = link_element.get_attribute('class').split()
    ids = link_element.get_attribute('id').split()
    position = link_element.location['y']
    surrounding_text = driver.execute_script(
        "return arguments[0].parentNode.innerText;", link_element).lower()
    
    # Heuristic scoring
    score = 0
    # 1. Link Text
    if any(keyword in text for keyword in ['next', 'continue', 'more']):
        score += 1
    # 2. Link Position (assuming a higher 'y' value means lower on the page)
    height = driver.execute_script("return window.innerHeight")
    if position > height * 0.7:  # If the link is in the lower 30% of the page
        score += 1
    # 3. CSS Class/ID
    if any(keyword in classes + ids for keyword in ['next', 'pagination-next', 'continue']):
        score += 1
    # 4. Link Order (not implemented here, requires context of all links)
    # 5. URL Pattern
    if any(str.isdigit(c) for c in urlparse(href).path):
        score += 1
    # 6. Surrounding Text
    if any(keyword in surrounding_text for keyword in ['next', 'continue', 'upcoming']):
        score += 1
    
    return score

def is_internal_link_v2(base_url, link):
    """Check if the link is an internal link."""
    href = link.get_attribute('href')
    absolute_href = urljoin(base_url, href)
    return urlparse(absolute_href).netloc == urlparse(base_url).netloc

def extract_links_and_score(driver, url):
    driver.get(url)
    links = driver.find_elements(By.TAG_NAME, 'a')
    internal_links = [link for link in links if is_internal_link_v2(url, link)]
    scored_links = []
    for link in internal_links:
        if link.get_attribute('href'):
            score = score_link(link, url, driver)
            scored_links.append((link.get_attribute('href'), score))
    return scored_links

def main():
    url = 'https://12factor.net/'  # Change this to your target URL
    driver = initialize_browser()
    try:
        scored_links = extract_links_and_score(driver, url)
        # Sort links by score, highest first
        scored_links.sort(key=lambda x: x[1], reverse=True)
        for href, score in scored_links:
            print(f"Link: {href}, Score: {score}")
    finally:
        driver.quit()  # Ensure the driver closes when done

if __name__ == '__main__':
    main()