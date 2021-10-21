def format_border(message):
    left_border = "<---------------------"
    right_border = ""

    while len(left_border + message + right_border) < 80:
        right_border += "-"

    print(left_border + message + right_border + ">")
