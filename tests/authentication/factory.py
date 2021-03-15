from tests.factory import pydantic_model_generator
from wealth.authentication.models import CreateUser

_create_user_defaults = {
    "email": "test@test.com",
    "first_name": "test_fn",
    "last_name": "test_ln",
    "password": "password123",
    "password2": "password123",
}

generate_create_user = pydantic_model_generator(CreateUser, _create_user_defaults)
