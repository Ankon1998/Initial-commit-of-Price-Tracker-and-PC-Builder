import smtplib

def send_alert(email_receiver, product_name, price, url):
    email_sender = "your_email@gmail.com"
    password = "your_app_password" # Use Google App Password

    subject = f"Price Drop Alert: {product_name}"
    body = f"Good news! The price for {product_name} has dropped to ${price}.\nCheck it out here: {url}"
    
    msg = f"Subject: {subject}\n\n{body}"

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(email_sender, password)
            server.sendmail(email_sender, email_receiver, msg)
            print("Alert email sent!")
    except Exception as e:
        print(f"Failed to send email: {e}")