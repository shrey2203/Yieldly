import pandas as pd
import smtplib
import configparser
import io
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import formatdate
from email import encoders
from datetime import datetime
from config import db

def generateAndSendReport(reportId, recipients):
    print ("Inside Mail Dispatcher")
    config = configparser.ConfigParser()
    try:
        with open('./backend/emailConfig.properties', 'r') as f:
            config_string = '[DEFAULT]\n' + f.read()
        config.read_string(config_string)
    except FileNotFoundError:
        print("Error: emailConfig.properties file not found.")
        return
    
    sqlFilePath = "/Users/bhavya/Downloads/AppServer/Scripts/" + reportId + ".sql"
    
    try:
        with open(sqlFilePath, 'r') as f:
            sqlQuery = f.read()
    except FileNotFoundError:
        print(f"Error: SQL file not found at {sqlFilePath}")
        return

    fileName = f"Report_{reportId}_{datetime.now().strftime('%Y%m%d')}.xlsx"
    df = pd.read_sql(sqlQuery, db.engine)

    writer = pd.ExcelWriter(fileName, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Performance')
    
    workbook  = writer.book
    worksheet = writer.sheets['Performance']

    headerFormat = workbook.add_format({'bold': True, 'bg_color': '#D7E4BC', 'border': 1, 'align': 'center'})
    
    indianNumberFormat = workbook.add_format({
        'num_format': r'[>99999]##\,##\,##0;[<-99999]-##\,##\,##0;#,##0',
        'border': 1 
    })
    
    textFormat = workbook.add_format({'border': 1})

    for col_num, value in enumerate(df.columns.values):
        worksheet.write(0, col_num, value, headerFormat)
        column_len = max(df[value].astype(str).map(len).max(), len(value)) + 3
        
        if value in ["Date", "Daily Change %", "Monthly Change %", "Yearly Change %", "units", "nav", "dailyPnLPercentage", "overallPnLPercentage"]:
            worksheet.set_column(col_num, col_num, column_len, textFormat)
        else:
            worksheet.set_column(col_num, col_num, column_len, indianNumberFormat)

    writer.close()

    print ("Prepared Excel to be sent")

    # --- 4. Prepare Email Config ---
    try:
        recipients_str = ", ".join(recipients) if recipients else None

        email_params = {
            "send_from": config.get('DEFAULT', 'mail.send_from'),
            "send_to": recipients_str or config.get('DEFAULT', 'mail.send_to'),
            "subject": f"{config.get('DEFAULT', 'mail.subject')} - {datetime.now().date()}",
            "text": config.get('DEFAULT', 'mail.body'),
            "server": config.get('DEFAULT', 'mail.server'),
            "port": config.getint('DEFAULT', 'mail.port'),
            "username": config.get('DEFAULT', 'mail.username'),
            "password": config.get('DEFAULT', 'mail.password'),
            "isTls": True
        }
        print ("Fetched all configs successfully")

        send_mail(files=[fileName], **email_params)
        print("Report sent successfully!")
    except configparser.NoOptionError as e:
        print(f"Configuration Error: {e}")

def send_mail(send_from, send_to, subject, text, files, server, port, username='', password='', isTls=True):
    msg = MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = send_to
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject
    msg.attach(MIMEText(text))

    for f in files:
        part = MIMEBase('application', "octet-stream")
        with open(f, "rb") as file_data:
            part.set_payload(file_data.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="{f}"')
        msg.attach(part)

    with smtplib.SMTP(server, port) as smtp:
        if isTls:
            smtp.starttls()
        smtp.login(username, password)
        targets = [addr.strip() for addr in send_to.split(',')]
        smtp.sendmail(send_from, targets, msg.as_string())
        print ("Mail sent successfully")