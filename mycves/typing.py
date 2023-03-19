from typing import Any, Union

JSONDict = dict[str, Any]
JSONList = list[Any]
JSON = Union[JSONDict, JSONList, str, int, float, bool, None]
