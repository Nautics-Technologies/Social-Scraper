import sys
import time
import ssl
from instagram_private_api import Client as AppClient, ClientError

ssl._create_default_https_context = ssl._create_unverified_context

class Osintgram:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.api = None

    def login(self):
        try:
            self.api = AppClient(self.username, self.password, auto_patch=True)
        except ClientError as e:
            print(f'Login error: {e}')
            sys.exit(1)

    def get_user_contact_info(self, username):
        try:
            user_info = self.api.username_info(username)
            user = user_info['user']
            email = user.get('public_email', '')
            phone_number = user.get('contact_phone_number', '')
            return email, phone_number
        except ClientError as e:
            print(f'Error fetching contact info for user {username}: {e}')
            return '', ''
