# -*- coding: utf-8 -*-
"""
量子线路映射模块 - 主入口 
组装 graph / bfs / check_sim / cost / swap / mapping 六个微模块，
实现 main_qm
"""

from graph import build_graph
from bfs import all_pairs_distance, shortest_path
from check_sim import find_executable
from cost import compute_cost
from swap import select_swap
from mapping import apply_swap, track_depth


def main_qm(cnot_list, connectivities, obj):
    """
    量子线路映射模块主函数。

    参数:
        cnot_list:      CNOT门列表 [(q0,q1), ...]
        connectivities: 硬件拓扑 [(p0,p1), ...]
        obj:            "size" 或 "depth"

    返回:
        SWAP门列表 [(s0,s1), ...]
    """
    # 构建图
    adj, edge_set, num_q = build_graph(connectivities)

    # 距离矩阵
    dist = all_pairs_distance(adj, num_q)

    # 初始映射: 逻辑i ↔ 物理i
    log_to_phy = list(range(num_q))
    phy_to_log = list(range(num_q))

    # 深度追踪 (仅 depth 模式)
    qubit_depth = [0] * num_q if obj == "depth" else None

    # 主循环
    gates = list(cnot_list)
    swaps_out = []
    max_iter = len(gates) * 200
    it = 0

    while gates:
        it += 1
        if it > max_iter:
            break

        idx = find_executable(gates, log_to_phy, edge_set, num_q)

        if idx >= 0:
            
            l0, l1 = gates.pop(idx)
            if qubit_depth is not None:
                p0, p1 = log_to_phy[l0], log_to_phy[l1]
                track_depth(qubit_depth, [p0, p1], cost=1)
            continue

        
        best = select_swap(
            gates, log_to_phy, phy_to_log, adj, edge_set, dist, num_q,
            qubit_depth)

        
        if best is None:
            l0, l1 = gates[0]
            p0 = log_to_phy[l0] if l0 < num_q else l0
            p1 = log_to_phy[l1] if l1 < num_q else l1
            path = shortest_path(adj, p0, p1)
            if len(path) >= 2:
                best = (path[0], path[1])

        if best is None:
            for p in range(num_q):
                if adj[p]:
                    best = (p, adj[p][0])
                    break
        if best is None:
            break

        
        swaps_out.append(best)
        apply_swap(best, phy_to_log, log_to_phy, num_q)

        if qubit_depth is not None:
            track_depth(qubit_depth, list(best), cost=3)

    return swaps_out


def main_cs(full_path):
    """不做要求"""
    return [0.1 + 2j, -2 - 3j]
