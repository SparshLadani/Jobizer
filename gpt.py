import os
from openai import OpenAI
from dotenv import load_dotenv
import resumeParsing
from resumeParsing import extract_text_from_pdf
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from concurrent.futures import ThreadPoolExecutor

load_dotenv()

#Enter your own OpenAI API key
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

data = extract_text_from_pdf()

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
service = Service(executable_path=r'') #Add your chromedriver path
driver = webdriver.Chrome(service=service, options=chrome_options)

interested_areas = input("Enter one interested area, for example, sales manager or data scientist, you would like to find an internship or full-time job in: ")
residence = input("Enter which country or city you want to work in (If mentioning a city, please mention the province as well): ")
type_of_job = input("Are you looking for an internship/Co-op or full-time job: ")
languages = input("Enter which languages you are fluent in communication at the workplace: ")
remote_input = input("Do you want a remote job? (Yes/No): ").strip().lower()

prompt = interested_areas + " " + type_of_job + " " + residence
if remote_input == "yes":
    prompt = interested_areas + " " + type_of_job + " " + residence + " remote"

print(prompt)

def fetch_google_results(driver, prompt):
    driver.get("http://www.google.com")
    search = driver.find_element(By.NAME, "q")
    search.send_keys(prompt)
    search.send_keys(Keys.RETURN)
    time.sleep(2)  
    links = []
    search_results = driver.find_elements(By.XPATH, '//div[@id="center_col"]//a')
    
    for result in search_results:
        href = result.get_attribute('href')
        if href and "google" not in href:
            links.append(href)
    
    return links

def analyze_links_batch(data, link_batch, interested_areas, residence, type_of_job, languages):
    prompt = f"Analyze these links and suggest job postings from real companies for which I can apply based on the resume provided. Include factors: {interested_areas}, {residence}, {type_of_job}, {languages}. Links: {link_batch}\nResume: {data}"

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        max_tokens=4095 - len(data[:1000]),
        top_p=1,
        frequency_penalty=0.5,
        presence_penalty=0.5,
    )
    return response.choices[0].message.content

def process_job_search(prompt):
    links = fetch_google_results(driver, prompt)
    
    batch_size = 10
    relevant_links = []
    suggestions = []
    
    with ThreadPoolExecutor() as executor:
        future_to_links = {executor.submit(analyze_links_batch, data, links[i:i+batch_size], interested_areas, residence, type_of_job, languages): links[i:i+batch_size] for i in range(0, len(links), batch_size)}

        for future in future_to_links:
            try:
                suggestions.append(future.result())
                relevant_links.extend(future_to_links[future])
            except Exception as e:
                print(f"Error analyzing batch: {e}")
    
    return relevant_links, suggestions

relevant_links, suggestions = process_job_search(prompt)

with open('job_suggestions.txt', 'w') as file:
    file.write("Relevant Links:\n")
    file.write("\n".join(relevant_links))
    file.write("\n\nSuggestions:\n")
    file.write("\n".join(suggestions))

driver.quit()
