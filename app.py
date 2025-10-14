from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import time
import threading
import queue
import contextlib
import sys
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from tkinter import ttk
import random

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
                        # List of possible comments and recommendations
            comments_list = [
                "Good performance overall",
                "Very helpful and knowledgeable.",
                "Explains concepts clearly.",
                "Supportive and approachable.",
                "Makes learning interesting.",
                "Excellent teaching style.",
                "Engages students effectively.",
                "Always willing to help.",
                "Great communication skills.",
                "Creates a positive environment."
            ]
            recommendations_list = [
                "Keep up the good work",
                "Continue to motivate students",
                "Maintain current teaching methods",
                "Encourage more student participation",
                "Provide more real-life examples",
                "Give more feedback on assignments",
                "Organize more interactive sessions",
                "Use more visual aids",
                "Be available for extra help",
                "Keep improving"
            ]
            # Randomly select a comment and recommendation
            comment = random.choice(comments_list)
            recommendation = random.choice(recommendations_list)

            # Fill overall comments
            comments_field = driver.find_element(By.NAME, "comments")
            comments_field.clear()
            comments_field.send_keys(comment)
            
            # Fill recommendations
            recommendations_field = driver.find_element(By.NAME, "recommendations")
            recommendations_field.clear()
            recommendations_field.send_keys(recommendation)
            
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
    pass


# --- New GUI + worker implementation ---
class QueueWriter:
    """File-like object that writes to a queue (for redirecting stdout)"""
    def __init__(self, q, orig=None):
        self.q = q
        self.orig = orig

    def write(self, s):
        if s and not s.isspace():
            # split lines and put each
            for line in s.splitlines():
                self.q.put(line)
        if self.orig:
            try:
                self.orig.write(s)
            except Exception:
                pass

    def flush(self):
        if self.orig:
            try:
                self.orig.flush()
            except Exception:
                pass


def create_driver(preferred: str = 'chrome'):
    """Create a webdriver instance. preferred: 'chrome' or 'edge'. Will try fallback if preferred is unavailable."""
    preferred = (preferred or 'chrome').lower()
    def try_chrome():
        chrome_opts = webdriver.ChromeOptions()
        chrome_opts.add_argument('--start-maximized')
        # chrome_opts.add_argument('--headless')
        return webdriver.Chrome(options=chrome_opts)

    def try_edge():
        edge_opts = webdriver.EdgeOptions()
        edge_opts.add_argument('--start-maximized')
        # edge_opts.add_argument('--headless')
        return webdriver.Edge(options=edge_opts)

    # order of attempts based on preference
    attempts = []
    if preferred == 'edge':
        attempts = [('edge', try_edge), ('chrome', try_chrome)]
    else:
        attempts = [('chrome', try_chrome), ('edge', try_edge)]

    last_exc = None
    for name, fn in attempts:
        try:
            driver = fn()
            print(f'Using {"Google Chrome" if name=="chrome" else "Microsoft Edge"} for automation')
            return driver
        except WebDriverException as e:
            print(f'{name.capitalize()} not available or failed to start: {e}')
            last_exc = e

    # if we get here, none succeeded
    raise RuntimeError('Could not start Chrome or Edge. Please install a supported browser or check your Selenium setup.') from last_exc


def run_evaluation(username, password, log_q: queue.Queue, progress_q: queue.Queue, stop_event: threading.Event, preferred_browser: str = 'chrome'):
    """Background worker that runs the evaluation flow and posts logs/progress to queues."""
    orig_stdout = sys.stdout
    writer = QueueWriter(log_q, orig=orig_stdout)
    try:
        with contextlib.redirect_stdout(writer):
            print('\nInitializing browser...')
            try:
                driver = create_driver(preferred=preferred_browser)
            except Exception as e:
                print(f'Failed to start a browser: {e}')
                progress_q.put(('error', 'No browser available'))
                return

            try:
                # Login
                if not login(driver, username, password):
                    print('Login failed. Exiting...')
                    return

                # Navigate to evaluation page
                print('\nNavigating to faculty evaluation page...')
                driver.get('https://student.mist.ac.bd/semester-evaluation/faculty-evaluation')
                time.sleep(3)

                # Process evaluations
                total_evaluated = 0

                # Determine total faculty to evaluate (initial snapshot)
                faculty_list = get_faculty_list(driver)
                total_faculty = len(faculty_list)
                progress_q.put(('total', total_faculty))

                while not stop_event.is_set():
                    print('\nChecking for faculty members to evaluate...')
                    faculty_list = get_faculty_list(driver)
                    if not faculty_list:
                        print('\n✓ All faculty evaluations completed!')
                        break

                    print(f'Found {len(faculty_list)} faculty member(s) to evaluate')
                    faculty_name, evaluate_button = faculty_list[0]

                    # Click evaluate button
                    evaluate_button.click()
                    time.sleep(2)

                    # Evaluate this faculty member
                    success = evaluate_faculty(driver, faculty_name)
                    if success:
                        total_evaluated += 1
                        # notify progress (completed count)
                        progress_q.put(('progress', total_evaluated))
                        print(f'Progress: {total_evaluated} evaluation(s) completed')

                    # Go back to the main evaluation page
                    driver.get('https://student.mist.ac.bd/semester-evaluation/faculty-evaluation')
                    time.sleep(2)

                print(f"\n{'='*50}")
                print(f'COMPLETED: {total_evaluated} faculty evaluations finished!')
                print(f"{'='*50}")

            except Exception as e:
                print(f'\nAn error occurred: {e}')
                import traceback
                traceback.print_exc()

            finally:
                print('\nClosing browser in 5 seconds...')
                time.sleep(5)
                try:
                    driver.quit()
                except Exception:
                    pass
    finally:
        # ensure stdout is restored (contextlib does this automatically)
        pass


def gui_main():
    root = tk.Tk()
    root.title('Faculty Evaluation Bot')
    root.geometry('700x500')

    frame = tk.Frame(root)
    frame.pack(padx=8, pady=8, fill='x')

    tk.Label(frame, text='Username/ID:').grid(row=0, column=0, sticky='w')
    username_var = tk.StringVar()
    tk.Entry(frame, textvariable=username_var, width=40).grid(row=0, column=1, sticky='w')

    tk.Label(frame, text='Password:').grid(row=1, column=0, sticky='w')
    password_var = tk.StringVar()
    tk.Entry(frame, textvariable=password_var, show='*', width=40).grid(row=1, column=1, sticky='w')

    # Browser preference
    tk.Label(frame, text='Browser:').grid(row=2, column=0, sticky='w')
    browser_var = tk.StringVar(value='chrome')
    browser_frame = tk.Frame(frame)
    browser_frame.grid(row=2, column=1, sticky='w')
    tk.Radiobutton(browser_frame, text='Google Chrome', variable=browser_var, value='chrome').pack(side='left')
    tk.Radiobutton(browser_frame, text='Microsoft Edge', variable=browser_var, value='edge').pack(side='left')

    btn_frame = tk.Frame(root)
    btn_frame.pack(padx=8, pady=(0,8), fill='x')

    # Use ttk for nicer buttons and progressbar
    style = ttk.Style()
    try:
        style.theme_use('clam')
    except Exception:
        pass
    style.configure('Accent.TButton', foreground='white', background='#4a90e2', padding=6)
    style.map('Accent.TButton', background=[('active', '#357ab8')])

    start_btn = ttk.Button(btn_frame, text='Start', width=12, style='Accent.TButton')
    stop_btn = ttk.Button(btn_frame, text='Stop', width=12, state='disabled')
    start_btn.pack(side='left', padx=(0,8))
    stop_btn.pack(side='left')

    progress_label = tk.Label(btn_frame, text='Evaluations completed: 0')
    progress_label.pack(side='left', padx=12)

    # Progress bar (determinate) and percentage
    progressbar = ttk.Progressbar(btn_frame, orient='horizontal', length=240, mode='determinate')
    progressbar.pack(side='left', padx=(8,4))
    percent_label = tk.Label(btn_frame, text='0%')
    percent_label.pack(side='left')

    log_box = ScrolledText(root, state='disabled', height=20)
    log_box.pack(padx=8, pady=4, fill='both', expand=True)

    log_q = queue.Queue()
    progress_q = queue.Queue()
    worker_thread = None
    stop_event = threading.Event()

    def append_log(line):
        log_box.configure(state='normal')
        log_box.insert('end', line + '\n')
        log_box.see('end')
        log_box.configure(state='disabled')

    def poll_queues():
        try:
            while True:
                line = log_q.get_nowait()
                append_log(line)
        except queue.Empty:
            pass

        try:
            total = getattr(poll_queues, '_total', None)
            completed = getattr(poll_queues, '_completed', 0)
            while True:
                item = progress_q.get_nowait()
                if isinstance(item, tuple) and item[0] == 'error':
                    append_log('ERROR: ' + str(item[1]))
                elif isinstance(item, tuple) and item[0] == 'total':
                    # total number of faculty (for percent calculation)
                    poll_queues._total = int(item[1]) if item[1] is not None else 0
                    total = poll_queues._total
                    # reset progressbar
                    progressbar['value'] = 0
                    percent_label.config(text='0%')
                    progress_label.config(text=f'Evaluations completed: 0')
                elif isinstance(item, tuple) and item[0] == 'progress':
                    completed = int(item[1])
                    poll_queues._completed = completed
                    progress_label.config(text=f'Evaluations completed: {completed}')
                    # update percentage if total known
                    if total and total > 0:
                        pct = int((completed / total) * 100)
                        progressbar['maximum'] = 100
                        progressbar['value'] = pct
                        percent_label.config(text=f'{pct}%')
                    else:
                        # Unknown total: just pulse progressbar
                        progressbar.config(mode='indeterminate')
                        try:
                            progressbar.start(10)
                        except Exception:
                            pass
                else:
                    # numbers only (legacy)
                    completed = int(item)
                    poll_queues._completed = completed
                    progress_label.config(text=f'Evaluations completed: {completed}')
        except queue.Empty:
            pass

        root.after(200, poll_queues)

    def on_start():
        nonlocal worker_thread, stop_event
        username = username_var.get().strip()
        password = password_var.get().strip()
        if not username or not password:
            append_log('Please enter username and password')
            return

        start_btn.config(state='disabled')
        stop_btn.config(state='normal')
        log_box.configure(state='normal')
        log_box.delete('1.0', 'end')
        log_box.configure(state='disabled')
        progress_label.config(text='Evaluations completed: 0')

        # start background worker
        stop_event = threading.Event()
        preferred_browser = browser_var.get()
        worker_thread = threading.Thread(target=run_evaluation, args=(username, password, log_q, progress_q, stop_event, preferred_browser), daemon=True)
        worker_thread.start()

    def on_stop():
        nonlocal stop_event
        append_log('Stop requested. Attempting to stop...')
        stop_event.set()
        stop_btn.config(state='disabled')
        start_btn.config(state='normal')

    start_btn.config(command=on_start)
    stop_btn.config(command=on_stop)

    root.after(200, poll_queues)
    root.mainloop()

if __name__ == "__main__":
    gui_main()
