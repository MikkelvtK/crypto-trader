import requests
import sys
import os
import time
import functools
import config
import smtplib
from class_blueprints.exceptions import BinanceAccountIssue


def connection_authenticator(func):
    """Checks if there is a connection with the API"""
    def wrapper(*args, n=0, **kwargs):
        try:
            response = func(*args, **kwargs)

        except requests.exceptions.ConnectionError:

            # Restart bot if exception is not resolved
            if n == 3:
                os.system(config.command)
                sys.exit("Can't connect to the API. Restarting bot.")

            # Try connecting again, max 3 times
            else:
                print("There's an issue with the API connection. Please HODL.")
                time.sleep(5)
                return wrapper(*args, n=n + 1, **kwargs)
        else:
            return response
    return wrapper


def check_response(func):
    """Checks if the response is as expected"""
    def wrapper(*args, **kwargs):
        response = func(*args, **kwargs)

        if response.ok:
            return response.json()
        else:
            skippable_codes = (-1022, )
            try:
                if response.json()["code"] not in skippable_codes:
                    with smtplib.SMTP("smtp.gmail.com") as connection:
                        connection.starttls()
                        connection.login(config.my_email, config.email_password)
                        connection.sendmail(
                            from_addr=config.my_email,
                            to_addrs=config.to_email,
                            msg=f"{config.crash_mail_body} \n\nPs. Please fix the following issue:\n {response.text}."
                        )
            except NameError:
                print("No email given. No message will be send.")
            raise BinanceAccountIssue
    return wrapper


def timer_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        tic = time.perf_counter()
        value = func(*args, **kwargs)
        toc = time.perf_counter()
        duration = toc - tic
        print(f"Elapsed time: {duration:0.4f} seconds.")
        return value
    return wrapper
