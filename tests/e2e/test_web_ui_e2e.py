"""
End-to-end tests for web UI functionality
"""

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
import time
import os
import base64


class TestMainPageE2E:
    """E2E tests for main index.html page"""
    
    @pytest.fixture
    def driver(self):
        """Create Selenium WebDriver"""
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # Run in headless mode
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        driver = webdriver.Chrome(options=options)
        driver.set_window_size(1920, 1080)
        yield driver
        driver.quit()
    
    @pytest.fixture
    def base_url(self):
        """Base URL for the application"""
        return "http://localhost:8080"
    
    def test_page_loads(self, driver, base_url):
        """Test that main page loads successfully"""
        driver.get(f"{base_url}/index.html")
        
        # Check page title
        assert "VLM Interface" in driver.title
        
        # Check main elements exist
        assert driver.find_element(By.ID, "chatContainer")
        assert driver.find_element(By.ID, "providerSelect")
        assert driver.find_element(By.CLASS_NAME, "chat-input")
    
    def test_provider_switching(self, driver, base_url):
        """Test switching between providers"""
        driver.get(f"{base_url}/index.html")
        
        # Find provider selector
        provider_select = Select(driver.find_element(By.ID, "providerSelect"))
        
        # Test switching to OpenAI
        provider_select.select_by_value("openai")
        time.sleep(1)
        
        # Check provider indicator
        provider_indicator = driver.find_element(By.CLASS_NAME, "provider-status")
        assert "openai" in provider_indicator.get_attribute("class")
        
        # Switch back to local
        provider_select.select_by_value("local")
        time.sleep(1)
        
        # Check provider indicator
        assert "local" in provider_indicator.get_attribute("class")
    
    def test_bank_extraction_tool(self, driver, base_url):
        """Test bank statement extraction tool selection"""
        driver.get(f"{base_url}/index.html")
        
        # Select bank transactions tool
        tool_button = driver.find_element(By.CSS_SELECTOR, "[data-tool='bank-transactions']")
        tool_button.click()
        
        # Check tool is selected
        assert "selected" in tool_button.get_attribute("class")
        
        # Check file input appears
        file_input = driver.find_element(By.ID, "imageInput")
        assert file_input.is_displayed()
    
    def test_privacy_warning_modal(self, driver, base_url):
        """Test privacy warning modal for sensitive content"""
        driver.get(f"{base_url}/index.html")
        
        # Switch to OpenAI
        provider_select = Select(driver.find_element(By.ID, "providerSelect"))
        provider_select.select_by_value("openai")
        
        # Type sensitive content
        chat_input = driver.find_element(By.ID, "userInput")
        chat_input.send_keys("Process my bank statement account 123456789")
        
        # Submit message
        send_button = driver.find_element(By.ID, "sendButton")
        send_button.click()
        
        # Wait for privacy modal
        wait = WebDriverWait(driver, 10)
        modal = wait.until(EC.visibility_of_element_located((By.ID, "privacyModal")))
        
        # Check modal content
        modal_text = modal.find_element(By.CLASS_NAME, "modal-body").text
        assert "sensitive" in modal_text.lower()
        assert "openai" in modal_text.lower()
        
        # Test cancel button
        cancel_button = modal.find_element(By.CSS_SELECTOR, "[onclick*='cancelOpenAI']")
        cancel_button.click()
        
        # Modal should be hidden
        wait.until(EC.invisibility_of_element_located((By.ID, "privacyModal")))
    
    def test_export_csv_functionality(self, driver, base_url):
        """Test CSV export button functionality"""
        driver.get(f"{base_url}/index.html")
        
        # First, we need to have some bank extraction results
        # This would require mocking or having a test server with pre-loaded data
        
        # Check export button appears after results
        # export_button = driver.find_element(By.ID, "exportCSV")
        # assert export_button.is_displayed()
        pass
    
    def test_error_handling_ui(self, driver, base_url):
        """Test error handling in UI"""
        driver.get(f"{base_url}/index.html")
        
        # Test with invalid server endpoint
        # This would test the error message display
        pass
    
    def test_responsive_design(self, driver, base_url):
        """Test responsive design elements"""
        driver.get(f"{base_url}/index.html")
        
        # Test mobile view
        driver.set_window_size(375, 667)  # iPhone SE size
        
        # Check elements still visible and functional
        assert driver.find_element(By.ID, "chatContainer")
        
        # Test tablet view
        driver.set_window_size(768, 1024)  # iPad size
        
        # Check layout adjustments
        assert driver.find_element(By.ID, "chatContainer")


class TestBankProcessorPageE2E:
    """E2E tests for bank_processor.html page"""
    
    @pytest.fixture
    def driver(self):
        """Create Selenium WebDriver"""
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        driver = webdriver.Chrome(options=options)
        yield driver
        driver.quit()
    
    def test_bank_processor_loads(self, driver, base_url):
        """Test bank processor page loads"""
        driver.get(f"{base_url}/bank_processor.html")
        
        # Check page elements
        assert driver.find_element(By.ID, "fileInput")
        assert driver.find_element(By.ID, "processButton")
        assert driver.find_element(By.ID, "outputFormatSelect")
    
    def test_format_selection(self, driver, base_url):
        """Test output format selection"""
        driver.get(f"{base_url}/bank_processor.html")
        
        # Find format selector
        format_select = Select(driver.find_element(By.ID, "outputFormatSelect"))
        
        # Test table format
        format_select.select_by_value("table")
        
        # Test JSON format
        format_select.select_by_value("json")
        
        # Verify selection changes
        assert format_select.first_selected_option.get_attribute("value") == "json"
    
    def test_file_upload_ui(self, driver, base_url):
        """Test file upload UI elements"""
        driver.get(f"{base_url}/bank_processor.html")
        
        # Check file input
        file_input = driver.find_element(By.ID, "fileInput")
        assert file_input.get_attribute("accept") == "image/*"
        
        # Check process button is initially disabled
        process_button = driver.find_element(By.ID, "processButton")
        assert process_button.get_attribute("disabled") is not None


class TestProviderFallbackE2E:
    """E2E tests for provider fallback functionality"""
    
    @pytest.fixture
    def driver(self):
        """Create Selenium WebDriver"""
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        driver = webdriver.Chrome(options=options)
        yield driver
        driver.quit()
    
    def test_openai_fallback_dialog(self, driver, base_url):
        """Test OpenAI fallback confirmation dialog"""
        driver.get(f"{base_url}/index.html")
        
        # This test would require simulating an OpenAI API failure
        # and checking that the fallback dialog appears
        pass
    
    def test_automatic_provider_switch(self, driver, base_url):
        """Test automatic provider switching on error"""
        driver.get(f"{base_url}/index.html")
        
        # This test would verify that the UI updates when
        # the server automatically switches providers
        pass


class TestAccessibility:
    """Accessibility tests for the web UI"""
    
    @pytest.fixture
    def driver(self):
        """Create Selenium WebDriver with accessibility testing"""
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        driver = webdriver.Chrome(options=options)
        yield driver
        driver.quit()
    
    def test_keyboard_navigation(self, driver, base_url):
        """Test keyboard navigation through UI"""
        driver.get(f"{base_url}/index.html")
        
        # Test tab navigation
        driver.find_element(By.TAG_NAME, "body").send_keys("\t")
        
        # Check focus moves through interactive elements
        # This would verify proper tab order
        pass
    
    def test_aria_labels(self, driver, base_url):
        """Test ARIA labels for screen readers"""
        driver.get(f"{base_url}/index.html")
        
        # Check important elements have ARIA labels
        buttons = driver.find_elements(By.TAG_NAME, "button")
        for button in buttons:
            assert button.get_attribute("aria-label") or button.text
    
    def test_color_contrast(self, driver, base_url):
        """Test color contrast for visibility"""
        driver.get(f"{base_url}/index.html")
        
        # This would use a tool to check WCAG color contrast requirements
        pass


if __name__ == "__main__":
    # Run specific test class
    pytest.main([__file__, "-v", "-k", "TestMainPageE2E"])