# -*- coding: utf-8 -*-
"""
SWAP 选择模块
遍历硬件拓扑中每条边作为 SWAP 候选，模拟其效果，
选择使代价函数最小的 SWAP。

支持两种模式:
规模优化 
深度优化 

"""

from cost import compute_cost


def select_swap(gates, log_to_phy, phy_to_log, adj, edge_set, dist, num_q,
                qubit_depth=None, lookahead=12, depth_weight=0.05):
    """
    参数:
        gates:       list of tuple  剩余 CNOT 门
        log_to_phy:  list of int    逻辑→物理
        phy_to_log:  list of int    物理→逻辑
        adj:         list of list   邻接表
        edge_set:    set of tuple   边集合
        dist:        list of list   距离矩阵
        num_q:       int            量子比特数
        qubit_depth: list or None   每比特当前深度 
        lookahead:   int            前瞻窗口
        depth_weight: float         深度惩罚系数

    返回:
        tuple (s0,s1) or None   选中的 SWAP
    """
    best_swap = None
    best_cost = float('inf')
    seen_edges = set()

    for p0 in range(num_q):
        for p1 in adj[p0]:
            edge_key = (min(p0, p1), max(p0, p1))
            if edge_key in seen_edges:
                continue
            seen_edges.add(edge_key)

            l0 = phy_to_log[p0]
            l1 = phy_to_log[p1]

            
            new_log = log_to_phy[:]
            if l0 < num_q:
                new_log[l0] = p1
            if l1 < num_q:
                new_log[l1] = p0

          
            cost = compute_cost(gates, new_log, dist, num_q, lookahead)

          
            if qubit_depth is not None:
                cost += depth_weight * (qubit_depth[p0] + qubit_depth[p1])

            if cost < best_cost:
                best_cost = cost
                best_swap = (p0, p1)

    return best_swap
