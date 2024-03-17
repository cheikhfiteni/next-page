import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from urllib.parse import urlparse, urljoin


def take_screenshot(driver, filename):
    # Ensure the directory for screenshots exists, if not, create it
    screenshot_directory = "screenshots"
    if not os.path.exists(screenshot_directory):
        os.makedirs(screenshot_directory)
    
    # Define the path for the screenshot file
    filepath = os.path.join(screenshot_directory, filename)
    
    # Save the screenshot to the specified file path
    driver.save_screenshot(filepath)
    print(f"Screenshot saved to {filepath}")

def take_full_page_screenshot(driver, filename):
    # Set the window size to the page's width and the height required to capture the full page
    original_size = driver.get_window_size()
    required_width = driver.execute_script('return document.body.parentNode.scrollWidth')
    required_height = driver.execute_script('return document.body.parentNode.scrollHeight')
    driver.set_window_size(required_width, required_height)
    
    # Ensure the directory for screenshots exists, if not, create it
    screenshot_directory = "screenshots"
    os.makedirs(screenshot_directory, exist_ok=True)
    
    # Define the path for the screenshot file
    filepath = os.path.join(screenshot_directory, filename)
    
    # Save the screenshot to the specified file path
    driver.save_screenshot(filepath)
    print(f"Full page screenshot saved to {filepath}")
    
    # Revert back to the original window size
    driver.set_window_size(original_size['width'], original_size['height'])