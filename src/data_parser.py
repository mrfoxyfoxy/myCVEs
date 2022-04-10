"""
parser functions for the retrieved json data from the API response
"""

from typing import TYPE_CHECKING, Optional, Union

if TYPE_CHECKING:
    from container import JSON, JSONDict


def traverse_json(data: "JSON", index: str) -> Optional["JSON"]:
    """
    traverse through json data
    deep traversal will be used for indices which were not found on the next level
    and recursiv traversal is used for lists
    """
    if isinstance(data, dict):
        if index in data:
            if result := data.get(index):

                if not data.get("children"):
                    return result
                res = deep_traverse(data, index)
                res.insert(0, result)

                return res
            elif result is False:
                return result
        # ! It is possible that an index is found without a result but it can also be present in deeper layers, too
        return deep_traverse(data, index)
    elif isinstance(data, list):
        return [traverse_json(date, index) for date in data]
    return None


def deep_traverse(data: "JSONDict", index: str) -> list["JSON"]:
    """
    deep traverse through all levels of json data if the index was not found on the first searched level
    """
    results = []
    for key in data:
        sub_result = traverse_json(data[key], index)
        if sub_result is not None:
            if isinstance(sub_result, list):
                if len(sub_result) != 0 and isinstance(sub_result[0], list):
                    for sub in sub_result:
                        results.extend(sub)
                else:
                    results.extend(sub_result)
            else:
                results.append(sub_result)
    return results


def recursive_get(data: "JSON", *indices) -> Optional[Union["JSON", str, int, bool]]:
    """
    safely search multiple indexes deep into JSON data from the API response
    """
    results = data
    for index in indices:
        results = traverse_json(results, index)
        # ! stop if an intermediate index wasn't found at any level or if the result is None
        if results is None:
            return results

    # flatten multidimensional lists
    if results and isinstance(results, list) and isinstance(results[0], list):
        return [r for res in results for r in res]
    else:
        return results
