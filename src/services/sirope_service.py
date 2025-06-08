import sirope
from typing import TypeVar, Type, Optional, List, Callable
import logging
import os
import pickle
import redis
import json

logger = logging.getLogger(__name__)
# Configurar el nivel de logging para ver todos los mensajes
logger.setLevel(logging.DEBUG)

T = TypeVar('T')

class SiropeService:
    _instance = None
    _sirope = None
    _redis = None
    _next_id_counter = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SiropeService, cls).__new__(cls)
            
            try:
                # Usar una ruta fija para desarrollo
                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                sirope_path = os.path.join(base_dir, 'data', 'sirope')
                logger.info(f"Usando ruta para Sirope: {sirope_path}")
                
                # Verificar si el directorio existe y es accesible
                if not os.path.exists(sirope_path):
                    logger.info(f"Creando directorio Sirope en: {sirope_path}")
                    os.makedirs(sirope_path, exist_ok=True)
                
                # Inicializar Redis
                redis_client = redis.Redis(
                    host='localhost',
                    port=6379,
                    db=0,
                    decode_responses=False  # Importante: debe ser False para que Sirope funcione correctamente
                )
                cls._redis = redis_client
                logger.info("Redis inicializado correctamente")
                
                # Inicializar Sirope
                cls._sirope = sirope.Sirope(sirope_path)
                # Asignar el cliente Redis a Sirope
                cls._sirope._redis = redis_client
                cls._objects = {}
                logger.info("Sirope inicializado correctamente")
                
                # Cargar contadores de IDs desde Redis o inicializar si no existen
                try:
                    counters = cls._redis.get('sirope:id_counters')
                    if counters:
                        cls._next_id_counter = json.loads(counters)
                    else:
                        cls._next_id_counter = {}
                except Exception as e:
                    logger.warning(f"Error al cargar contadores de Redis: {e}")
                    cls._next_id_counter = {}
                    
            except Exception as e:
                logger.error(f"Error al inicializar Sirope: {e}")
                logger.error(f"Detalles del error: {str(e)}")
                raise
        return cls._instance

    @property
    def sirope(self):
        if not self._sirope:
            raise RuntimeError("Sirope no está inicializado")
        return self._sirope

    def _ensure_sirope_initialized(self):
        """Asegura que Sirope está inicializado antes de cualquier operación"""
        if not self._sirope:
            raise RuntimeError("Sirope no está inicializado correctamente")

    def _get_class_key(self, cls: Type[T]) -> str:
        """Obtiene la clave para una clase"""
        return f"{cls.__module__}.{cls.__name__}"

    def _get_object_key(self, cls: Type[T], numeric_id: str) -> str:
        """Obtiene la clave para un objeto"""
        return f"{self._get_class_key(cls)}@{numeric_id}"

    def _extract_numeric_id(self, id_value: str) -> str:
        """Extrae el ID numérico de un ID completo"""
        if not id_value:
            return None
        return str(id_value).split('@')[-1] if '@' in str(id_value) else str(id_value)

    def _get_next_id(self, class_name: str) -> int:
        """Obtiene el siguiente ID para una clase"""
        try:
            if class_name not in self._next_id_counter:
                self._next_id_counter[class_name] = 0
            
            self._next_id_counter[class_name] += 1
            
            # Guardar el contador actualizado en Redis
            try:
                self._redis.set('sirope:id_counters', json.dumps(self._next_id_counter))
            except Exception as e:
                logger.warning(f"Error al guardar contador en Redis: {e}")
            
            return self._next_id_counter[class_name]
        except Exception as e:
            logger.error(f"Error al generar siguiente ID: {e}")
            raise

    def save(self, obj: T) -> T:
        """Guarda un objeto en la base de datos y retorna el objeto con su ID actualizado"""
        self._ensure_sirope_initialized()
        try:
            # Validar que el objeto no sea None
            if obj is None:
                raise ValueError("No se puede guardar un objeto None")

            # Generar un nuevo ID si el objeto no tiene uno
            if not hasattr(obj, '_id') or not obj._id:
                class_name = self._get_class_key(obj.__class__)
                new_id = str(self._get_next_id(class_name))
                obj._id = new_id
                if hasattr(obj, 'id'):
                    obj.id = new_id
            
            # Guardar en Sirope
            logger.info(f"Guardando objeto en Sirope: {obj}")
            self._sirope.save(obj)
            
            # Guardar en caché
            try:
                class_key = self._get_class_key(obj.__class__)
                self._objects.setdefault(class_key, {})[str(obj._id)] = obj
                cache_key = f"sirope:obj:{class_key}:{obj._id}"
                self._redis.set(cache_key, pickle.dumps(obj))
                logger.info(f"Objeto guardado en caché: {cache_key}")
            except Exception as cache_error:
                logger.warning(f"Error al guardar en caché: {cache_error}")
            
            return obj
            
        except Exception as e:
            logger.error(f"Error al guardar objeto: {str(e)}")
            raise

    def load(self, oid: str, cls: Type[T]) -> Optional[T]:
        """Carga un objeto por su ID y clase"""
        if not oid:
            logger.debug("Intentando cargar objeto con ID None")
            return None
            
        try:
            numeric_id = self._extract_numeric_id(oid)
            logger.info(f"Intentando cargar objeto de clase {cls.__name__} con ID numérico: {numeric_id}")
            
            # Usar filter para encontrar el objeto por ID
            def match_id(obj):
                if not hasattr(obj, 'id'):
                    return False
                obj_numeric_id = self._extract_numeric_id(obj.id)
                return obj_numeric_id == numeric_id
            
            matches = list(self._sirope.filter(cls, match_id))
            
            if not matches:
                logger.warning(f"No se encontró objeto con ID: {numeric_id}")
                return None
                
            obj = matches[0]
            logger.info(f"Objeto cargado exitosamente con ID: {obj.id}")
            return obj
        except Exception as e:
            logger.error(f"Error al cargar objeto con ID {oid}: {str(e)}")
            return None

    def delete(self, obj: T) -> bool:
        """Elimina un objeto de la base de datos y de Redis"""
        try:
            # Obtener el ID del objeto
            obj_id = None
            if hasattr(obj, '_id'):
                obj_id = obj._id
            elif hasattr(obj, 'id'):
                obj_id = obj.id
            
            if not obj_id:
                logger.error("No se puede eliminar un objeto sin ID")
                return False
            
            numeric_id = self._extract_numeric_id(obj_id)
            class_key = self._get_class_key(obj.__class__)
            
            # Asegurarnos de que el objeto tenga el ID correcto en formato Sirope
            if not hasattr(obj, '_id') or not obj._id or '@' not in obj._id:
                obj._id = f"{class_key}@{numeric_id}"
            
            success = True
            
            # 1. Eliminar de Sirope
            if hasattr(self._sirope, 'delete'):
                try:
                    self._sirope.delete(obj)
                    logger.info(f"Objeto eliminado de Sirope: {obj._id}")
                except Exception as sirope_error:
                    logger.error(f"Error al eliminar de Sirope: {sirope_error}")
                    success = False
            else:
                logger.error("El objeto Sirope no tiene método delete")
                success = False
            
            # 2. Eliminar de la caché en memoria
            try:
                if class_key in self._objects and numeric_id in self._objects[class_key]:
                    del self._objects[class_key][numeric_id]
                    logger.info(f"Objeto eliminado de la caché en memoria: {obj._id}")
            except Exception as cache_error:
                logger.warning(f"Error al eliminar de la caché en memoria: {cache_error}")
            
            # 3. Eliminar de Redis
            try:
                cache_key = f"sirope:obj:{class_key}:{numeric_id}"
                self._redis.delete(cache_key)
                logger.info(f"Objeto eliminado de Redis: {cache_key}")
            except Exception as redis_error:
                logger.warning(f"Error al eliminar de Redis: {redis_error}")
            
            return success
        
        except Exception as e:
            logger.error(f"Error al eliminar objeto: {str(e)}")
            return False

    def find_first(self, cls: Type[T], condition: Callable[[T], bool]) -> Optional[T]:
        """Encuentra el primer objeto que cumple una condición"""
        try:
            # Primero buscar en memoria
            class_key = self._get_class_key(cls)
            if class_key in self._objects:
                for obj in self._objects[class_key].values():
                    if condition(obj):
                        return obj
            
            # Si no se encuentra en memoria, buscar en Sirope
            try:
                all_objects = list(self._sirope.load_all(cls))
                for obj in all_objects:
                    # Guardar en memoria para futuros accesos
                    obj_numeric_id = self._extract_numeric_id(obj._id)
                    if class_key not in self._objects:
                        self._objects[class_key] = {}
                    self._objects[class_key][obj_numeric_id] = obj
                    if condition(obj):
                        return obj
            except Exception as e:
                logger.warning(f"Error al cargar objetos de Sirope: {e}")
            
            return None
        except Exception as e:
            logger.error(f"Error al buscar objeto: {str(e)}")
            return None

    def find_all(self, cls: Type[T], condition: Optional[Callable[[T], bool]] = None) -> List[T]:
        """Encuentra todos los objetos que cumplen una condición"""
        try:
            # Si no hay condición, usar un predicado que siempre devuelve True
            pred = condition if condition else lambda x: True
            
            # Cargar todos los objetos
            all_objects = []
            try:
                loaded_objects = list(self._sirope.load_all(cls))
                logger.info(f"Objetos cargados de Sirope: {len(loaded_objects)}")
                
                for obj in loaded_objects:
                    try:
                        # Verificar y corregir el ID
                        if hasattr(obj, '_id') and obj._id:
                            numeric_id = self._extract_numeric_id(obj._id)
                            if numeric_id:
                                obj._id = numeric_id
                                if hasattr(obj, 'id'):
                                    obj.id = numeric_id
                        
                        # Si es un usuario, verificar sus atributos
                        if cls.__name__ == 'User':
                            obj = self._ensure_user_attributes(obj)
                            if not obj:
                                logger.warning("Usuario descartado por atributos inválidos")
                                continue
                        
                        # Aplicar el predicado de filtrado
                        if pred(obj):
                            all_objects.append(obj)
                            
                    except Exception as obj_error:
                        logger.error(f"Error procesando objeto: {str(obj_error)}")
                        continue
                    
            except Exception as load_error:
                logger.error(f"Error cargando objetos de Sirope: {str(load_error)}")
            
            logger.info(f"Total objetos encontrados después de filtrar: {len(all_objects)}")
            return all_objects
            
        except Exception as e:
            logger.error(f"Error en find_all: {str(e)}")
            return []

    def find_by_id(self, id_value: str, cls: Type[T]) -> Optional[T]:
        """Busca un objeto por su ID"""
        try:
            if not id_value:
                logger.warning(f"ID inválido: {id_value}")
                return None

            logger.info(f"Buscando objeto con ID: {id_value}")
            
            # Intentar obtener de la memoria caché
            class_key = cls.__module__ + '.' + cls.__name__
            if class_key in self._objects and str(id_value) in self._objects[class_key]:
                obj = self._objects[class_key][str(id_value)]
                logger.info(f"Objeto encontrado en memoria: {obj}")
                return obj
            
            # Intentar obtener de Redis
            try:
                cache_key = f"sirope:obj:{class_key}:{id_value}"
                cached_data = self._redis.get(cache_key)
                if cached_data:
                    obj = pickle.loads(cached_data)
                    logger.info(f"Objeto encontrado en Redis: {obj}")
                    return obj
            except Exception as e:
                logger.warning(f"Error al buscar en Redis: {str(e)}")
            
            # Buscar en el almacenamiento persistente
            matches = self._sirope.filter(
                cls,
                lambda obj: (
                    isinstance(obj, cls) and 
                    str(getattr(obj, 'id', None)) == str(id_value)
                )
            )
            
            if matches:
                obj = matches[0]
                logger.info(f"Objeto encontrado en Sirope: {obj}")
                
                # Guardar en caché
                try:
                    self._objects.setdefault(class_key, {})[str(id_value)] = obj
                    cache_key = f"sirope:obj:{class_key}:{id_value}"
                    self._redis.set(cache_key, pickle.dumps(obj))
                except Exception as cache_error:
                    logger.warning(f"Error al guardar en caché: {cache_error}")
                
                return obj
                
            logger.warning(f"No se encontró objeto con ID: {id_value}")
            return None
            
        except Exception as e:
            logger.error(f"Error al buscar objeto con ID {id_value}: {str(e)}")
            return None

    def _ensure_user_attributes(self, user):
        """Asegura que un usuario tenga todos los atributos necesarios"""
        try:
            from werkzeug.security import generate_password_hash
            
            # Si el usuario no tiene los atributos básicos, no es válido
            if not hasattr(user, 'username') or not user.username:
                logger.error("Usuario sin username")
                return None
                
            # Asegurar password_hash
            if not hasattr(user, 'password_hash') or not user.password_hash:
                if user.username == 'root':
                    user.password_hash = generate_password_hash('root')
                else:
                    logger.error(f"Usuario {user.username} sin password_hash")
                    return None
            
            # Asegurar otros atributos
            if not hasattr(user, 'email'):
                user.email = f"{user.username}@example.com"
            if not hasattr(user, 'bio'):
                user.bio = ""
            if not hasattr(user, 'artworks'):
                user.artworks = []
            if not hasattr(user, 'followers'):
                user.followers = []
            user = self.save(user)
            if not hasattr(user, 'following'):
                user.following = []
            user = self.save(user)
            if not hasattr(user, 'points'):
                user.points = 0
            if not hasattr(user, 'created_at'):
                from datetime import datetime
                user.created_at = datetime.utcnow()
                
            logger.info(f"Atributos de usuario verificados y corregidos: {user.username}")
            logger.info(f"Estado de following: {user.following}")
            logger.info(f"Estado de followers: {user.followers}")
            
            return user
            
        except Exception as e:
            logger.error(f"Error al asegurar atributos de usuario: {str(e)}")
            return None

    def find_many_by_ids(self, ids: List[str], cls: Type[T]) -> List[T]:
        """Encuentra múltiples objetos por sus IDs"""
        if not ids:
            return []
        return [obj for obj in (self.find_by_id(id_value, cls) for id_value in ids) if obj is not None]

    def update(self, obj: T) -> bool:
        """Actualiza un objeto en la base de datos"""
        try:
            self.save(obj)
            return True
        except Exception as e:
            logger.error(f"Error al actualizar objeto: {str(e)}")
            return False

    def force_delete(self, obj: T) -> bool:
        """Elimina un objeto directamente usando el método delete de Sirope"""
        try:
            # Obtener el ID del objeto
            obj_id = None
            if hasattr(obj, '_id'):
                obj_id = obj._id
            elif hasattr(obj, 'id'):
                obj_id = obj.id
            
            if not obj_id:
                logger.error("No se puede eliminar un objeto sin ID")
                return False
            
            numeric_id = self._extract_numeric_id(obj_id)
            class_key = self._get_class_key(obj.__class__)
            
            success = True
            
            # 1. Eliminar de Redis
            try:
                # Eliminar solo la clave específica del objeto
                cache_key = f"sirope:obj:{class_key}:{numeric_id}"
                if self._redis.exists(cache_key):
                    self._redis.delete(cache_key)
                    logger.info(f"Objeto eliminado de Redis: {cache_key}")
            except Exception as redis_error:
                logger.warning(f"Error al eliminar de Redis: {redis_error}")
                success = False
            
            # 2. Eliminar de la memoria caché
            try:
                if class_key in self._objects:
                    if numeric_id in self._objects[class_key]:
                        del self._objects[class_key][numeric_id]
                        logger.info(f"Objeto eliminado de la memoria caché: {class_key}:{numeric_id}")
            except Exception as cache_error:
                logger.warning(f"Error al eliminar de la caché: {cache_error}")
                success = False
            
            # 3. Eliminar usando el método delete de Sirope
            try:
                # Asegurarnos de que el objeto tenga el ID correcto
                if not hasattr(obj, '_id') or not obj._id or '@' not in str(obj._id):
                    obj._id = f"{class_key}@{numeric_id}"
                
                # Intentar eliminar usando delete
                self._sirope.delete(obj)
                logger.info(f"Objeto eliminado usando delete: {obj}")
                
                # Verificar que el objeto fue eliminado
                deleted_obj = self.find_by_id(numeric_id, obj.__class__)
                if deleted_obj:
                    logger.error("El objeto aún existe después de intentar eliminarlo")
                    success = False
                
            except Exception as delete_error:
                logger.error(f"Error al eliminar usando delete: {delete_error}")
                success = False
            
            return success
            
        except Exception as e:
            logger.error(f"Error al forzar eliminación del objeto: {str(e)}")
            return False 