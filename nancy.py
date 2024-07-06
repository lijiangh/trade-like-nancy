import csv, json, zipfile
import requests, PyPDF2, fitz
import time, os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

zip_file_url = 'https://disclosures-clerk.house.gov/public_disc/financial-pdfs/2024FD.zip'
pdf_file_url = 'https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/2024/'

# Email configuration
load_dotenv()
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
APP_PASSWORD = os.getenv("APP_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")

def check_for_new_trades():
    r = requests.get(zip_file_url)
    zipfile_name = '2024.zip'
    with open(zipfile_name, 'wb') as f:
        f.write(r.content)
    
    with zipfile.ZipFile(zipfile_name) as z:
        z.extractall('.')
    
    new_trades = []
    with open('2024FD.txt') as f:
        for line in csv.reader(f, delimiter='\t'):
            if line[1] == 'Pelosi':
                dt = datetime.strptime(line[7], '%m/%d/%Y')
                doc_id = line[8]
                new_trades.append((dt, doc_id))
    
    # Sort trades by date, most recent first
    new_trades.sort(key=lambda x: x[0], reverse=True)
    return new_trades

def send_email_notification(trades):
    if not trades:
        return

    subject = "New Nancy Pelosi Trades Detected"
    body = "New trades have been detected:\n\n"

    for trade in trades:
        body += f"Date: {trade[0].strftime('%Y-%m-%d')}\n"
        body += f"Document ID: {trade[1]}\n"
        body += f"PDF URL: {pdf_file_url}{trade[1]}.pdf\n\n"

    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, APP_PASSWORD)
        text = msg.as_string()
        server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, text)
        server.quit()
        print(f"Email notification sent for {len(trades)} trades")
    except Exception as e:
        print(f"Failed to send email notification: {e}")

def main():
    last_check = datetime.now() - timedelta(minutes=10)
    last_trade_date = None
    
    while True:
        current_time = datetime.now()
        if current_time - last_check >= timedelta(minutes=5):
            print("Checking for new trades...")
            all_trades = check_for_new_trades()
            
            if last_trade_date is None:
                new_trades = all_trades
            else:
                new_trades = [trade for trade in all_trades if trade[0] > last_trade_date]
            
            if new_trades:
                send_email_notification(new_trades)
                last_trade_date = new_trades[0][0]
            
            last_check = current_time
        time.sleep(60)

if __name__ == "__main__":
    main()