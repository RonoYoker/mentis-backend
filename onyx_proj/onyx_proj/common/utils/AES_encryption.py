import hashlib
from Crypto.Cipher import AES
import base64


class AesEncryptDecrypt:
    def __init__(self, key: str, mode: AES.MODE_ECB = AES.MODE_ECB, block_size: int = 16):
        self.key = self.setKey(key)
        self.mode = mode
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

    def setKey(self, key: str):
        # convert to bytes
        key = key.encode('utf-8')
        # get the sha1 method - for hashings
        sha1 = hashlib.sha1
        # and use digest and take the last 16 bytes
        key = sha1(key).digest()[:16]
        # now zero pad - just incase
        key = key.zfill(16)
        return key

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


# if __name__ == '__main__':
#     # message to encrypt
#     message = 'hello world'
#     secret_key = "prodcenter$123@123 - Prod"
#     AES_pkcs5_obj = encrypt_decrypt(secret_key)
#
#     encrypted_message = AES_pkcs5_obj.encrypt(message)
#
#     print(encrypted_message)
#     decrypted_message = AES_pkcs5_obj.decrypt(encrypted_message)
#     print(decrypted_message)
