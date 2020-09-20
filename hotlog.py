import argparse
import requests
import re
import hashlib
import binascii

def main():

    print("""
[+] *****************************************************************************************
[+] HotLog - Mikrotik Hotspot Login Script v1.0
[+] *****************************************************************************************
[+]""")
    args = get_args()

    # if list of credentials, then attempt for each one; else use args for '--username' and '--password'
    if args['credential_list'] is not None:
        credential_list = get_credential_list(args['credential_list'])
        for credentials in credential_list:
            success = login(args['target'], credentials[0], credentials[1])
            if success:
                break
    else:
        success = login(args['target'], args['username'], args['password'])


def login(target, username, password, check_logged_in=True):
    session = requests.Session()

    # get login page
    try:
        login_page = session.get(target)
        if login_page.status_code != 200:
            print(f'[!] Login page request at {target} returned a status code of {login_page.status_code}')
            return False

        # check and see if already logged in
        if check_logged_in:
            if re.search('Welcome', login_page.text) or re.search('logged in', login_page.text):
                print(f'[+] User is already logged in at {target}')
                exit(0)

        # get url of login page
        login_pattern = re.search('form name="sendin" action="(.*)" method="post"', login_page.text)
        if login_pattern is None:
            print(f'[!] Login page at {target} contained no URL for login post')
            return False
        login_url = login_pattern.group(1)

        # if salt values, exist then hash the password and submit
        # get salt values
        salt_pattern = re.search("hexMD5\((.*)\)", login_page.text)
        if salt_pattern is None:
            print(f'[*] Login page at {target} contained no salt values; attempting clear-text POST')
            post_data = {'username': username, 'password': password}

        else:
            print(f'[*] Login page at {target} contained salt values; attempting hashed POST')
            salt_values = [x.strip().replace('\'', '') for i, x in enumerate(salt_pattern.group(1).split('+')) if i % 2 == 0]

            # get hash of password
            salted_password = get_salt(salt_values[0]) + password.encode() + get_salt(salt_values[1])
            hashed_password = hashlib.md5(salted_password).hexdigest()

            # post username and hashed password to login url
            post_data = {'username': username, 'password': hashed_password }

        login_response = session.post(login_url, post_data)

        if login_response.status_code != 200:
            print(f'[!] Login page at {login_url} returned a status code of {login_response.status_code}')
            return False

        # look for welcome message to indicate successfully logged in
        if not re.search('Welcome', login_response.text) and not re.search('logged in', login_response.text):
            print(f'[!] Fail - Unsuccessful login attempt at {login_url} with credentials "{username}" and "{password}"')
            return False

    except Exception as ex:
        print(ex)
        return False

    # successfully logged in
    print(f'[+] Success - User successfully logged in at {target} with credentials "{username}" and "{password}"')
    return True


def get_args():
    """
    Get and validate command line arguments and return dictionary of those key/values
    :return:
    """
    ap = argparse.ArgumentParser()

    ap.add_argument("-t", "--target", required=False,
                    help="Target IP; defaults to 192.168.88.10")

    ap.add_argument("-u", "--username", required=False,
                    help="Username for login; defaults to 'admin'")

    ap.add_argument("-p", "--password", required=False,
                    help="Password for login; defaults to 'admin'")

    ap.add_argument("-c", "--credential-list", required=False,
                    help="File path to list of credentials")

    args = vars(ap.parse_args())
    # print(args)

    # target ip
    if args['target'] is None:
        args['target'] = 'http://192.168.88.10'

    # user name
    if args['username'] is None:
        args['username'] = 'admin'

    # password
    if args['password'] is None:
        args['password'] = 'admin'

    # credential list
    if args['credential_list'] is not None:
        pass

    return args

def get_salt(salt):
    hex_vals = [hex(int('0o' + x, 8)).replace('0x', '').zfill(2) for x in salt.split('\\') if x]
    unhex_vals = [binascii.unhexlify(x) for x in hex_vals]
    binary_salt = b''.join(unhex_vals)
    return binary_salt

def get_credential_list(credential_path):
    credential_list = []
    with open(credential_path, "r") as file:
        for line in file:
            credentials = line.strip()
            if credentials and ',' in credentials:
                credential_list.append(credentials.split(','))

    return credential_list




if __name__ == "__main__":
    main()

    """
    # post username and password

    # check if response code = 200 and successful login
    # <div style="color: #FF8080; font-size: 9px">invalid username or password</div>

    
    Password Hashing:
    <script type="text/javascript">
	<!--
	    function doLogin() {
		document.sendin.username.value = document.login.username.value;
		document.sendin.password.value = hexMD5('\305' + document.login.password.value + '\271\171\314\133\350\311\203\366\035\205\113\257\121\062\340\346');
		document.sendin.submit();
		return false;
	    }
	//-->
	</script>
    <form name="sendin" action="http://192.168.88.10/login" method="post">
		<input type="hidden" name="username">
		<input type="hidden" name="password">
		<input type="hidden" name="dst" value="http://192.168.88.1/">
		<input type="hidden" name="popup" value="true">
	</form>


	<form name="login" action="http://192.168.88.10/login" method="post" onsubmit="return doLogin()">
        <input type="hidden" name="dst" value="">
        <input type="hidden" name="popup" value="true">

            <table width="100" style="background-color: #ffffff">
                <tbody><tr><td align="right">login</td>
                        <td><input style="width: 80px" name="username" type="text" value="poop"></td>
                </tr>
                <tr><td align="right">password</td>
                        <td><input style="width: 80px" name="password" type="password"></td>
                </tr>
                <tr><td>&nbsp;</td>
                        <td><input type="submit" value="OK"></td>
                </tr>
            </tbody></table>
    </form>
    """
    ###########################################################################################################################

    """
    /status -> when logged in
    <div style="text-align: center;">Welcome user1!</div>

    logout:
    <script language="JavaScript">
    <!--

        function openLogout() {
        if (window.name != 'hotspot_status') return true;
            open('http://192.168.88.10/logout', 'hotspot_logout', 'toolbar=0,location=0,directories=0,status=0,menubars=0,resizable=1,width=280,height=250');
        window.close();
        return false;
        }
    //-->
    </script>
    <form action="http://192.168.88.10/logout" name="logout" onsubmit="return openLogout()">
        <br><div style="text-align: center;">Welcome user1!</div><br><table border="1" class="tabula">
            <tbody><tr><td align="right">IP address:</td><td>192.168.88.230</td></tr>
            <tr><td align="right">bytes up/down:</td><td>0 B / 0 B</td></tr>
            <tr><td align="right">connected:</td><td>1m1s</td></tr>
            <tr><td align="right">status refresh:</td><td>1m</td>
        </tr></tbody></table>
        <br>
        <!-- user manager link. if user manager resides on other router, replace 192.168.88.10 by its address
        <button onclick="document.location='http://192.168.88.10/user?subs='; return false;">status</button>
        <!-- end of user manager link -->
        <input type="submit" value="log off">
        </form>
    <input type="submit" value="log off">
    """
