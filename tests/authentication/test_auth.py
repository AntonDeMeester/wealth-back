from unittest.mock import patch

import httpx
import pytest
from fastapi.exceptions import HTTPException
from fastapi_jwt_auth.exceptions import JWTDecodeError, MissingTokenError
from odmantic import AIOEngine

from tests.authentication.factory import generate_create_user
from tests.database.factory import generate_user
from wealth.authentication.models import CreateUser, LoginUser
from wealth.authentication.passwords import check_password, encode_password, validate_password
from wealth.authentication.wealth_jwt import WealthJwt
from wealth.database.models import User
from wealth.main import app


class TestModels:
    test_async_validate_data = (
        (None, None),
        (ValueError("Could not find email"), HTTPException(status_code=422, detail=["Could not find email"])),
    )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("side_effect,expected", test_async_validate_data)
    async def test_user_async_validate(self, side_effect, expected):
        user = CreateUser.construct(email="test")
        with patch.object(CreateUser, "validate_email") as mock:
            mock.side_effect = side_effect
            if side_effect is None:
                await user.async_validate()
            else:
                with pytest.raises(type(expected)) as exc:
                    await user.async_validate()
                    assert exc.status_code == expected.status_code
                    assert exc.detail == expected.detail

    @pytest.mark.asyncio
    # pylint: disable=unused-argument
    async def test_user_async_validate_email_present(self, local_database: AIOEngine):
        not_present_email = "not@present.com"
        validated = await CreateUser.validate_email(not_present_email)
        assert validated == not_present_email

    @pytest.mark.asyncio
    # pylint: disable=unused-argument
    async def test_user_async_validate_email_not_present(self, local_database: AIOEngine):
        already_present_email = "is@present.com"

        db_user = User(email=already_present_email, password=b"123", first_name="hello", last_name="world")
        await local_database.save(db_user)

        with pytest.raises(ValueError) as exc:
            await CreateUser.validate_email(already_present_email)
            assert str(exc) == "Email already registered"

    test_password_complete_data = (
        ({"password": "password123", "password2": "password123"}, True),
        ({"password": "short", "password2": "short"}, False),
        ({"password": "notthesame123", "password2": "123notthesame"}, False),
    )

    @pytest.mark.parametrize("user_info,correct", test_password_complete_data)
    def test_password_complete(self, user_info, correct):
        if correct:
            generate_create_user(**user_info)
        else:
            with pytest.raises(ValueError):
                generate_create_user(**user_info)


class TestPasswords:
    test_validate_password_data = (
        ("393tHRLuM48NEPw8UZK7", True),
        ("short", False),
        ("onlyletters", True),
        ("123456789", True),
        ("superlong-superlong-superlong-superlong-superlong-", True),
    )

    @pytest.mark.parametrize("password,valid", test_validate_password_data)
    def test_validate_password(self, password, valid):
        assert validate_password(password) == valid

    def test_encode_password(self):
        original = "original"
        encoded = encode_password(original)
        assert original != encoded

    def test_encode_password_salt(self):
        original = "original"
        encoded = encode_password(original)
        twice = encode_password(original)
        assert encoded != twice

    test_check_password_data = (
        ("original", "original", True),
        ("original", "different", False),
    )

    @pytest.mark.parametrize("original,to_check,valid", test_check_password_data)
    def test_check_password(self, original, to_check, valid):
        original = "original"
        encoded = encode_password(original)
        assert check_password(to_check, encoded) == valid


class TestAuthViews:
    @pytest.mark.asyncio
    # pylint: disable=unused-argument
    async def test_login_valid(self, local_database: AIOEngine):
        password = "password123"
        user = generate_user(email="test@test.com", password=password)
        await local_database.save(user)

        data = {"email": user.email, "password": password}

        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/auth/login", json=data)

        assert response.status_code == 200
        assert "access_token" in response.json()
        assert "refresh_token" in response.json()

    @pytest.mark.asyncio
    # pylint: disable=unused-argument
    async def test_login_user_not_exist(self, local_database: AIOEngine):
        password = "password123"
        data = {"email": "test@test.com", "password": password}

        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/auth/login", json=data)

        assert response.status_code == 401

    @pytest.mark.asyncio
    # pylint: disable=unused-argument
    async def test_login_user_not_password_wrong(self, local_database: AIOEngine):
        password = "password123"
        wrong_password = "password124"
        user = generate_user(email="test@test.com", password=password)
        await local_database.save(user)

        data = {"email": user.email, "password": wrong_password}

        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/auth/login", json=data)

        assert response.status_code == 401

    @pytest.mark.asyncio
    # pylint: disable=unused-argument
    async def test_refresh_valid(self, local_database: AIOEngine):
        password = "password123"
        user = generate_user(email="test@test.com", password=password)
        await local_database.save(user)

        data = {"email": user.email, "password": password}

        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            jwt = await client.post("/auth/login", json=data)
            auth = f"Bearer {jwt.json()['refresh_token']}"
            response = await client.post("/auth/refresh", headers={"Authorization": auth})

        assert response.status_code == 200
        assert "access_token" in response.json()

    @pytest.mark.asyncio
    # pylint: disable=unused-argument
    async def test_refresh_wrong_jwt(self, local_database: AIOEngine):
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            auth = "Bearer Somethingwrong"
            response = await client.post("/auth/refresh", headers={"Authorization": auth})

        assert response.status_code == 422

    @pytest.mark.asyncio
    # pylint: disable=unused-argument
    async def test_get_user(self, local_database: AIOEngine):
        password = "password123"
        user = generate_user(email="test@test.com", password=password)
        await local_database.save(user)

        data_input = {"email": user.email, "password": password}

        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            jwt = await client.post("/auth/login", json=data_input)
            auth = f"Bearer {jwt.json()['access_token']}"
            response = await client.get("/auth/user", headers={"Authorization": auth})

        assert response.status_code == 200
        data = response.json()
        assert user.email == data["email"]
        assert user.first_name == data["first_name"]
        assert "password" not in data

    @pytest.mark.asyncio
    # pylint: disable=unused-argument
    async def test_get_user_no_auth(self, local_database: AIOEngine):
        password = "password123"
        user = generate_user(email="test@test.com", password=password)
        await local_database.save(user)

        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            auth = "Bearer hello world"
            response = await client.get("/auth/user", headers={"Authorization": auth})

        assert response.status_code == 422

    @pytest.mark.asyncio
    # pylint: disable=unused-argument
    async def test_create_user(self, local_database: AIOEngine):
        data_input = generate_create_user(email="test@test.com", _raw=True)

        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/auth/user", json=data_input)

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == data_input["email"]


class TestWealthJwt:
    @pytest.mark.asyncio
    # pylint: disable=unused-argument
    async def test_get_jwt_user_present(self, local_database: AIOEngine):
        email = "test@test.com"
        user = generate_user(email=email)
        await local_database.save(user)

        jwt = WealthJwt()

        with patch.object(WealthJwt, "get_jwt_subject", return_value=email):
            retrieved_user = await jwt.get_jwt_user()

        assert retrieved_user is not None
        assert retrieved_user.email == email

    @pytest.mark.asyncio
    # pylint: disable=unused-argument
    async def test_get_jwt_user_not_present(self, local_database: AIOEngine):
        email = "test@test.com"

        jwt = WealthJwt()

        with patch.object(WealthJwt, "get_jwt_subject", return_value=email):
            retrieved_user = await jwt.get_jwt_user()

        assert retrieved_user is None

    @pytest.mark.asyncio
    # pylint: disable=unused-argument
    async def test_get_jwt_user_no_token(self, local_database: AIOEngine):
        jwt = WealthJwt()

        with patch.object(WealthJwt, "get_jwt_subject", return_value=None):
            retrieved_user = await jwt.get_jwt_user()

        assert retrieved_user is None

    @pytest.mark.asyncio
    # pylint: disable=unused-argument
    async def test_get_authenticated_jwt_user_valid(self, local_database: AIOEngine):
        user = generate_user()

        jwt = WealthJwt()

        with patch.object(WealthJwt, "get_jwt_user", return_value=user), patch.object(WealthJwt, "jwt_required"):
            retrieved_user = await jwt.get_authenticated_jwt_user()

        assert user == retrieved_user

    @pytest.mark.asyncio
    # pylint: disable=unused-argument
    async def test_get_authenticated_jwt_user_invalid(self, local_database: AIOEngine):
        user = None

        jwt = WealthJwt()

        with patch.object(WealthJwt, "get_jwt_user", return_value=user), patch.object(WealthJwt, "jwt_required"):
            with pytest.raises(JWTDecodeError) as exc:
                await jwt.get_authenticated_jwt_user()
                assert exc.status_code == 401  # type: ignore

    @pytest.mark.asyncio
    # pylint: disable=unused-argument
    async def test_get_authenticated_jwt_user_no_token(self, local_database: AIOEngine):
        jwt = WealthJwt()

        with pytest.raises(MissingTokenError) as exc:
            await jwt.get_authenticated_jwt_user()
            assert exc.status_code == 401  # type: ignore

    def test_jwt_forbidden_valid(self):
        user = None
        jwt = WealthJwt()

        with patch.object(WealthJwt, "get_jwt_subject", return_value=user):
            jwt.jwt_forbidden()

    def test_jwt_forbidden_invalid(self):
        user = "test@test.com"
        jwt = WealthJwt()

        with patch.object(WealthJwt, "get_jwt_subject", return_value=user):
            with pytest.raises(JWTDecodeError) as exc:
                jwt.jwt_forbidden()
                assert exc.status_code == 422

    @pytest.mark.asyncio
    # pylint: disable=unused-argument
    async def test_login_valid(self, local_database: AIOEngine):
        password = "password123"
        user = generate_user(email="test@test.com", password=password)
        await local_database.save(user)

        data = {"email": user.email, "password": password}
        jwt = WealthJwt()

        retrieved_user = await jwt.login_user(LoginUser(**data))

        assert retrieved_user.email == user.email

    @pytest.mark.asyncio
    # pylint: disable=unused-argument
    async def test_login_user_not_exist(self, local_database: AIOEngine):
        password = "password123"
        user = generate_user(email="test@test.com", password=password)

        data = {"email": user.email, "password": password}
        jwt = WealthJwt()

        with pytest.raises(JWTDecodeError) as exc:
            await jwt.login_user(LoginUser(**data))
            assert exc.status_code == 401  # type: ignore

    @pytest.mark.asyncio
    # pylint: disable=unused-argument
    async def test_login_user_password_wrong(self, local_database: AIOEngine):
        password = "password123"
        wrong_password = "password124"
        user = generate_user(email="test@test.com", password=password)
        await local_database.save(user)

        data = {"email": user.email, "password": wrong_password}
        jwt = WealthJwt()

        with pytest.raises(JWTDecodeError) as exc:
            await jwt.login_user(LoginUser(**data))
            assert exc.status_code == 401  # type: ignore
