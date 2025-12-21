import string

from django.core.cache import cache

letters = "ءاأبتثجحخدذرزسشصضطظعغفقكامنهوي" + "123456789" + string.punctuation

letters_indexes = {}

## Giving every letter, number and punctuation that are strings an index in order to sort it like a integer

for dx, i in enumerate(letters):
    letters_indexes[i] = dx

for dx, i in enumerate(string.ascii_lowercase):
    letters_indexes[i] = dx


# for dx,i in enumerate(string.ascii_uppercase):
#     letters_indexes[i] = dx


## for a list with numbers use quickSort([int,int,int])

## for a list with strings use quickSort([str,str,str],True)


def quickSort(arr: list):
    if len(arr) <= 1:
        return arr
    ## Getting the middle element of the list
    pivot_ind = int(len(arr) / 2)

    pivot = arr[pivot_ind]
    ## removing it for the list
    arr.pop(pivot_ind)

    right_list = []
    left_list = []
    ## if it's not a list of strings then it's a list of integers so we can compare them
    for i in arr:
        if i[0] < pivot[0]:
            left_list.append(i)
        else:
            right_list.append(i)
    return quickSort(left_list) + [pivot] + quickSort(right_list)


## To scale the rating from 1-10 to -5-5
def scale(x, srcRange, dstRange) -> float:
    return round(
        (x - srcRange[0]) * (dstRange[1] - dstRange[0]) / (srcRange[1] - srcRange[0])
        + dstRange[0],
        3,
    )


def get_cached_or_queryset(
    cache_key,
    queryset,
    serializer_cls=None,
    many=True,
    timeout=60 * 60,
    for_template=False,
):
    """
    Utility to DRY up getting data from cache or DB.
    If serializer_cls is None or for_template=True, returns the actual queryset instead of serialized data.
    """
    data = cache.get(cache_key)
    if data is None:
        if serializer_cls and not for_template:
            data = serializer_cls(queryset, many=many).data
        else:
            # For use in template views -- just evaluate the queryset (convert to list to cache)
            data = list(queryset)
        cache.set(cache_key, data, timeout)
    return data
