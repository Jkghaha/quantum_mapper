# -*- coding: utf-8 -*-
"""
图构建模块 
根据硬件拓扑连通性列表构建图数据结构。
输入: [(0,1), (1,2), ...]  →  输出: 邻接表 + 边集合 + 量子比特数
"""


def build_graph(connectivity):

    max_id = 0
    for a, b in connectivity:
        if a > max_id:
            max_id = a
        if b > max_id:
            max_id = b
    num_q = max_id + 1

    
    adj = [[] for _ in range(num_q)]
    edge_set = set()
    for a, b in connectivity:
        adj[a].append(b)
        adj[b].append(a)
        edge_set.add((a, b))
        edge_set.add((b, a))

    return adj, edge_set, num_q
