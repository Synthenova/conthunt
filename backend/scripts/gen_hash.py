
import hashlib

password = ""
username = "conthunt_service"
hashed = 'md5' + hashlib.md5((password + username).encode('utf-8')).hexdigest()
print(hashed)
