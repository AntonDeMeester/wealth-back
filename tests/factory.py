from typing import Any, Callable, Literal, Protocol, Type, TypeVar, Union, overload

from pydantic import BaseModel

T = TypeVar("T", covariant=True)
P = TypeVar("P", bound=BaseModel)

SpecialCaseDict = dict[str, Callable[[Any], Any]]


class ModelGenerator(Protocol[T]):
    @overload
    def __call__(self, *, _raw: Literal[True], **kwargs) -> dict:
        pass

    @overload
    def __call__(self, *, _raw: Literal[False] = False, **kwargs) -> T:
        pass

    def __call__(self, *, _raw=False, **kwargs) -> Union[T, dict]:
        pass


def database_model_generator(
    model_type: Type[P], defaults: dict, special_cases: SpecialCaseDict | None = None
) -> ModelGenerator[P]:
    _special_cases = special_cases if special_cases is not None else {}

    @overload
    def _generate_model(*, _raw: Literal[True], **kwargs) -> dict:
        pass

    @overload
    def _generate_model(*, _raw: Literal[False] = False, **kwargs) -> P:
        pass

    def _generate_model(*, _raw=False, **kwargs) -> Union[P, dict]:
        all_data = defaults | kwargs
        for key, to_be_called in _special_cases.items():
            all_data[key] = to_be_called(all_data[key])
        if _raw:
            return all_data
        return model_type.parse_obj(all_data)

    return _generate_model


def pydantic_model_generator(
    model_type: Type[P], defaults: dict, special_cases: SpecialCaseDict | None = None
) -> ModelGenerator[P]:
    _special_cases = special_cases if special_cases is not None else {}

    @overload
    def _generate_model(*, _raw: Literal[True], **kwargs) -> dict:
        pass

    @overload
    def _generate_model(*, _raw: Literal[False] = False, **kwargs) -> P:
        pass

    def _generate_model(*, _raw=False, **kwargs) -> Union[P, dict]:
        all_data = defaults | kwargs
        for key, to_be_called in _special_cases.items():
            all_data[key] = to_be_called(all_data[key])
        if _raw:
            return all_data
        return model_type.parse_obj(all_data)

    return _generate_model
