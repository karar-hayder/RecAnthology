import string
letters = 'ءاأبتثجحخدذرزسشصضطظعغفقكامنهوي' + '123456789' +string.punctuation

letters_indexes = {}

## Giving every letter, number and punctuation that are strings an index in order to sort it like a integer

for dx,i in enumerate(letters):
    letters_indexes[i] = dx

for dx,i in enumerate(string.ascii_lowercase):
    letters_indexes[i] = dx


# for dx,i in enumerate(string.ascii_uppercase):
#     letters_indexes[i] = dx


## for a list with numbers use quickSort([int,int,int])

## for a list with strings use quickSort([str,str,str],True)

def quickSort(arr:list):
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
