#!/usr/bin/python3

import argparse
import requests
import re
import hashlib
import binascii


def main():
    print("""
[+] *****************************************************************************************
[+] Mikrotik Hotspot Logout Script v1.0
[+] *****************************************************************************************
[+]""")
    args = get_args()

    logout(args['target'])

def logout(target):
    session = requests.Session()

    # check status
    try:
        logout_page = session.get(target)
        if logout_page.status_code != 200:
            print(f'[!] Logout page request at {target} returned a status code of {logout_page.status_code}')
            return False

        # check and see if logged in
        status_pattern = re.search('Welcome (.*)!', logout_page.text)
        if status_pattern is not None:
            print(f'[+] Device is currently logged in as {status_pattern.group(1)}')

        # get url of login page
        # <form action="http://192.168.88.10/logout" name="logout" onsubmit="return openLogout()">
        logout_pattern = re.search('form action="(.*/logout)"', logout_page.text)
        if logout_pattern is None:
            print(f'[!] Logout page at {target} contained no URL for logout')
            print()
            exit(0)

        logout_url = logout_pattern.group(1)

        # log out
        logout_response = session.get(logout_url)
        if logout_response.status_code != 200:
            print(f'[!] Logout page at {logout_url} returned a status code of {logout_url.status_code}')
            exit(0)

        # verify logout
        success_pattern = re.search('you have just logged out', logout_response.text)
        if success_pattern:
            print(f'[+] Success - Logged out "{status_pattern.group(1)}" from {logout_url}')
        else:
            print(f'[!] Fail - Did not log out from {logout_url}')

    except Exception as ex:
        print(ex)

    print()



def get_args():
    """
    Get and validate command line arguments and return dictionary of those key/values
    :return:
    """
    ap = argparse.ArgumentParser()

    ap.add_argument("-t", "--target", required=False,
                    help="Target IP; defaults to 192.168.88.10")


    args = vars(ap.parse_args())
    # print(args)

    # target ip
    if args['target'] is None:
        args['target'] = 'http://192.168.88.10'

    return args

if __name__ == "__main__":
    main()

    """
    Example of /status page with logout form
    
<form action="http://192.168.88.10/logout" name="logout" onsubmit="return openLogout()">
<br><div style="text-align: center;">Welcome user1!</div><br><table border="1" class="tabula">

	

	<tbody><tr><td align="right">IP address:</td><td>192.168.88.230</td></tr>
	<tr><td align="right">bytes up/down:</td><td>11.3 KiB / 13.4 KiB</td></tr>

	<tr><td align="right">connected:</td><td>7m44s</td></tr>


	<tr><td align="right">status refresh:</td><td>1m</td>


</tr></tbody></table>

<br>
<!-- user manager link. if user manager resides on other router, replace 192.168.88.10 by its address
<button onclick="document.location='http://192.168.88.10/user?subs='; return false;">status</button>
<!-- end of user manager link -->
<input type="submit" value="log off">

</form>
    """
