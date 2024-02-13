import hashlib
from Crypto.Cipher import AES
import base64
from django.conf import settings

from onyx_proj.exceptions.permission_validation_exception import InternalServerError


class AesEncryptDecrypt:
    def __init__(self, key: str = None, iv: str = None, mode=AES.MODE_ECB, block_size: int = 16):
        self.iv = None
        self.key = None
        self.mode = mode
        self.set_key(key, iv)
        self.block_size = block_size

    def pad(self, byte_array: bytearray):
        """
        pkcs5 padding
        """
        pad_len = self.block_size - len(byte_array) % self.block_size
        return byte_array + (bytes([pad_len]) * pad_len)

    # pkcs5 - unpadding
    def unpad(self, byte_array: bytearray):
        return byte_array[:-ord(byte_array[-1:])]

    def set_key(self, key: str, iv: str):
        if self.mode == AES.MODE_CBC:
            self.key = key.encode("utf-8")
            self.iv = iv.encode("utf-8")
        elif self.mode == AES.MODE_ECB:
            # convert to bytes
            key = key.encode('utf-8')
            # get the sha1 method - for hashings
            sha1 = hashlib.sha1
            # and use digest and take the last 16 bytes
            key = sha1(key).digest()[:16]
            # now zero pad - just incase
            key = key.zfill(16)
            self.key = key
        else:
            raise InternalServerError(reason="Unable to set encryption keys due to invalid mode.")

    def encrypt(self, message: str) -> str:
        # convert to bytes
        byte_array = message.encode("UTF-8")
        # pad the message - with pkcs5 style
        padded = self.pad(byte_array)
        # new instance of AES with encoded key
        cipher = AES.new(self.key, AES.MODE_ECB)
        # now encrypt the padded bytes
        encrypted = cipher.encrypt(padded)
        # base64 encode and convert back to string
        return base64.b64encode(encrypted).decode('utf-8')

    def decrypt(self, message: str) -> str:
        # convert the message to bytes
        byte_array = message.encode("utf-8")
        # base64 decode
        message = base64.b64decode(byte_array)
        # AES instance with the - setKey()
        cipher = AES.new(self.key, AES.MODE_ECB)
        # decrypt and decode
        decrypted = cipher.decrypt(message).decode('utf-8')
        # unpad - with pkcs5 style and return
        return self.unpad(decrypted)

    def decrypt_str_with_missing_padding(self, message: str) -> str:
        # convert the message to bytes
        message += "=" * ((self.block_size - len(message) % self.block_size) % self.block_size)
        byte_array = message.encode("utf-8")
        # base64 decode
        try:
            message = base64.b64decode(byte_array)
        except Exception as e:
            message = base64.urlsafe_b64decode(byte_array)
        # AES instance with the - setKey()
        cipher = AES.new(self.key, AES.MODE_ECB)
        # decrypt and decode
        decrypted = cipher.decrypt(message).decode('utf-8')
        # unpad - with pkcs5 style and return
        return self.unpad(decrypted)

    def encrypt_aes_cbc(self, plain_text: str) -> str:
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        padded_plaintext = self.pad_cbc(plain_text)
        ciphertext = cipher.encrypt(padded_plaintext)
        return base64.b64encode(ciphertext).decode("utf-8")

    def pad_cbc(self, plain_text: str) -> bytes:
        padding_len = self.block_size - len(plain_text) % self.block_size
        padding = bytes([padding_len]) * padding_len
        return bytes(plain_text, "utf-8") + padding

    def decrypt_aes_cbc(self, encrypted_text: str) -> str:
        from Crypto.Util.Padding import unpad
        encrypted_text = encrypted_text.encode("utf-8")
        encrypted_text = base64.b64decode(encrypted_text)
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        decrypted_text = unpad(cipher.decrypt(encrypted_text), block_size=self.block_size)
        return decrypted_text.decode("utf-8")
