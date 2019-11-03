# Temporal Proximity

import time
import os
from itertools import combinations
from math_tool import average, sigmoid
from argparse import ArgumentParser
import json
from methods_dic import build_methods_dic

time_format = "%a %b %d %H:%M:%S %Z %Y"


def cal_time_diff_by_second(time_str1, time_str2):
    seconds1 = int(time.mktime(time.strptime(time_str1, time_format)))
    seconds2 = int(time.mktime(time.strptime(time_str2, time_format)))
    return abs(seconds1-seconds2)


# load dic of last modify time for all methods
def load_dic_lmt(proj_path):
    id_method_dic = dict()
    id_value_dic = dict()
    for root, dirs, files in os.walk(proj_path):
        for file in files:
            if file.endswith(".java"):
                file_path = os.path.join(root, file)
                # print(file_path)
                f = open(file_path, 'r')
                lines = f.readlines()
                for line in lines:
                    if line is not None:
                        line = line.strip()
                        parts = line.split(',')
                        method_signature = parts[:-3]
                        last_modify_time = parts[-1]
                        # use relative path
                        relative_path = file_path.replace(proj_path, "")
                        key = relative_path + '#' + ','.join(method_signature)
                        build_methods_dic(method = key, value = last_modify_time,
                                          id_method_dic = id_method_dic ,
                                          id_value_dic = id_value_dic )
                f.close()
    return id_method_dic, id_value_dic


# use cache to reduce calculate operation
def get_td_list(id_value_dic):
    td_list = []
    cache_dic = {}
    for value in id_value_dic.values():
        if value in cache_dic:
            td_list.append(cache_dic[value])
        else:
            td = int(time.mktime(time.strptime(value, time_format)))
            cache_dic[value] = td
            td_list.append(td)
    return td_list


def cal_time_diff_for_dic(id_method_dic, id_value_dic, save_path):
    keys = id_value_dic.keys()
    comb_list = list(combinations(keys, 2))
    print("Calculate methods of size :", str(len(keys)))
    td_list = get_td_list(id_value_dic = id_value_dic)
    avg_td = average(td_list, len(td_list))
    del td_list

    cache_dic = dict()
    tp_dic = dict()
    with open(save_path, 'w') as f:
        for tp in comb_list:
            m1 = tp[0]
            m2 = tp[1]
            time_str1 = id_value_dic[m1]
            time_str2 = id_value_dic[m2]
            # if t1#t2 in result_dic, t2#t1 is in result_dic
            if (time_str1 + '#' + time_str2) in cache_dic:
                tp_dic[str(m1) + "分" + str(m2)] = cache_dic[time_str1 + '#' + time_str2]
                # f.write(m1 + "分"+ m2 + "分" + str(cache_dic[time_str1 + '#' + time_str2]) + "\n")
            else:
                diff = cal_time_diff_by_second(time_str1, time_str2)
                sig_time_diff = sigmoid(diff / avg_td)
                cache_dic[time_str1 + '#' + time_str2] = sig_time_diff
                cache_dic[time_str2 + '#' + time_str1] = sig_time_diff
                tp_dic[str(m1) + "分" + str(m2)] = sig_time_diff
                # f.write(m1 + "分"+ m2 + "分" + str(sig_time_diff) + "\n")
        f.write(json.dumps(tp_dic))
    with open(save_path + ".dic", 'w') as dic_f:
        dic_f.write(json.dumps(id_method_dic))
    return


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("-c", "--correspond_path", dest = "correspond_path", required = True)
    parser.add_argument("-s", "--save_path", dest = "save_path", required = True)
    args = parser.parse_args()
    correspond_path = args.correspond_path
    save_path = args.save_path

    start = time.process_time()
    print("Start Calculate Temporal Proximity...")
    # save_path = "/Users/lienming/FineLocator/expRes/tp/Time/Time_3"
    # time_dic = load_dic_lmt("/Users/lienming/FineLocator/expRes/afterPT/correspond/Closure/Closure_176")
    id_method_dic, id_value_dic = load_dic_lmt(correspond_path)
    cal_time_diff_for_dic(id_method_dic, id_value_dic, save_path = save_path)
    elapsed = round(time.process_time() - start, 2)
    print("Finished Calculate Temporal Proximity. Time used : ", elapsed, "s.")
    print("Save to File :", save_path)
    print("File size is around : ", str(round(os.path.getsize(save_path) / (1024 * 1024 ), 2)), "M.")