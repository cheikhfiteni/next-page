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

def main():
    url = 'https://12factor.net/'  # Change this to your target URL
    driver = initialize_browser()
    try:
        links = extract_links(driver, url)
        for link in links:
            print(link)
    finally:
        driver.quit()  # Ensure the driver closes when done

if __name__ == '__main__':
    main()
