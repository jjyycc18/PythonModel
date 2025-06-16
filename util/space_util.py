from collections import defaultdict
import os
import shutil

def make_dict_group_by_key_func(input_list, extract_key_func):
    group_by_dict = defaultdict(list)
    for item in input_list:
        group_by_dict[extract_key_func(item)].append(item)
    return group_by_dict

#오사오입 파이슨용
def excel_round(val, digits):
    return round(val + 10**(-len(str(val))-1), digits)
  
