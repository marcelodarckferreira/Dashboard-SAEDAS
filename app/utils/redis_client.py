import redis
import pickle
import os
import json
import zlib
from typing import Any, Optional
import pandas as pd
from decouple import config

class RedisClient:
    """
    Cliente Redis Singleton para gerenciamento de cache no SAEDAS.
    Implementa serialização de DataFrames e objetos genéricos.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisClient, cls).__new__(cls)
            cls._instance._init_connection()
        return cls._instance

    def _init_connection(self):
        """Inicializa a conexão com o Redis usando variáveis de ambiente."""
        try:
            self.host = config("REDIS_HOST", default="redis")
            self.port = config("REDIS_PORT", default=6379, cast=int)
            self.password = config("REDIS_PASSWORD", default=None)
            self.db = config("REDIS_DB", default=0, cast=int)

            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                password=self.password,
                db=self.db,
                socket_timeout=5
            )
            # Testa a conexão
            self.client.ping()
        except Exception as e:
            print(f"Erro ao conectar no Redis: {e}")
            self.client = None

    def is_connected(self) -> bool:
        """Verifica se o cliente está conectado."""
        if self.client is None:
            return False
        try:
            return self.client.ping()
        except:
            return False

    def set_dataframe(self, key: str, df: pd.DataFrame, ttl: int = 43200) -> bool:
        """
        Armazena um DataFrame no Redis com compressão.
        Default TTL: 12 horas (43200 segundos).
        """
        if not self.is_connected():
            return False
        try:
            # Serializa e comprime
            data = zlib.compress(pickle.dumps(df))
            return self.client.setex(key, ttl, data)
        except Exception as e:
            print(f"Erro ao salvar DataFrame no Redis ({key}): {e}")
            return False

    def get_dataframe(self, key: str) -> Optional[pd.DataFrame]:
        """Recupera um DataFrame do Redis."""
        if not self.is_connected():
            return None
        try:
            data = self.client.get(key)
            if data:
                return pickle.loads(zlib.decompress(data))
            return None
        except Exception as e:
            print(f"Erro ao ler DataFrame do Redis ({key}): {e}")
            return None

    def set_object(self, key: str, obj: Any, ttl: int = 43200) -> bool:
        """Armazena um objeto serializável em JSON ou Pickle."""
        if not self.is_connected():
            return False
        try:
            if isinstance(obj, (dict, list, str, int, float, bool)):
                data = json.dumps(obj)
                # Flag para identificar que é JSON
                return self.client.setex(f"json:{key}", ttl, data)
            else:
                data = pickle.dumps(obj)
                return self.client.setex(f"pkl:{key}", ttl, data)
        except Exception as e:
            print(f"Erro ao salvar objeto no Redis ({key}): {e}")
            return False

    def get_object(self, key: str) -> Any:
        """Recupera um objeto do Redis."""
        if not self.is_connected():
            return None
        try:
            # Tenta JSON primeiro
            data = self.client.get(f"json:{key}")
            if data:
                return json.loads(data)
            
            # Tenta Pickle
            data = self.client.get(f"pkl:{key}")
            if data:
                return pickle.loads(data)
            
            return None
        except Exception as e:
            print(f"Erro ao ler objeto do Redis ({key}): {e}")
            return None

    def delete(self, key: str) -> bool:
        """Remove uma chave do Redis."""
        if not self.is_connected():
            return False
        return self.client.delete(key) > 0

    def set_dataframe_with_timestamp(self, key: str, df: pd.DataFrame, file_path: str, ttl: int = 43200) -> bool:
        """
        Armazena o DataFrame e o timestamp de modificação do arquivo original.
        """
        if not self.is_connected():
            return False
        try:
            mtime = os.path.getmtime(file_path)
            payload = {
                "df": df,
                "mtime": mtime
            }
            data = zlib.compress(pickle.dumps(payload))
            return self.client.setex(key, ttl, data)
        except Exception as e:
            print(f"Erro ao salvar DataFrame com timestamp ({key}): {e}")
            return False

    def get_dataframe_with_timestamp(self, key: str, file_path: str) -> Optional[pd.DataFrame]:
        """
        Recupera o DataFrame apenas se o arquivo original não tiver sido modificado.
        """
        if not self.is_connected():
            return None
        try:
            data = self.client.get(key)
            if not data:
                return None
            
            payload = pickle.loads(zlib.decompress(data))
            cache_mtime = payload.get("mtime")
            current_mtime = os.path.getmtime(file_path)

            # Se o arquivo no disco for mais novo que o cache, invalida
            if current_mtime > cache_mtime:
                print(f"Cache desatualizado para {file_path}. Lendo do disco...")
                return None
            
            return payload.get("df")
        except Exception as e:
            print(f"Erro ao ler DataFrame com timestamp ({key}): {e}")
            return None

# Instância global para importação facilitada
redis_cache = RedisClient()
