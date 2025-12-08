# hash_password_tool.py

import bcrypt

def hash_password(plain_password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain_password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

if __name__ == "__main__":
    plain = input("비밀번호를 입력하세요: ")
    hashed = hash_password(plain)
    print(f"\n🔒 암호화된 비밀번호:\n{hashed}")
