def screenPWM(pwmpercent, pin=18):
    """
    Note: if you don't add the newline, it'll fail every time
    """
    pwmf = "/dev/pi-blaster"
    try:
        f = open(pwmf, "w")
        f.write("%d=%1.1f\n" % (pin, pwmpercent))
        f.close()
    except IOError:
        pass
