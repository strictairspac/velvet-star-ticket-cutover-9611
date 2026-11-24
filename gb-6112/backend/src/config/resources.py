from redis import Redis
from sqlalchemy import create_engine

from .settings import DATABASE_URL, REDIS_URL

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
cache = Redis.from_url(REDIS_URL, socket_connect_timeout=2, socket_timeout=3)
