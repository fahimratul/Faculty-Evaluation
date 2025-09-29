# Faculty Evaluation Automation

Automates the repetitive faculty evaluation process on the MIST student portal.

> DISCLAIMER: Use only for your own account and only if automating does not violate your university's terms of use or academic integrity policies. Always provide honest feedback where required.

---
## Features
- Logs into `https://student.mist.ac.bd/login` using interactive credential prompts.
- Navigates to the faculty evaluation dashboard.
- Iteratively opens each pending faculty evaluation.
- Selects the first ("Very Good") answer option for all 10 questions (configurable).
- Fills Overall Comments and Recommendations (configurable) and submits.
- Loops until no more "Evaluate" buttons remain.
- Defensive waits + JavaScript clicking to reduce intermittent Selenium issues.

---
## Requirements
- Python 3.9+ (tested with Python 3.10+ recommended)
- Google Chrome (matching version for ChromeDriver)
- ChromeDriver (auto-managed if you install `webdriver-manager`, otherwise place driver in PATH)
- Selenium 4.x

### Install dependencies
Create (optional) virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install Selenium:
```bash
pip install selenium
```

(OPTIONAL) If you prefer automatic driver management:
```bash
pip install webdriver-manager
```
Then replace the driver initialization in `fe.py` with a managed example (instructions included below under Customization > Driver Management).

---
## Running
From the project directory:
```bash
python fe.py
```
Enter your username/ID and password at the prompts.

To run headless (no browser window), open `fe.py` and uncomment:
```python
# options.add_argument('--headless')
```
You may also want:
```python
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')
options.add_argument('--window-size=1280,1024')
```

---
## Git Repository Setup
Initialize and push to a new GitHub repository:
```bash
git init
git add fe.py README.md
git commit -m "Automate faculty evaluation"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```
(Replace the remote URL with your actual repository.)

---
## Customization
### 1. Changing the Selected Rating (Very Good -> Good, etc.)
In `fe.py`, inside the function `evaluate_faculty`, locate this block (simplified excerpt):
```python
answer_container = q_elem.find_element(By.XPATH, "../../following-sibling::div")
very_good_option = answer_container.find_element(
    By.XPATH, ".//div[contains(@class,'semesterEvaluation_answer_item__G6tGB')]"
)
```
Currently it picks the **first** answer option ("Very Good"). To select a different one, fetch all answer items and index the one you want:
```python
options = answer_container.find_elements(
    By.XPATH, ".//div[contains(@class,'semesterEvaluation_answer_item__G6tGB')]"
)
# Index mapping (based on observed order):
# 0 = Very Good, 1 = Good, 2 = Average, 3 = Poor, 4 = Very Poor
chosen = options[1]  # For "Good"
```
Replace the two lines that define `very_good_option` and subsequent usage with the snippet above and then use `chosen` instead of `very_good_option`.

### 2. Changing Overall Comments / Recommendations
Still within `evaluate_faculty`, find:
```python
comments_field.send_keys("Good performance overall. N/A")
...
recommendations_field.send_keys("Keep up the good work. N/A")
```
Edit those strings to whatever you prefer, for example:
```python
comments_field.send_keys("N/A")
recommendations_field.send_keys("N/A")
```
Or load them from environment variables for privacy:
```python
import os
comments_field.send_keys(os.getenv("EVAL_COMMENTS", "N/A"))
recommendations_field.send_keys(os.getenv("EVAL_RECOMMEND", "N/A"))
```
Then run with:
```bash
EVAL_COMMENTS="Overall good" EVAL_RECOMMEND="Continue same approach" python fe.py
```

### 3. Adjusting Delays
There are small `time.sleep(...)` calls for stability. You can:
- Reduce them to speed up (risk: intermittent failures)
- Increase if elements load slowly for you
Consider replacing them with explicit waits if you need further robustness.

### 4. Headless / CI Usage
Enable headless mode and ensure you pass additional Chrome flags if running in a container (see "Running" section). You can also wrap `main()` in a try/except that returns a non-zero exit code for integration pipelines.

### 5. Driver Management with webdriver-manager (Optional)
If you installed `webdriver-manager`, replace:
```python
driver = webdriver.Chrome(options=options)
```
with:
```python
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)
```
This auto-downloads a compatible driver.

---
## Error Handling & Debugging Tips
- If answers fail to click, ensure the class names haven't changed (UI updates may break selectors).
- Insert a screenshot capture for debugging:
```python
driver.save_screenshot(f"debug_{int(time.time())}.png")
```
- Run with slower network? Add `options.add_argument('--disable-dev-shm-usage')`.

---
## Ethical & Academic Note
Automating evaluations may reduce the quality of feedback faculty rely on for improvement. Use responsibly and ensure compliance with institutional policies.

---
## Roadmap Ideas (Optional Enhancements)
- CLI flags for mode (e.g., `--rating good`)
- Randomize ratings within a safe set
- Progress CSV log
- Resume capability / skip already done log
- Parallel evaluation (probably unnecessary)

---
## License
Add a license of your choice (e.g., MIT) if you plan to publish this.

---
## Support
Open an issue in your repository or extend the script based on the customization guidelines above.
