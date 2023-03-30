from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5, PKCS1_OAEP
import base64

from Crypto.Random import get_random_bytes
from django.conf import settings


class RsaEncrypt:
    def __init__(self, application):
        self.encryption_key = settings.RSA_ENCRYPTION_KEY[application]['PUBLIC']
        self.decryption_key = settings.RSA_ENCRYPTION_KEY[application]['PRIVATE']

    def rsa_encrypt_data(self, plain_text):
        """
        Method to encrypt string using RSA
        """
        public_key = RSA.import_key(self.encryption_key)
        cipher = PKCS1_v1_5.new(public_key)
        encrypted_message = cipher.encrypt(plain_text.encode("UTF-8"))
        encrypted_message_b64 = base64.b64encode(encrypted_message).decode("utf-8")
        return encrypted_message_b64

    def rsa_decrypt_data(self, encrypted_data):
        """
        Method to decrypt string using RSA
        """
        encrypted_message = base64.b64decode(encrypted_data)
        private_key = RSA.import_key(self.decryption_key)
        cipher = PKCS1_v1_5.new(private_key)
        decrypted_message = cipher.decrypt(encrypted_message, get_random_bytes(16), expected_pt_len=0)
        return decrypted_message.decode('utf-8')