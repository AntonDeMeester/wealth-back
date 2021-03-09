from os import environ
from typing import Any, Dict, Tuple, Type, Union, cast


def is_env_variable(name: str, annotation_class: Type, default: Any) -> bool:
    valid_classes = (str, int, type(None))
    try:
        origin = annotation_class.__origin__
    except AttributeError:
        origin = None
    if origin is Union:
        if not all(subtype in valid_classes for subtype in annotation_class.__args__):
            return False
    elif annotation_class not in valid_classes:
        return False
    if not isinstance(default, valid_classes):
        return False
    if not name.upper() == name:
        return False
    return True


class EnvironmentMeta(type):
    def __new__(
        cls: Type["EnvironmentMeta"], name: str, bases: Tuple[type, ...], namespace: Dict[str, Any]
    ) -> "EnvironmentMeta":
        obj = super().__new__(cls, name, bases, namespace)  # type: ignore
        for key, value in namespace["__annotations__"].items():
            default = namespace.get("key")
            if is_env_variable(key, value, default):
                setattr(cls, key, environ.get(key, default))
        return cast("EnvironmentMeta", obj)


class Environment(metaclass=EnvironmentMeta):
    ENV: str
    APP_SECRET: str
    MONGO_URL: str
    LOG_LEVEL: str = "INFO"
    SENTRY_DSN: str = ""


env = Environment()
