import requests
import sys
import os
import time
import functools
import config
import smtplib
import pandas as pd


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
            with smtplib.SMTP("smtp.gmail.com") as connection:
                connection.starttls()
                connection.login(config.my_email, config.email_password)
                connection.sendmail(
                    from_addr=config.my_email,
                    to_addrs=config.to_email,
                    msg=config.crash_mail_body
                )
            raise Exception(f"Something is wrong. Please fix the following issue:\n {response.text}")
    return wrapper


def add_border(func):
    """Add a border to message"""
    def wrapper(*args, **kwargs):
        data = func(*args, **kwargs)

        # Add border for each row in message
        for i in range(len(data) + 1):
            try:
                text = data[i]
            except IndexError:
                text = ""

            left_border = "<-----------------------"
            right_border = ""

            if isinstance(text, pd.Series):
                print(text)
            else:
                while len(left_border + text + right_border) < 80:
                    right_border += "-"

                print(left_border + text + right_border + ">")

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
