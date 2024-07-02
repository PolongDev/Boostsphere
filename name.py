import requests
import json
import os
import re


def load_data():
    try:
        with open('data.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"accounts": [], "access_tokens": []}
    except json.decoder.JSONDecodeError:
        return {"accounts": [], "access_tokens": []}

def save_data(data):
    print("Saving data:", data)  # Add this line for debugging
    with open('data.json', 'w') as f:
        if isinstance(data, dict):
            json.dump(data, f, indent=4)
        else:
            json.dump({"access_tokens": data}, f, indent=4)

def count_accounts_and_pages(data):
    if isinstance(data, list):
        access_tokens = data
    else:
        access_tokens = data.get("access_tokens", [])
    
    total_accounts = len(access_tokens)
    total_pages = sum(len(token.get("pages", [])) for token in access_tokens)
    
    return total_accounts, total_pages

def add_token():
    data = load_data()
    
    if isinstance(data, list):
        access_tokens = data
    else:
        access_tokens = data.get("access_tokens", [])
    
    while True:
        access_token = input('Enter your access token (if done just leave this blank): ')
        if not access_token:
            save_data(data)  # Save the updated data structure
            main()  # Return to the main menu
            break
        
        
        # Check if the token already exists
        if any(token.get("access_token") == access_token for token in access_tokens):
            print("Token already exists.")
            continue

        # Verify the token
        try:
            response = requests.get(f'https://graph.facebook.com/me?access_token={access_token}')
            if response.status_code == 200:
                is_valid_token = True
                # Extract pages belonging to this account
                pages_response = requests.get(f'https://graph.facebook.com/me/accounts?access_token={access_token}')
                if pages_response.status_code == 200:
                    pages_data = pages_response.json().get("data", [])
                    # Separate pages from account data
                    account_data = {"access_token": access_token}
                    account_pages = [page for page in pages_data]
                    account_data["pages"] = account_pages
                    access_tokens.append(account_data)
                    if isinstance(data, list):
                        data = access_tokens  # Update data if it was initially a list
                    else:
                        data["access_tokens"] = access_tokens  # Update the access_tokens in the data structure
                        
                    print("\033[91mSuccessfully added Account\033[0m")  # Successfully added message in red
            else:
                is_valid_token = False
        except requests.exceptions.RequestException:
            is_valid_token = False

        if not is_valid_token:
            print("Invalid token. Please enter a valid token.")

        # Add this line for debugging
        save_data(data)
def extract_ids(url):
    group_pattern = r'groups/(\d+)/permalink/(\d+)/'
    post_pattern = r'(\d+)/posts/(\d+)/'
    photo_pattern = r'fbid=(\d+)'

    group_match = re.search(group_pattern, url)
    post_match = re.search(post_pattern, url)
    photo_match = re.search(photo_pattern, url)

    if group_match:
        group_id, post_id = group_match.groups()
        return f"{group_id}_{post_id}"
    elif post_match:
        group_id, post_id = post_match.groups()
        return f"{group_id}_{post_id}"
    elif photo_match:
        photo_id = photo_match.group(1)
        return photo_id
    else:
        return None 
def has_reacted(post_id, access_token):
    try:
        url = f'https://graph.facebook.com/v18.0/{post_id}/reactions'
        params = {'access_token': access_token}
        response = requests.get(url, params=params)
        response.raise_for_status()
        reactions = response.json().get('data', [])
        
        # Get the id of the user/page associated with the access token
        user_info = requests.get('https://graph.facebook.com/me', params={'access_token': access_token}).json()
        user_id = user_info.get('id', '')
        
        for reaction in reactions:
            if reaction.get('id') == user_id:
                return True
        
    except requests.exceptions.RequestException as error:
        print(f"\033[1;91m[EXCEPTION]\033[0;1m {error}\033[0m")
    
    return False

def has_commented(post_id, access_token):
    try:
        url = f'https://graph.facebook.com/v18.0/{post_id}/comments'
        params = {'access_token': access_token}
        response = requests.get(url, params=params)
        response.raise_for_status()
        comments = response.json().get('data', [])
        
        # Get the id of the user/page associated with the access token
        user_info = requests.get('https://graph.facebook.com/me', params={'access_token': access_token}).json()
        user_id = user_info.get('id', '')
        
        for comment in comments:
            if comment.get('from', {}).get('id') == user_id:
                return True
        
    except requests.exceptions.RequestException as error:
        print(f"\033[1;91m[EXCEPTION]\033[0;1m {error}\033[0m")
    
    return False


def perform_reaction(post_id, reaction_type, reactor_type, num_reactions):
    access_tokens_data = load_data()
    access_tokens = access_tokens_data if isinstance(access_tokens_data, list) else access_tokens_data.get("access_tokens", [])
    
    reactions_count = 0

    for token_info in access_tokens:
        access_token = token_info.get("access_token", "") if isinstance(token_info, dict) else token_info
        try:
            if access_token.startswith("EA") or access_token.startswith("EAA"):
                if reactor_type == "PAGE":
                    # Use only pages as reactors
                    response = requests.get(f'https://graph.facebook.com/me/accounts', headers={'Authorization': f'Bearer {access_token}'}).json()
                    
                    for page in response.get('data', []):
                        page_access_token = page.get('access_token', '')
                        page_name = page.get('name', '')
                        try:
                            if not has_reacted(post_id, page_access_token):
                                url = f'https://graph.facebook.com/v18.0/{post_id}/reactions'
                                params = {'access_token': page_access_token, 'type': reaction_type}
                                response = requests.post(url, params=params)
                                
                                if response.status_code == 200:
                                    reactions_count += 1
                                    print("\033[0m\033[1m[\033[91mSUCCESS\033[0m\033[1m] SUCCESSFULLY REACTION |\033[91m {}\033[0m \033[1m|\033[91m {}\033[0m \033[1m|\033[90m {}\033[0m".format(page_name, post_id, str(response.json())))
                                    if reactions_count >= num_reactions:
                                        print("Reached the limit of {} reactions.".format(num_reactions))
                                        return
                                else:
                                    print("\033[1;91m[ERROR]\033[0;1m FAILED TO POST REACTION | \033[91m{}\033[0m".format(post_id))
                        except requests.exceptions.RequestException as error:
                            print("\033[1;91m[EXCEPTION]\033[0;1m {}\033[0m".format(error))
                        
                elif reactor_type == "ACCOUNT":
                    # Use only accounts as reactors
                    try:
                        if not has_reacted(post_id, access_token):
                            url = f'https://graph.facebook.com/v18.0/{post_id}/reactions'
                            params = {'access_token': access_token, 'type': reaction_type}
                            response = requests.post(url, params=params)
                            
                            if response.status_code == 200:
                                reactions_count += 1
                                print("\033[0m\033[1m[\033[91mSUCCESS\033[0m\033[1m] SUCCESSFULLY REACTED |\033[91m Personal Profile\033[0m \033[1m|\033[91m {}\033[0m \033[1m|\033[90m {}\033[0m".format(post_id, str(response.json())))
                                if reactions_count >= num_reactions:
                                    print("Reached the limit of {} reactions.".format(num_reactions))
                                    return
                            else:
                                print("\033[1;91m[ERROR]\033[0;1m FAILED TO POST REACTION | \033[91m{}\033[0m".format(post_id))
                    except requests.exceptions.RequestException as error:
                        print("\033[1;91m[EXCEPTION]\033[0;1m {}\033[0m".format(error))
                    
                elif reactor_type == "BOTH":
                    # Use both pages and accounts as reactors
                    try:
                        if not has_reacted(post_id, access_token):
                            url = f'https://graph.facebook.com/v18.0/{post_id}/reactions'
                            params = {'access_token': access_token, 'type': reaction_type}
                            response = requests.post(url, params=params)
                            
                            if response.status_code == 200:
                                reactions_count += 1
                                print("\033[0m\033[1m[\033[91mSUCCESS\033[0m\033[1m] SUCCESSFULLY REACTED |\033[91m Personal Profile\033[0m \033[1m|\033[91m {}\033[0m \033[1m|\033[90m {}\033[0m".format(post_id, str(response.json())))
                                if reactions_count >= num_reactions:
                                    print("Reached the limit of {} reactions.".format(num_reactions))
                                    return
                            else:
                                print("\033[1;91m[ERROR]\033[0;1m FAILED TO POST REACTION | \033[91m{}\033[0m".format(post_id))
                    except requests.exceptions.RequestException as error:
                        print("\033[1;91m[EXCEPTION]\033[0;1m {}\033[0m".format(error))
            else:
                print("\033[1;91m[ERROR]\033[0;1m Invalid access token format\033[0m")
        except requests.exceptions.RequestException as error:
            print("\033[1;91m[EXCEPTION]\033[0;1m {}\033[0m".format(error))
def extract_facebook_id(url):
    # Define the regular expression pattern to match the Facebook URL format
    pattern = r'https?://(?:www\.)?facebook\.com/([0-9]+)'
    
    # Use re.match to find the pattern in the URL
    match = re.match(pattern, url)
    
    # If a match is found, return the extracted ID
    if match:
        return match.group(1)
    else:
        return None 
def auto_follow(fb_user_id, num_followers):
    # Load access tokens from data.json
    data = load_data()
    access_tokens = data.get("access_tokens", [])

    # Iterate through each access token
    for access_token_info in access_tokens:
        access_token = access_token_info.get("access_token", "")
        
        # Make sure access token is not empty
        if access_token:
            headers = {'Authorization': f'Bearer {access_token}'}
            
            try:
                # Get the list of accounts/pages associated with the user
                response = requests.get('https://graph.facebook.com/v18.0/me/accounts', headers=headers)
                pages_data = response.json().get('data', [])

                # Loop through the pages/accounts
                for page in pages_data:
                    page_access_token = page.get('access_token', '')

                    # Make sure the page access token is valid
                    if page_access_token:
                        try:
                            # Subscribe to (follow) the specified Facebook user ID
                            response = requests.post(f'https://graph.facebook.com/v18.0/{fb_user_id}/subscribers', headers={'Authorization': f'Bearer {page_access_token}'})
                            if response.status_code == 200:
                                print(f"Successfully followed user ID {fb_user_id} with account {page['name']}")
                                num_followers -= 1
                                if num_followers <= 0:
                                    print("Reached the limit of followers to follow.")
                                    return
                            else:
                                print(f"Failed to follow user ID {fb_user_id} with account {page['name']}. Error: {response.json()}")
                        except requests.exceptions.RequestException as error:
                            print(f"Exception occurred: {error}")
            except requests.exceptions.RequestException as error:
                print(f"Exception occurred: {error}")



def comment_on_post(post_id, comment_text, commentator_type=None, num_comments=1):
    access_tokens_data = load_data()
    access_tokens = access_tokens_data if isinstance(access_tokens_data, list) else access_tokens_data.get("access_tokens", [])
    
    # Ask user for commentator type if it's not provided
    if not commentator_type:
        commentator_type = input('Enter the commentator type (BOTH, PAGE, ACCOUNT): ').upper()
    
    comments_count = 0

    for token_info in access_tokens:
        access_token = token_info.get("access_token", "") if isinstance(token_info, dict) else token_info
        try:
            if access_token.startswith("EA") or access_token.startswith("EAA"):
                if commentator_type == "PAGE":
                    # Use only pages as commentators
                    response = requests.get(f'https://graph.facebook.com/me/accounts', headers={'Authorization': f'Bearer {access_token}'}).json()
                    
                    for page in response.get('data', []):
                        page_access_token = page.get('access_token', '')
                        page_name = page.get('name', '')
                        try:
                            if not has_commented(post_id, page_access_token):
                                url = f'https://graph.facebook.com/v18.0/{post_id}/comments'
                                params = {'access_token': page_access_token, 'message': comment_text}
                                response = requests.post(url, params=params)
                                
                                if response.status_code == 200:
                                    comments_count += 1
                                    print("\033[0m\033[1m[\033[91mSUCCESS\033[0m\033[1m] Successfully commented on post | {}\033[0m".format(post_id))
                                    if comments_count >= num_comments:
                                        print("Reached the limit of {} comments.".format(num_comments))
                                        return
                                else:
                                    print("\033[1;91m[ERROR]\033[0;1m Failed to comment on post | {}\033[0m".format(post_id))
                        except requests.exceptions.RequestException as error:
                            print("\033[1;91m[EXCEPTION]\033[0;1m {}\033[0m".format(error))
                
                elif commentator_type == "ACCOUNT":
                    # Use only accounts as commentators
                    try:
                        if not has_commented(post_id, access_token):
                            url = f'https://graph.facebook.com/v18.0/{post_id}/comments'
                            params = {'access_token': access_token, 'message': comment_text}
                            response = requests.post(url, params=params)
                            
                            if response.status_code == 200:
                                comments_count += 1
                                print("\033[0m\033[1m[\033[91mSUCCESS\033[0m\033[1m] Successfully commented on post | {}\033[0m".format(post_id))
                                if comments_count >= num_comments:
                                    print("Reached the limit of {} comments.".format(num_comments))
                                    return
                            else:
                                print("\033[1;91m[ERROR]\033[0;1m Failed to comment on post | {}\033[0m".format(post_id))
                    except requests.exceptions.RequestException as error:
                        print("\033[1;91m[EXCEPTION]\033[0;1m {}\033[0m".format(error))
                
                elif commentator_type == "BOTH":
                    # Use both pages and accounts as commentators
                    response = requests.get(f'https://graph.facebook.com/me/accounts', headers={'Authorization': f'Bearer {access_token}'}).json()
                    
                    for page in response.get('data', []):
                        page_access_token = page.get('access_token', '')
                        page_name = page.get('name', '')
                        try:
                            if not has_commented(post_id, page_access_token):
                                url = f'https://graph.facebook.com/v18.0/{post_id}/comments'
                                params = {'access_token': page_access_token, 'message': comment_text}
                                response = requests.post(url, params=params)
                                
                                if response.status_code == 200:
                                    comments_count += 1
                                    print("\033[0m\033[1m[\033[91mSUCCESS\033[0m\033[1m] Successfully commented on post | {}\033[0m".format(post_id))
                                    if comments_count >= num_comments:
                                        print("Reached the limit of {} comments.".format(num_comments))
                                        return
                                else:
                                    print("\033[1;91m[ERROR]\033[0;1m Failed to comment on post | {}\033[0m".format(post_id))
                        except requests.exceptions.RequestException as error:
                            print("\033[1;91m[EXCEPTION]\033[0;1m {}\033[0m".format(error))
                    
                    try:
                        if not has_commented(post_id, access_token):
                            url = f'https://graph.facebook.com/v18.0/{post_id}/comments'
                            params = {'access_token': access_token, 'message': comment_text}
                            response = requests.post(url, params=params)
                            
                            if response.status_code == 200:
                                comments_count += 1
                                print("\033[0m\033[1m[\033[91mSUCCESS\033[0m\033[1m] Successfully commented on post | {}\033[0m".format(post_id))
                                if comments_count >= num_comments:
                                    print("Reached the limit of {} comments.".format(num_comments))
                                    return
                            else:
                                print("\033[1;91m[ERROR]\033[0;1m Failed to comment on post | {}\033[0m".format(post_id))
                    except requests.exceptions.RequestException as error:
                        print("\033[1;91m[EXCEPTION]\033[0;1m {}\033[0m".format(error))
            
            else:
                print("\033[1;91m[ERROR]\033[0;1m Invalid access token format\033[0m")
        except requests.exceptions.RequestException as error:
                        print("\033[1;91m[EXCEPTION]\033[0;1m {}\033[0m".format(error))
            
def auto_react_to_reels(reels_link, reaction_type, num_reactions):
    # Load access tokens from the data file
    access_tokens_data = load_data()
    access_tokens = access_tokens_data if isinstance(access_tokens_data, list) else access_tokens_data.get("access_tokens", [])
    
    # Iterate over each access token
    for token_info in access_tokens:
        access_token = token_info.get("access_token", "") if isinstance(token_info, dict) else token_info
        try:
            # Check if the access token is valid
            if access_token.startswith("EA") or access_token.startswith("EAA"):
                # Perform the auto reaction
                url = f'https://graph.facebook.com/v13.0/{reels_link}/reactions'
                params = {'access_token': access_token, 'type': reaction_type}
                for _ in range(num_reactions):
                    response = requests.post(url, params=params)
                    if response.status_code == 200:
                        print("Successfully reacted to reels.")
                    else:
                        print("Failed to react to reels.")
                        print(response.json())
            else:
                print("Invalid access token format.")
        except requests.exceptions.RequestException as error:
            print("Exception occurred:", error)
def auto_reply_to_comment(post_id, comment_id, reply_text, bot_types, num_bots):
    # Load access tokens from the data file
    access_tokens_data = load_data()
    access_tokens = access_tokens_data if isinstance(access_tokens_data, list) else access_tokens_data.get("access_tokens", [])
    
    # Iterate over each access token
    for token_info in access_tokens:
        access_token = token_info.get("access_token", "") if isinstance(token_info, dict) else token_info
        try:
            # Check if the access token is valid
            if access_token.startswith("EA") or access_token.startswith("EAA"):
                # Determine which bot types to use
                if "ACCOUNT" in bot_types and "PAGE" in bot_types:
                    bots_to_use = ["ACCOUNT", "PAGE"]
                elif "ACCOUNT" in bot_types:
                    bots_to_use = ["ACCOUNT"]
                elif "PAGE" in bot_types:
                    bots_to_use = ["PAGE"]
                else:
                    print("Invalid bot types. Please choose between ACCOUNT, PAGE, or BOTH.")
                    return
                
                # Perform auto reply with each bot type
                for bot_type in bots_to_use:
                    url = f'https://graph.facebook.com/v13.0/{post_id}_{comment_id}/comments'
                    params = {'access_token': access_token, 'message': reply_text}
                    for _ in range(num_bots):
                        response = requests.post(url, params=params)
                        if response.status_code == 200:
                            print(f"Successfully replied to comment with {bot_type} bot.")
                        else:
                            print(f"Failed to reply to comment with {bot_type} bot.")
                            print(response.json())
            else:
                print("Invalid access token format.")
        except requests.exceptions.RequestException as error:
            print("Exception occurred:", error)
            

def auto_group_join(group_id, bot_types, num_bots):
    data = load_data()
    access_tokens = data.get("access_tokens", [])
    
    bot_types = [bot_type.upper() for bot_type in bot_types]
    
    def join_group(group_id, bot_ids, access_token):
        for bot_id in bot_ids:
            url = f'https://graph.facebook.com/{group_id}/members/{bot_id}'
            params = {'access_token': access_token}
            response = requests.post(url, params=params)
            if response.status_code == 200:
                print(f"Bot with ID {bot_id} joined the group successfully.")
            else:
                print(f"Failed to join the group with bot ID {bot_id}. Status code: {response.status_code}, Response: {response.text}")

    for token_info in access_tokens:
        access_token = token_info.get("access_token", "")
        try:
            if access_token.startswith("EA") or access_token.startswith("EAA"):
                response = requests.get(f'https://graph.facebook.com/{group_id}/members', params={'access_token': access_token}).json()
                available_bots = response.get('data', [])
                
                if len(available_bots) < num_bots:
                    print(f"Not enough bots available to join {num_bots} bots to the group.")
                    continue
                
                if "BOTH" in bot_types:
                    half_num_bots = num_bots // 2
                    page_ids = [bot['id'] for bot in available_bots[:half_num_bots]]
                    account_ids = [bot['id'] for bot in available_bots[half_num_bots:num_bots]]
                    join_group(group_id, page_ids, access_token)
                    join_group(group_id, account_ids, access_token)
                elif "PAGE" in bot_types or "ACCOUNT" in bot_types:
                    bot_ids = [bot['id'] for bot in available_bots[:num_bots]]
                    join_group(group_id, bot_ids, access_token)
            else:
                print("[ERROR] Invalid access token format")
        except requests.exceptions.RequestException as error:
            print(f"[EXCEPTION] {error}")


def display_menu():


    print("\033[97m" + """
██████╗  ██████╗  ██████╗ ███████╗████████╗███████╗██████╗ ██╗  ██╗███████╗██████╗ ███████╗
██╔══██╗██╔═══██╗██╔═══██╗██╔════╝╚══██╔══╝██╔════╝██╔══██╗██║  ██║██╔════╝██╔══██╗██╔════╝
██████╔╝██║   ██║██║   ██║███████╗   ██║   ███████╗██████╔╝███████║█████╗  ██████╔╝█████╗  
██╔══██╗██║   ██║██║   ██║╚════██║   ██║   ╚════██║██╔═══╝ ██╔══██║██╔══╝  ██╔══██╗██╔══╝  
██████╔╝╚██████╔╝╚██████╔╝███████║   ██║   ███████║██║     ██║  ██║███████╗██║  ██║███████╗
╚═════╝  ╚═════╝  ╚═════╝ ╚══════╝   ╚═╝   ╚══════╝╚═╝     ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚══════╝
""")
    print("\033[91m                      Created By : PolongDev                                            \033[0m")
     
    data = load_data()
    total_accounts, total_pages = count_accounts_and_pages(data)
    print(f"Total Accounts: {total_accounts}")
    print(f"Total Pages: {total_pages}")

    
    print("\n╔════════════════════════════════════════╗")
    print("║   [1] Add Account(Token only)          ║") 
    print("║   [2] Send Reaction to Link            ║")
    print("║   [3] Auto Comment                     ║")
    print("║   [4] Auto Follow                      ║")
    print("║   [5] Auto React To Reels              ║")
    print("║   [6] Auto Reply Comment               ║")
    print("║   [7] Auto Group Join                  ║")
    print("║   [8] Like & Follow Page               ║")
    print("║   [9] Auto Create Page (500 limit)     ║")
    print("║  [10] Auto Create Account              ║")
    print("╚════════════════════════════════════════╝")


display_menu()



def main():
    while True:
        display_menu()
        choice = input("\nSelect an option (0 to return to main menu): ")
        
        if choice == "0":
            continue  # Go back to the main menu
        
        elif choice == "1":
            while True:
                add_token()
                back_to_menu = input("Press 0 to return to the main menu(ENTER AGAIN IF YOU WANT TO CONTINUE): ")
                if back_to_menu == "0":
                    break
       
        elif choice == '2':
            post_id = input('Enter the post ID: ')
            extracted = extract_ids(post_id)
            reaction_type = input('Enter the reaction type: ')
            reactor_type = input('Enter the reactor type (BOTH, PAGE, ACCOUNT): ').upper()
            num_reactions = int(input('Enter the number of reactions to perform: '))
            perform_reaction(extracted, reaction_type, reactor_type, num_reactions)
            back_to_menu = input("Press 0 to return to the main menu(ENTER AGAIN IF YOU WANT TO CONTINUE): ")
              
            if back_to_menu == "0":
                    break
    
    

        elif choice == '3':
            post_id = input('Enter the post ID: ')
            extracted = extract_ids(post_id)
            comment_text = input('Enter your comment: ')
            commentator_type = input('Enter the commentator type (BOTH, PAGE, ACCOUNT): ').upper()
            num_comments = int(input('Enter the number of comments to make: '))
            comment_on_post(extracted, comment_text, commentator_type, num_comments)
            back_to_menu = input("Press 0 to return to the main menu (ENTER AGAIN IF YOU WANT TO CONTINUE): ")
            if back_to_menu == "0":
                    break
              
        elif choice == '4':
            fb_user_id = input('Enter the Facebook user ID to follow: ')
            extracted_fbid = extract_facebook_id(fb_user_id)
            num_followers = int(input('Enter the number of followers desired: '))
            auto_follow(extracted_fbid, num_followers)
            back_to_menu = input("Press 0 to return to the main menu (ENTER AGAIN IF YOU WANT TO CONTINUE): ")
            if back_to_menu == "0":
                break
        
        elif choice == '5':
            reels_link = input('Enter the reels link: ')
            reaction_type = input('Enter the reaction type: ')
            num_reactions = int(input('Enter the number of reactions to reels: '))
            auto_react_to_reels(reels_link, reaction_type, num_reactions)
            back_to_menu = input("Press 0 to return to the main menu (ENTER AGAIN IF YOU WANT TO CONTINUE): ")
            if back_to_menu == "0":
                break
        
        elif choice == '6':
            post_id = input('Enter the post ID: ')
            comment_id = input('Enter the comment ID: ')
            reply_text = input('Enter the reply text: ')
            bot_types = input('Enter bot types (comma-separated, e.g., ACCOUNT,PAGE): ').upper().split(',')
            num_bots = int(input('Enter the number of bots to use: '))
            auto_reply_to_comment(post_id, comment_id, reply_text, bot_types, num_bots)
            back_to_menu = input("Press 0 to return to the main menu (ENTER AGAIN IF YOU WANT TO CONTINUE): ")
            if back_to_menu == "0":
                break
        elif choice == '7':
            group_id = input('Enter the Facebook group ID: ')
            bot_types = input('Enter the bot types (ACCOUNT, PAGE, BOTH): ').split(',')
            num_bots = int(input('Enter the number of bots to join: '))
            auto_group_join(group_id, bot_types, num_bots)
        
        else: 
        
        
            print("Invalid option. Please try again.")

if __name__ == "__main__":
    main()
