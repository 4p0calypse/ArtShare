from src.services.sirope_service import SiropeService
from src.auth.user_model import User

def main():
    sirope = SiropeService()
    users = sirope.find_all(User)
    
    # Agrupar usuarios por ID
    users_by_id = {}
    for user in users:
        if user.id not in users_by_id:
            users_by_id[user.id] = []
        users_by_id[user.id].append(user)
    
    # Para cada ID, mantener solo el primer usuario y eliminar los duplicados
    for user_id, user_list in users_by_id.items():
        if len(user_list) > 1:
            print(f"\nEncontrados {len(user_list)} usuarios con ID {user_id}")
            print(f"Manteniendo: Username: {user_list[0].username}, Email: {user_list[0].email}")
            
            # Eliminar duplicados (todos excepto el primero)
            for duplicate in user_list[1:]:
                print(f"Eliminando duplicado: Username: {duplicate.username}, Email: {duplicate.email}")
                sirope.force_delete(duplicate)

    # Verificar usuarios restantes
    remaining_users = sirope.find_all(User)
    print("\nUsuarios después de la limpieza:")
    for user in remaining_users:
        print(f"ID: {user.id}, Username: {user.username}, Email: {user.email}")

if __name__ == '__main__':
    main() 