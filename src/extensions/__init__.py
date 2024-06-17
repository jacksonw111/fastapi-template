from src.extensions.database import init as database_init
from src.extensions.redis import init as redis_init


class Extensions:
    db = database_init()
    redis = redis_init()
