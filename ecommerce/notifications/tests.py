import smtplib, ssl
import certifi

context = ssl.create_default_context(cafile=certifi.where())
with smtplib.SMTP("smtp.gmail.com", 587) as server:
    server.starttls(context=context)
    server.login("shawng32176@gmail.com", "xyjilrutycmhpgzl")
    print("Success!")