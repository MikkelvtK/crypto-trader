import requests
import sys
import os
import config
import time


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

            # Try connecting again
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
            sys.exit(f"Something is wrong. Please fix the following issue:\n {response.text}")
    return wrapper


def add_border(func):
    """Add a border to message"""
    def wrapper(*args, **kwargs):
        left_border = "<-------------------------"
        message = func(*args, **kwargs)
        right_border = ""
        while len(left_border + message) < 92:
            right_border += "-"
        return left_border + message + right_border + ">"
    return wrapper
