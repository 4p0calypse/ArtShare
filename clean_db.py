import os
import shutil
import redis
import sys
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_sirope():
    """Limpia la base de datos Sirope"""
    try:
        # Obtener la ruta absoluta del directorio data
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(base_dir, 'data')
        sirope_dir = os.path.join(data_dir, 'sirope')
        
        # Eliminar el directorio data si existe
        if os.path.exists(data_dir):
            logger.info(f"Eliminando directorio: {data_dir}")
            shutil.rmtree(data_dir)
            logger.info("Directorio data eliminado correctamente")
        else:
            logger.info("El directorio data no existe")
            
        # Crear el directorio sirope vacío
        os.makedirs(sirope_dir)
        logger.info(f"Creado nuevo directorio sirope en: {sirope_dir}")
        
    except Exception as e:
        logger.error(f"Error al limpiar Sirope: {e}")
        raise

def clean_redis():
    """Limpia Redis y la caché"""
    try:
        # Intentar conectar a Redis
        redis_client = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            socket_connect_timeout=1
        )
        
        # Verificar la conexión
        redis_client.ping()
        
        # Limpiar Redis
        redis_client.flushall()
        logger.info("Redis limpiado correctamente")
        
    except redis.ConnectionError:
        logger.warning("No se pudo conectar a Redis - puede que no esté instalado o no esté ejecutándose")
    except Exception as e:
        logger.error(f"Error al limpiar Redis: {e}")

def main():
    try:
        logger.info("Iniciando limpieza de la base de datos...")
        
        # Limpiar Sirope
        clean_sirope()
        
        # Limpiar Redis
        clean_redis()
        
        logger.info("¡Limpieza completada con éxito!")
        return 0
        
    except Exception as e:
        logger.error(f"Error durante la limpieza: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 