from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, Form
from selenium import webdriver
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import uvicorn
import time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

options = Options()
options.add_argument("--enable-logging")
options.add_argument("--headless")
options.add_argument("--log-level=0")
options.add_argument("--no-sandbox")
options.add_argument("--lang=en")
options.add_argument("--disable-translate")
options.add_argument("--start-maximized")

@app.post("/nassau_county")
async def nassau_county(last_name: str = Form(...), first_name: str = Form(...)):
    if not last_name or not first_name:
        raise HTTPException(status_code=400, detail="First Name and Last Name are required for the search.")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        driver.get("https://i2f.uslandrecords.com/NY/Nassau/D/Default.aspx")
        time.sleep(10)

        select_element1 = Select(driver.find_element(By.ID, "SearchCriteriaOffice1_DDL_OfficeName"))
        select_element1.select_by_value("Deeds/Mortgages")

        last_name_input = driver.find_element(By.ID, "SearchFormEx1_ACSTextBox_LastName1")
        last_name_input.clear()
        last_name_input.send_keys(last_name)

        first_name_input = driver.find_element(By.ID, "SearchFormEx1_ACSTextBox_FirstName1")
        first_name_input.clear()
        first_name_input.send_keys(first_name)

        select_element2 = Select(driver.find_element(By.ID, "SearchFormEx1_ACSRadioButtonList_PartyType1"))
        select_element2.select_by_value("D")

        select_element3 = Select(driver.find_element(By.ID, "SearchFormEx1_ACSRadioButtonList_NameType1"))
        select_element3.select_by_value("P")

        search_button = driver.find_element(By.ID, "SearchFormEx1_btnSearch")
        search_button.click()
        time.sleep(3)

        try:
            error_msg = driver.find_element(By.ID, "MessageBoxCtrl1_ErrorLabel1")
            if error_msg.is_displayed():
                driver.find_element(By.ID, "MessageBoxCtrl1_ButtonContainer").click()
                raise HTTPException(status_code=400, detail="Incorrect Name")
        except:
            pass

        results_data = []
        while True:
            data_container = driver.find_element(By.CSS_SELECTOR, "#DocList1_ContentContainer1 > table > tbody > tr:nth-child(1) > td > div > div:nth-child(2)")
            rows = data_container.find_elements(By.XPATH, ".//tr[contains(@class, 'DataGridRow') or contains(@class, 'DataGridAlternatingRow')]")
            
            for row in rows:
                cols = row.find_elements(By.TAG_NAME, "td")
                if len(cols) > 0:
                    result = {
                        "Type": cols[1].text,
                        "Name/ Corporation": cols[2].text,
                        "Book": cols[3].text,
                        "Page": cols[4].text,
                        "Type Desc.": cols[5].text,
                        "File Date": cols[6].text,
                        "Doc. #": cols[7].text,
                        "# of Pgs.": cols[8].text,
                    }
                    results_data.append(result)

            try:
                next_button = driver.find_element(By.ID, "DocList1_LinkButtonNext")
                if "disabled" in next_button.get_attribute("outerHTML"):
                    break
                else:
                    next_button.click()
                    time.sleep(5)
            except:
                break

        return {"data": results_data if results_data else "No data found"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

    finally:
        driver.quit()

@app.post("/suffolk_county")
async def suffolk_county(last_name: str = Form(...), first_name: str = Form(...)):
    if not last_name or not first_name:
        raise HTTPException(status_code=400, detail="First Name and Last Name are required for the search.")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        driver.get("https://clerk.suffolkcountyny.gov/kiosk/Agreement.aspx")

        time.sleep(10)

        cmdIAgree = driver.find_element(By.ID, "cmdIAgree")
        cmdIAgree.click()

        time.sleep(5)

        HERE_button = driver.find_element(By.LINK_TEXT, "HERE")
        HERE_button.click()
        
        time.sleep(5)

        radio_btn = driver.find_element(By.ID, "radio_name")
        radio_btn.click()

        driver.execute_script("document.getElementById('inputLastNameCorp').removeAttribute('disabled');")
        driver.execute_script("document.getElementById('inputFirstName').removeAttribute('disabled');")

        driver.find_element(By.ID, "inputLastNameCorp").send_keys(last_name)
        driver.find_element(By.ID, "inputFirstName").send_keys(first_name)

        driver.find_element(By.ID, "cmdSearchName").click()

        driver.find_element(By.ID, "tJudgments")

        WebDriverWait(driver, 90).until(
            EC.visibility_of_element_located((By.ID, "tJudgments"))
        )

        results_data = {}
        sections = ["Judgments", "Liens", "UCCs"]

        for section in sections:
            results_data[section] = []
            has_data = False

            while True:
                try:
                    # Get the rows for the current section
                    rows = driver.find_elements(By.XPATH, f"//div[@id='c{section}']//table/tbody/tr")
                    headers = driver.find_elements(By.XPATH, f"//div[@id='c{section}']//table/thead/tr/th")
                    header_names = [header.text.strip() for header in headers]

                    for row in rows:
                        data_row = {}
                        cells = row.find_elements(By.TAG_NAME, "td")
                        for i, cell in enumerate(cells):
                            if i < len(header_names):
                                data_row[header_names[i]] = cell.text.strip()
                        results_data[section].append(data_row)
                        has_data = True

                except Exception as e:
                    print(f"Error collecting data from section {section} on the current page:", e)
                    break

                try:
                    # Check if the 'Next' button exists and is enabled
                    next_button = driver.find_element(By.ID, f"t{section}_next")
                    if "disabled" in next_button.get_attribute("class"):
                        break  # Exit loop if 'Next' button is disabled
                    next_button.click()
                    time.sleep(2)
                except NoSuchElementException:
                    print(f"No 'Next' button found for {section}, stopping pagination.")
                    break  # Exit loop if 'Next' button does not exist for the section
                except Exception as e:
                    print(f"Error occurred when trying to click 'Next' for {section}: {e}")
                    break

            if not has_data:
                results_data[section] = 'No Records Found'

        return {"data": results_data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

    finally:
        driver.quit()


@app.post("/appext")
async def ucc_search(first_name: str = Form(...), last_name: str = Form(...)):
    if not last_name or not first_name:
        raise HTTPException(status_code=400, detail="First Name and Last Name are required for the search.")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        driver.get("https://appext20.dos.ny.gov/pls/ucc_public/web_search.main_frame")

        driver.switch_to.frame("main")
        debtor_search_link = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "NYS Standard Debtor Search"))
        )
        debtor_search_link.click()

        driver.switch_to.default_content()
        driver.switch_to.frame("rframe")

        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "pfirst"))
        )
        driver.find_element(By.ID, "pname").send_keys("")
        driver.find_element(By.ID, "plast").send_keys(last_name)
        driver.find_element(By.ID, "pfirst").send_keys(first_name)
        driver.find_element(By.ID, "sbutton").click()

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "form"))
        )

        results_data = []
        
        debtor_tables = driver.find_elements(By.XPATH, "//table[@align='CENTER'][@width='100%']")
        for debtor_table in debtor_tables:
            try:
                debtors = []
                all_rows = debtor_table.find_elements(By.XPATH, ".//tr")
                collecting_debtors = True
                
                for row in all_rows:
                    if "Secured Party Names" in row.text:
                        collecting_debtors = False
                        continue

                    if collecting_debtors:
                        debtor_name = row.find_element(By.XPATH, "./td[3]/font/b").text if row.find_elements(By.XPATH, "./td[3]/font/b") else None
                        debtor_address = row.find_element(By.XPATH, "./td[4]/font/b").text if row.find_elements(By.XPATH, "./td[4]/font/b") else None
                        if debtor_name:
                            debtors.append({
                                "debtor_name": debtor_name,
                                "debtor_address": debtor_address
                            })

                secured_parties = []
                collecting_secured_parties = False

                for row in all_rows:
                    if "Secured Party Names" in row.text:
                        collecting_secured_parties = True
                        continue

                    if collecting_secured_parties:
                        secured_name = row.find_element(By.XPATH, "./td[3]/font/b").text if row.find_elements(By.XPATH, "./td[3]/font/b") else None
                        secured_address = row.find_element(By.XPATH, "./td[4]/font/b").text if row.find_elements(By.XPATH, "./td[4]/font/b") else None
                        if not secured_name:
                            break
                        secured_parties.append({
                            "secured_party_name": secured_name,
                            "secured_party_address": secured_address
                        })

                filings_table = debtor_table.find_element(By.XPATH, "following-sibling::table[1]")
                filings_rows = filings_table.find_elements(By.XPATH, ".//tr[td]")

                filings = []
                for filing_row in filings_rows:
                    file_no = filing_row.find_element(By.XPATH, "./td[1]/font").text if filing_row.find_elements(By.XPATH, "./td[1]/font") else "N/A"
                    file_date = filing_row.find_element(By.XPATH, "./td[2]/font").text if filing_row.find_elements(By.XPATH, "./td[2]/font") else "N/A"
                    lapse_date = filing_row.find_element(By.XPATH, "./td[3]/font").text if filing_row.find_elements(By.XPATH, "./td[3]/font") else "N/A"
                    filing_type = filing_row.find_element(By.XPATH, "./td[4]/font").text if filing_row.find_elements(By.XPATH, "./td[4]/font") else "N/A"
                    pages = filing_row.find_element(By.XPATH, "./td[5]/font").text if filing_row.find_elements(By.XPATH, "./td[5]/font") else "N/A"
                    image_link = filing_row.find_element(By.XPATH, "./td[6]/font/a").get_attribute("href") if filing_row.find_elements(By.XPATH, "./td[6]/font/a") else "N/A"

                    filings.append({
                        "file_no": file_no,
                        "file_date": file_date,
                        "lapse_date": lapse_date,
                        "filing_type": filing_type,
                        "pages": pages,
                        "image_link": image_link
                    })
                
                results_data.append({
                    "debtors": debtors,
                    "secured_parties": secured_parties,
                    "filings": filings
                })
            
            except Exception as e:
                print(f"Error processing debtor table: {e}")

        return {"status": "success", "data": results_data}

    finally:
        driver.quit()


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)
