#!/usr/local/bin/python3.7

# Call Dependency

import sys
sys.path.append('/Applications/Understand.app/Contents/MacOS/Python')
import understand as us
from argparse import ArgumentParser
from graph import Graph
from itertools import permutations
from math_tool import average, sigmoid
import time
import json
import os
from methods_dic import update_id_method_dic

def add_paras_for_method(method_name, paras):
    if paras is None:
        return str(method_name) + "()"
    else:
        return str(method_name) + "(" + str(paras) + ")"


def get_cd(udb, parent_dir, filter_file_type = ".java", filter_ref_type = "Call"):

    id_method_dic = dict()
    cd_dic = {}

    for f in udb.ents("File"):
        from_file_name = f.longname(True).replace(parent_dir, "") # get abs path
        if not str(from_file_name).endswith(filter_file_type):
            continue

        # print("filename : " + fromFileName)
        if filter_ref_type == "Call":
            dic = f.depends()
        else:
            dic = f.dependsby()

        for entKey in dic:
            ref_list = dic[entKey]
            to_file_name = entKey.longname(True).replace(parent_dir, "")  # get abs path
            for ref in ref_list:
                kindname = ref.kindname()
                if kindname == "Call":   # no matter "Call" or "Callby"
                    # line_num = ref.line()

                    from_ent = ref.scope()
                    # print()

                    from_method_paras = from_ent.parameters()
                    from_method_name = add_paras_for_method(method_name = from_ent.simplename(), paras = from_method_paras)
                    from_method_type = from_ent.type()
                    if from_method_type is not None:
                        from_method_name = from_method_type + ' ' + from_method_name

                    to_ent = ref.ent()
                    to_method_paras = to_ent.parameters()
                    to_method_name = add_paras_for_method(method_name = to_ent.simplename(), paras = to_method_paras)
                    to_method_type = to_ent.type()
                    if to_method_type is not None:
                        to_method_name = to_method_type + ' ' + to_method_name

                    from_signature = from_file_name + '#' + from_method_name
                    to_signature = to_file_name   + '#' + to_method_name

                    from_id = update_id_method_dic(id_method_dic = id_method_dic, method = from_signature)
                    to_id = update_id_method_dic(id_method_dic = id_method_dic, method = to_signature)

                    if filter_ref_type == "Call":
                        dic_key   = from_id
                        dic_value = to_id
                        add_to_dic(cd_dic, dic_key, dic_value)
                    else:
                        dic_key   = to_id
                        dic_value = from_id
                        add_to_dic(cd_dic, dic_key, dic_value)

    return id_method_dic, cd_dic


def add_to_dic(dic, key, value):
    if key not in dic:
        dic[key] = [value]
    else:
        if value not in dic[key]:
            dic[key].append(value)
        # else:
        #     print(key + " , " + value)


def build_graph(dic):
    return Graph(dic)


def build_cd_dic(graph, id_method_dic, save_path):

    vertices = graph.vertices()
    print("Calculate path for methods of size :", str(len(vertices)))
    permutations_list = list(permutations(vertices, 2))

    cd_length_dic = dict()
    sigmoid_cd_dic = dict()
    for cd_pair in permutations_list:
        start_vertice = cd_pair[0]
        end_vertice   = cd_pair[1]
        path = graph.find_shortest_path(start = start_vertice, end = end_vertice)
        if path is not None:
            path_length = len(path)
            cd_length_dic[cd_pair] = path_length

    length_list = list(cd_length_dic.values())
    size = len(length_list)
    avg_shortest_length = average(length_list, size)
    for cd_pair in cd_length_dic:
        sigmoid_cd_dic[str(cd_pair[0])+'分'+str(cd_pair[1])] = sigmoid(1 - cd_length_dic[cd_pair] / avg_shortest_length)

    print("Call dictionary size:", str(len(sigmoid_cd_dic)))
    with open(save_path, 'w') as save_file:
        save_file.write(json.dumps(sigmoid_cd_dic))
    with open(save_path + '.dic', 'w') as dic_file:
        dic_file.write(json.dumps(id_method_dic))

    return


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-u", "--udb_path",   dest = "udb_path",   required = True)
    parser.add_argument("-s", "--save_path",  dest = "save_path",  required = True)
    parser.add_argument("-p", "--parent_dir", dest = "parent_dir", required = True)
    args = parser.parse_args()
    udb_path = args.udb_path
    save_path = args.save_path
    parent_dir = args.parent_dir

    start = time.process_time()
    print("Start Calculate Call Dependency...")
    db = us.open(udb_path)
    id_method_dic, cd_dic = get_cd(udb = db, parent_dir = parent_dir)
    db.close()
    cd_graph = build_graph(cd_dic)
    build_cd_dic(graph = cd_graph, id_method_dic = id_method_dic, save_path = save_path)
    elapsed = round(time.process_time() - start, 2)
    print("Finished Calculate Call Dependency. Time used : ", elapsed, "s.")
    print("File size is around : ", str(round(os.path.getsize(save_path) / 1024, 2)), "K.")
    # dub = us.open("/Users/lienming/Time_3/Time_3.udb")
    # cd_dic = get_cd(dub)
    # cd_graph = build_graph(cd_dic)
    # build_cd_dic(graph = cd_graph, save_path = "/Users/lienming/FineLocator/expRes/cd/Time/Time_3")