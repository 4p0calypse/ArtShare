from src.services.sirope_service import SiropeService
from src.auth.user_model import User

def main():
    sirope = SiropeService()
    users = sirope.find_all(User)
    print('\nUsuarios encontrados:')
    for u in users:
        print(f'ID: {u.id}, Username: {u.username}, Email: {u.email}, Created: {u.created_at}')

if __name__ == '__main__':
    main() 