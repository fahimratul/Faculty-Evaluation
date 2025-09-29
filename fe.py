from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time

def login(driver, username, password):
    """Login to the student portal"""
    print("Navigating to login page...")
    driver.get("https://student.mist.ac.bd/login")
    
    try:
        # Wait for login form to load
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "email"))
        )
        password_field = driver.find_element(By.NAME, "password")
        
        # Enter credentials
        username_field.clear()
        username_field.send_keys(username)
        password_field.clear()
        password_field.send_keys(password)
        
        # Click login button
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_button.click()
        
        print("Login submitted, waiting for redirect...")
        time.sleep(3)
        
        return True
    except Exception as e:
        print(f"Login failed: {e}")
        return False

def evaluate_faculty(driver, faculty_name):
    """Evaluate a single faculty member"""
    try:
        print(f"Evaluating: {faculty_name}")
        # Wait until at least 10 question number elements are present
        try:
            WebDriverWait(driver, 10).until(
                lambda d: len(d.find_elements(By.XPATH, "//div[contains(@class,'semesterEvaluation_question_number__') and starts-with(normalize-space(.), 'Q')]") ) >= 10
            )
        except TimeoutException:
            print("  Could not detect 10 questions on the page (timeout).")
            return False

        question_number_elems = driver.find_elements(By.XPATH, "//div[contains(@class,'semesterEvaluation_question_number__') and starts-with(normalize-space(.), 'Q')]")
        
        for idx, q_elem in enumerate(question_number_elems, start=1):
            label = q_elem.text.strip()
            try:
                # Navigate from the question number element up two levels then to the sibling answers container
                answer_container = q_elem.find_element(By.XPATH, "../../following-sibling::div")
                very_good_option = answer_container.find_element(By.XPATH, ".//div[contains(@class,'semesterEvaluation_answer_item__G6tGB')]")

                # Skip click if already active
                classes = very_good_option.get_attribute("class") or ""
                if 'semesterEvaluation_answer_item_active' in classes:
                    print(f"  {label} already 'Very Good' (active)")
                else:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", very_good_option)
                    WebDriverWait(driver, 5).until(EC.element_to_be_clickable(very_good_option))
                    driver.execute_script("arguments[0].click();", very_good_option)
                    print(f"  Selected {label} -> Very Good")
                time.sleep(0.15)
            except Exception as e:
                print(f"  Error answering {label or 'Q'+str(idx)}: {e}")
                # Optional: capture a small debug snippet
                try:
                    snippet = very_good_option.get_attribute('outerHTML')[:120]
                    print(f"    Debug snippet: {snippet}...")
                except:
                    pass
        
        # Click the submit button to open the modal
        submit_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Submit')]"))
        )
        submit_button.click()
        print("  Opened comments modal")
        time.sleep(1)
        
        # Fill in the modal form
        try:
            # Wait for modal to appear
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "evaluate_form"))
            )
            
            # Fill overall comments
            comments_field = driver.find_element(By.NAME, "comments")
            comments_field.clear()
            comments_field.send_keys("Good performance overall. N/A")
            
            # Fill recommendations
            recommendations_field = driver.find_element(By.NAME, "recommendations")
            recommendations_field.clear()
            recommendations_field.send_keys("Keep up the good work. N/A")
            
            print("  Filled comments and recommendations")
            time.sleep(0.5)
            
            # Submit the form
            modal_submit = driver.find_element(By.CSS_SELECTOR, "button[type='submit'][form='evaluate_form']")
            modal_submit.click()
            print(f"  ✓ Evaluation submitted for {faculty_name}")
            time.sleep(2)
            
            return True
            
        except Exception as e:
            print(f"  Error filling modal: {e}")
            return False
            
    except Exception as e:
        print(f"Error evaluating faculty: {e}")
        return False

def get_faculty_list(driver):
    """Get list of all faculty members to evaluate"""
    try:
        # Find all evaluate buttons
        evaluate_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Evaluate')]")
        
        faculty_list = []
        for button in evaluate_buttons:
            try:
                # Get faculty name from the same container
                parent = button.find_element(By.XPATH, "./ancestor::div[contains(@class, 'semesterEvaluation_faculty_item')]")
                name_element = parent.find_element(By.XPATH, ".//div[contains(@class, 'MuiBox-root')][2]")
                faculty_name = name_element.text.strip()
                faculty_list.append((faculty_name, button))
            except:
                continue
        
        return faculty_list
    except Exception as e:
        print(f"Error getting faculty list: {e}")
        return []

def main():
    # Get user credentials
    username = input("Enter your username/ID: ")
    password = input("Enter your password: ")
    
    # Setup Chrome driver
    print("\nInitializing browser...")
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    # Uncomment the next line to run headless (without visible browser)
    # options.add_argument('--headless')
    
    driver = webdriver.Chrome(options=options)
    
    try:
        # Login
        if not login(driver, username, password):
            print("Login failed. Exiting...")
            return
        
        # Navigate to evaluation page
        print("\nNavigating to faculty evaluation page...")
        driver.get("https://student.mist.ac.bd/semester-evaluation/faculty-evaluation")
        time.sleep(3)
        
        # Process evaluations
        total_evaluated = 0
        while True:
            print("\nChecking for faculty members to evaluate...")
            
            # Get current list of faculty to evaluate
            faculty_list = get_faculty_list(driver)
            
            if not faculty_list:
                print("\n✓ All faculty evaluations completed!")
                break
            
            print(f"Found {len(faculty_list)} faculty member(s) to evaluate")
            
            # Get the first faculty member
            faculty_name, evaluate_button = faculty_list[0]
            
            # Click evaluate button
            evaluate_button.click()
            time.sleep(2)
            
            # Evaluate this faculty member
            if evaluate_faculty(driver, faculty_name):
                total_evaluated += 1
                print(f"Progress: {total_evaluated} evaluation(s) completed")
            
            # Go back to the main evaluation page
            driver.get("https://student.mist.ac.bd/semester-evaluation/faculty-evaluation")
            time.sleep(2)
        
        print(f"\n{'='*50}")
        print(f"COMPLETED: {total_evaluated} faculty evaluations finished!")
        print(f"{'='*50}")
        
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Keep browser open for 5 seconds to see results
        print("\nClosing browser in 5 seconds...")
        time.sleep(5)
        driver.quit()

if __name__ == "__main__":
    main()