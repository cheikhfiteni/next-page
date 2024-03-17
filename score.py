from selenium import webdriver
from selenium.webdriver.common.by import By
from urllib.parse import urlparse, urljoin
from collections import defaultdict

import os

def is_internal_link(base_url, link):
    """Check if the link is an internal link."""
    return urlparse(link).netloc == urlparse(base_url).netloc

def is_internal_link_v2(base_url, link):
    """Check if the link is an internal link."""
    href = link.get_attribute('href')
    absolute_href = urljoin(base_url, href)
    return urlparse(absolute_href).netloc == urlparse(base_url).netloc

def initialize_browser():
    # Initialize the WebDriver. Ensure chromedriver is in your PATH or specify its location.
    options = webdriver.ChromeOptions()
    # Add options like headless mode if needed
    options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)
    return driver

def score_link_elements(link_elements, base_url, driver):
    # Extract features for all links
    link_data = []
    for link_element in link_elements:
        text = link_element.text.lower()
        href = link_element.get_attribute('href')
        classes = link_element.get_attribute('class').split()
        ids = link_element.get_attribute('id').split()
        position = link_element.location
        surrounding_text = driver.execute_script(
            "return arguments[0].parentNode.innerText;", link_element).lower()
        
        link_data.append({
            'element': link_element,
            'text': text,
            'href': href,
            'classes': classes,
            'ids': ids,
            'position': position,
            'surrounding_text': surrounding_text
        })

    # Determine the orientation of the link container
    vertical_orientation = True  # Default orientation
    if link_data:
        # Compare the 'x' positions of the first two links to guess the orientation
        if len(link_data) > 1 and link_data[0]['position']['x'] != link_data[1]['position']['x']:
            vertical_orientation = False

    # Heuristic scoring
    for link_info in link_data:
        score = 0
        # 1. Link Text
        if any(keyword in link_info['text'] for keyword in ['next', 'continue', 'more']):
            score += 1
        # 2. Link Position (assuming a higher 'y' value means lower on the page)
        height = driver.execute_script("return window.innerHeight")
        if link_info['position']['y'] > height * 0.7:  # If the link is in the lower 30% of the page
            score += 1
        # 3. CSS Class/ID
        if any(keyword in link_info['classes'] + link_info['ids'] for keyword in ['next', 'pagination-next', 'continue']):
            score += 1
        # 4. Link Order
        if vertical_orientation:
            # In a vertical container, earlier links are scored higher
            score += max(0, 1 - (link_info['position']['y'] / height))
        else:
            # In a horizontal container, later links are scored higher
            width = driver.execute_script("return window.innerWidth")
            score += link_info['position']['x'] / width
        # 5. URL Pattern
        if any(str.isdigit(c) for c in urlparse(link_info['href']).path):
            score += 1
        # 6. Surrounding Text
        if any(keyword in link_info['surrounding_text'] for keyword in ['next', 'continue', 'upcoming']):
            score += 1
        
        link_info['score'] = score

    # Return the scored links
    return [(link_info['href'], link_info['score']) for link_info in link_data]

def score_link_elements_v2(link_elements, base_url, driver):
    # Group links by their parent element
    parent_groups = defaultdict(list)
    for link_element in link_elements:
        parent = driver.execute_script("return arguments[0].parentNode;", link_element)
        parent_groups[parent].append(link_element)

    scored_links = []

    for parent, links in parent_groups.items():
        # Sort links by their position: 'y' for vertical, 'x' for horizontal
        sorted_links = sorted(links, key=lambda el: el.location['x' if len(links) > 1 and links[0].location['x'] != links[1].location['x'] else 'y'])

        for index, link_element in enumerate(sorted_links):
            text = link_element.text.lower()
            href = link_element.get_attribute('href')
            classes = link_element.get_attribute('class').split()
            ids = link_element.get_attribute('id').split()
            position = link_element.location
            surrounding_text = driver.execute_script(
                "return arguments[0].parentNode.innerText;", link_element).lower()

            score = 0
            # Additional scoring based on ordinal numbers in text
            ordinal_keywords = ['first', 'second', 'third', 'fourth', 'fifth', 'last']
            ordinal_numerals = [str(i) + 'st' for i in range(1, 21)] + \
                               [str(i) + 'nd' for i in range(2, 21) if i not in [12]] + \
                               [str(i) + 'rd' for i in range(3, 21) if i not in [13]] + \
                               [str(i) + 'th' for i in range(4, 21)] + \
                               ['i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii', 'viii', 'ix', 'x', 
                                'xi', 'xii', 'xiii', 'xiv', 'xv', 'xvi', 'xvii', 'xviii', 'xix', 'xx']
            if any(keyword in text for keyword in ordinal_keywords) or \
               any(numeral in text for numeral in ordinal_numerals):
                score += 1
            # 1. Link Text
            if any(keyword in text for keyword in ['next', 'continue', 'more']):
                score += 1
            # 2. Link Position (assuming a higher 'y' value means lower on the page)
            height = driver.execute_script("return window.innerHeight")
            if position['y'] > height * 0.7:  # If the link is in the lower 30% of the page
                score += 1
            # 3. CSS Class/ID
            if any(keyword in classes + ids for keyword in ['next', 'pagination-next', 'continue']):
                score += 1
            # 4. Link Order
            # Score based on the index within the sorted list of links in the same parent
            if len(links) > 1 and links[0].location['x'] != links[1].location['x']:
                # Horizontal container: later links are scored higher
                score += (len(links) - index - 1) / len(links)
            else:
                # Vertical container: earlier links are scored higher
                score += index / len(links)
            # 5. URL Pattern
            if any(str.isdigit(c) for c in urlparse(href).path):
                score += 1
            # 6. Surrounding Text
            if any(keyword in surrounding_text for keyword in ['next', 'continue', 'upcoming']):
                score += 1

            scored_links.append((href, score))

    return scored_links

def extract_links_and_score(driver, url):
    driver.get(url)
    links = driver.find_elements(By.TAG_NAME, 'a')
    internal_links = [link for link in links if is_internal_link_v2(url, link)]
    # return score_link_elements(internal_links, url, driver)
    return score_link_elements_v2(internal_links, url, driver)

def main():
    url = 'https://craftinginterpreters.com/introduction.html'  # Change this to your target URL
    driver = initialize_browser()
    try:
        scored_links = extract_links_and_score(driver, url)
        # Sort links by score, highest first
        scored_links.sort(key=lambda x: x[1], reverse=True)
        for href, score in scored_links:
            print(f"Link: {href}, Score: {score}")
    finally:
        print("Quitting the browser... \n\n\n")
        driver.quit()  # Ensure the driver closes when done

if __name__ == '__main__':
    main()