#from playwright.sync_api import sync_playwright
import openpyxl
import os
import requests
from datetime import datetime

def fetch_latest_sofr_rate():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://www.newyorkfed.org/markets/reference-rates/sofr")
        page.wait_for_selector("table")
        sofr_table = page.query_selector("table")
        sofr_rows = sofr_table.query_selector_all("tr")
        if len(sofr_rows) > 1:
            latest_row = sofr_rows[1]
            columns = latest_row.query_selector_all("td")
            if columns:
                latest_row_data = [col.inner_text().strip() for col in columns]
                print(f"Latest Row Data (SOFR): {latest_row_data}")
                return latest_row_data
            else:
                print("No data found in the latest row.")
        else:
            print("No rows found in the SOFR table.")
        browser.close()
        return None

def fetch_latest_sofr_avg_data():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://www.newyorkfed.org/markets/reference-rates/sofr-averages-and-index")
        page.wait_for_selector("table")
        sofr_avg_table = page.query_selector("table")
        sofr_avg_rows = sofr_avg_table.query_selector_all("tr")
        if len(sofr_avg_rows) > 1:
            latest_row = sofr_avg_rows[1]
            columns = latest_row.query_selector_all("td")
            if columns:
                latest_row_data = [col.inner_text().strip() for col in columns]
                print(f"Latest Row Data (Avg Data): {latest_row_data}")
                return latest_row_data
            else:
                print("No data found in the latest row.")
        else:
            print("No rows found in the SOFR Averages table.")
        browser.close()
        return None

def fetch_treasury_rate(url, rate_name):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        page.wait_for_selector(".key-stat-title")  # Adjust selector if necessary
        rate_element = page.query_selector(".key-stat-title")
        if rate_element:
            rate = rate_element.inner_text().strip()
            print(f"Latest {rate_name}: {rate}")
            return str(rate)  # Ensure the rate is returned as a string
        else:
            print(f"Failed to fetch the {rate_name}.")
            return None
        browser.close()

def update_excel(file_path, sheet_name, data, headers):
    if os.path.exists(file_path):
        workbook = openpyxl.load_workbook(file_path)
    else:
        print(f"File not found: {file_path}")
        return
    if sheet_name in workbook.sheetnames:
        sheet = workbook[sheet_name]
    else:
        sheet = workbook.create_sheet(sheet_name)
    if sheet.max_row == 1 and sheet.max_column == 1 and sheet.cell(1, 1).value is None:
        for col_num, header in enumerate(headers, start=1):
            sheet.cell(row=1, column=col_num, value=header)
    sheet.append(data)
    workbook.save(file_path)
    print(f"Data updated in Excel file: {file_path}")

def parse_treasury_rate(rate_string):
    """
    Parse the treasury rate string to extract the rate and date.
    Example input: "3.88% for Apr 08 2025"
    Returns: (rate, formatted_date) -> ("3.88%", "04/08/2025")
    """
    try:
        rate, date_str = rate_string.split(" for ")
        formatted_date = datetime.strptime(date_str.strip(), "%b %d %Y").strftime("%m/%d/%Y")
        return rate.strip(), formatted_date
    except ValueError as e:
        print(f"Error parsing treasury rate: {e}")
        return None, None

def send_to_webhook(data):
    """
    Send the consolidated data to the specified webhook.
    """
    webhook_url = "https://hook.us1.make.com/p4e6fkaoj3n91pbcwn5b63h0kcegtp9a"
    try:
        response = requests.post(webhook_url, json=data)
        if response.status_code == 200:
            print("Data successfully sent to the webhook.")
        else:
            print(f"Failed to send data to the webhook. Status code: {response.status_code}, Response: {response.text}")
    except Exception as e:
        print(f"Error sending data to the webhook: {e}")

# OneDrive file path (replace with your actual OneDrive file path)
onedrive_path = os.path.expanduser("/Users/gunaseelanm/Library/CloudStorage/OneDrive-CastellanRealEstatePartners/SOFR Data/sofr_data.xlsx")

# Fetch SOFR rates, SOFR averages, and Treasury Rates
sofr_rate_data = fetch_latest_sofr_rate()
sofr_avg_data = fetch_latest_sofr_avg_data()
one_year_treasury_rate = fetch_treasury_rate(
    "https://ycharts.com/indicators/1_year_treasury_rate", "1-Year Treasury Rate"
)
two_year_treasury_rate = fetch_treasury_rate(
    "https://ycharts.com/indicators/2_year_treasury_rate", "2-Year Treasury Rate"
)
five_year_treasury_rate = fetch_treasury_rate(
    "https://ycharts.com/indicators/5_year_treasury_rate", "5-Year Treasury Rate"
)
ten_year_treasury_rate = fetch_treasury_rate(
    "https://ycharts.com/indicators/10_year_treasury_rate", "10-Year Treasury Rate"
)

# Prepare data for webhook
webhook_data = {}

# Update SOFR rate data in Excel and add to webhook data
if sofr_rate_data:
    date, rate, iPercentile, iiPercentile, iiiPercentile, ivPercentile, Volume = sofr_rate_data[0], sofr_rate_data[1],sofr_rate_data[2], sofr_rate_data[3], sofr_rate_data[4], sofr_rate_data[5], sofr_rate_data[6]
    update_excel(
        file_path=onedrive_path,
        sheet_name="SOFR Rates",
        data=[date, rate, iPercentile, iiPercentile, iiiPercentile, ivPercentile, Volume],
        headers=["Date", "Rate", "1st Percentile", "25th Percentile", "75th Percentile", "99th Percentile", "Volume"]
    )
    webhook_data["sofr_rate"] = {
        "date": date,
        "rate": rate,
        "1st_percentile": iPercentile,
        "25th_percentile": iiPercentile,
        "75th_percentile": iiiPercentile,
        "99th_percentile": ivPercentile,
        "volume": Volume
    }

# Update SOFR averages data in Excel and add to webhook data
if sofr_avg_data:
    date, avg_30, avg_90, avg_180, index = sofr_avg_data[0], sofr_avg_data[1], sofr_avg_data[2], sofr_avg_data[3], sofr_avg_data[4]
    update_excel(
        file_path=onedrive_path,
        sheet_name="SOFR Averages",
        data=[date, avg_30, avg_90, avg_180, index],
        headers=["Date", "30-Day Avg", "90-Day Avg", "180-Day Avg", "Index"]
    )
    webhook_data["sofr_averages"] = {
        "date": date,
        "30_day_avg": avg_30,
        "90_day_avg": avg_90,
        "180_day_avg": avg_180,
        "index": index
    }

# Update Treasury Rates in Excel and add to webhook data
treasury_rates = {}
if one_year_treasury_rate:
    rate, date = parse_treasury_rate(one_year_treasury_rate)
    if rate and date:
        treasury_rates["1_year_rate"] = rate
        treasury_rates["date"] = date

if two_year_treasury_rate:
    rate, date = parse_treasury_rate(two_year_treasury_rate)
    if rate and date:
        treasury_rates["2_year_rate"] = rate

if five_year_treasury_rate:
    rate, date = parse_treasury_rate(five_year_treasury_rate)
    if rate and date:
        treasury_rates["5_year_rate"] = rate

if ten_year_treasury_rate:
    rate, date = parse_treasury_rate(ten_year_treasury_rate)
    if rate and date:
        treasury_rates["10_year_rate"] = rate

if treasury_rates:
    update_excel(
        file_path=onedrive_path,
        sheet_name="Treasury Rates",
        data=[treasury_rates["date"], treasury_rates.get("1_year_rate"), treasury_rates.get("2_year_rate"),
              treasury_rates.get("5_year_rate"), treasury_rates.get("10_year_rate")],
        headers=["Date", "1-Year Rate", "2-Year Rate", "5-Year Rate", "10-Year Rate"]
    )
    webhook_data["treasury_rates"] = treasury_rates

# Send data to webhook
send_to_webhook(webhook_data)
