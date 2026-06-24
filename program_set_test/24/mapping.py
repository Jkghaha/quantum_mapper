# -*- coding: utf-8 -*-
"""
映射管理模块 
维护物理↔逻辑量子比特的双向映射，及深度追踪。
"""


def apply_swap(swap, phy_to_log, log_to_phy, num_q):
    """
    参数:
        swap:       tuple (s0,s1)  在物理比特 s0,s1 上做 SWAP
        phy_to_log: list of int    物理→逻辑 
        log_to_phy: list of int    逻辑→物理 
        num_q:      int
    """
    s0, s1 = swap
    l0 = phy_to_log[s0]
    l1 = phy_to_log[s1]

    # 交换
    phy_to_log[s0], phy_to_log[s1] = l1, l0

    if l0 < num_q:
        log_to_phy[l0] = s1
    if l1 < num_q:
        log_to_phy[l1] = s0


def track_depth(qubit_depth, qubits, cost):
    """
    更新受影响的 qubit 深度。

    CNOT: cost=1    SWAP: cost=3

    参数:
        qubit_depth: list of int  当前各 qubit 深度 
        qubits:      list of int  受影响的物理比特
        cost:        int          本次操作消耗的深度单位
    """
    new_d = max(qubit_depth[q] for q in qubits) + cost
    for q in qubits:
        qubit_depth[q] = new_d
