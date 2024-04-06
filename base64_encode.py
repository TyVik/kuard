import base64
import json
import os
from dotenv import dotenv_values

ip_ssh = {"IP": """-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEAqS80auVwqOzQMKH7SKM5geCU/XSHrR9chbpLVPuD+qRqO2Fd
nUDwiMsBivdNxgOZg4bvCl6WisBFwaUEYGtNyfLHVMYrq4vMZJ6hAIojRRDv67k0
....
....
"""}

ip_ssh_json = json.dumps(ip_ssh)

encoded = base64.b64encode(ip_ssh_json.encode()).decode()

print(encoded)

with open('.env', 'a') as env_file:
   env_file.write(f'IP_SSH={encoded}')

