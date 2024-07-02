import requests

# Assuming color is a module or class defined elsewhere
class color:
    END = '\033[0m'
    BOLD = '\033[1m'

def EAAA():
    username = input(f'{color.END}{color.BOLD}[✦] Phone Number/Email/ID: ')
    if username == '0':
        return  # exit the function if the user types 0
    password = input(f'{color.END}{color.BOLD}[✦] Password: ')
    url = f"https://b-api.facebook.com/method/auth.login?format=json&device_id=0ksqyflb-tnnh-aaag-j5si-gqof920ps1lo&email={username}&password={password}&cpl=true&family_device_id=0ksqyflb-tnnh-aaag-j5si-gqof920ps1lo&sim_serials=%5B%2289014103310593510720%22%5D&credentials_type=password&error_detail_type=button_with_disabled&locale=en_US&client_country_code=US&method=auth.login&fb_api_req_friendly_name=authenticate&fb_api_caller_class=com.facebook.account.login.protocol.Fb4aAuthHandler&access_token=6628568379%7Cc1e620fa708a1d5696fb991c1bde5662"
    response = requests.get(url)
    responses = response.json()
    if 'access_token' in responses:
        print(responses['access_token'])
    else:
        print(responses['error_msg'])

if __name__ == "__main__":
    while True:  # loop indefinitely until user types 0
        EAAA()
        
