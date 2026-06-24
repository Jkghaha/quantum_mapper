# -*- coding: utf-8 -*-
"""
代价函数模块 - cost.py
衰减加权距离代价函数，用于评估候选 SWAP 的优劣。

"""


def compute_cost(gates, log_to_phy, dist, num_q, lookahead=12, decay=0.5):

    cost = 0.0
    weight = 1.0

    for i, (l0, l1) in enumerate(gates):
        if i >= lookahead:
            break
        if l0 >= num_q or l1 >= num_q:
            continue

        p0 = log_to_phy[l0]
        p1 = log_to_phy[l1]
        cost += weight * dist[p0][p1]
        weight *= decay

    return cost
