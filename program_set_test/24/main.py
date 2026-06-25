# -*- coding: utf-8 -*-
"""
量子线路映射模块 - 队伍 24
============================================================
仅使用 Python 标准库，无需任何第三方库。
"""

from collections import deque



#  第一部分：拓扑结构处理

def _build_adjacency(connectivity):
    all_qubits = set()
    for a, b in connectivity:
        all_qubits.add(a)
        all_qubits.add(b)
    num_q = max(all_qubits) + 1

    adj = [[] for _ in range(num_q)]
    edge_set = set()
    for a, b in connectivity:
        adj[a].append(b)
        adj[b].append(a)
        edge_set.add((a, b))
        edge_set.add((b, a))

    return adj, edge_set, num_q


def _bfs_distances(adj, num_q):
    dist = [[0] * num_q for _ in range(num_q)]
    for src in range(num_q):
        d = [-1] * num_q
        d[src] = 0
        q = deque([src])
        while q:
            u = q.popleft()
            for v in adj[u]:
                if d[v] == -1:
                    d[v] = d[u] + 1
                    q.append(v)
        dist[src] = d
    return dist


def _bfs_path(adj, src, dst):
    if src == dst:
        return [src]
    parent = {src: None}
    q = deque([src])
    while q:
        u = q.popleft()
        if u == dst:
            break
        for v in adj[u]:
            if v not in parent:
                parent[v] = u
                q.append(v)
    if dst not in parent:
        return []
    path = [dst]
    while parent[path[-1]] is not None:
        path.append(parent[path[-1]])
    path.reverse()
    return path



#  第二部分：check_eq 兼容的执行模型（与原版一致）


def _find_executable(gates, log_to_phy, edge_set, num_q):
    
    qubits_ocpy = [False] * num_q

    for i, (l0, l1) in enumerate(gates):
        if not False in qubits_ocpy:
            break
        if l0 < num_q and l1 < num_q:
            if (not qubits_ocpy[l0]) and (not qubits_ocpy[l1]):
                p0 = log_to_phy[l0]
                p1 = log_to_phy[l1]
                if (p0, p1) in edge_set:
                    return i
        if l0 < num_q:
            qubits_ocpy[l0] = True
        if l1 < num_q:
            qubits_ocpy[l1] = True

    return -1



#  第三部分：SWAP 选择策略（增强版）


def _compute_cost(gates, log_to_phy, dist, num_q, lookahead):
    
    cost = 0.0
    weight = 1.0
    decay = 0.5

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


def _select_swap(gates, log_to_phy, phy_to_log, adj, dist, num_q,
                 qubit_depth=None):
    """
    选择最优 SWAP。

    size 模式
    depth 模式
    """
    if qubit_depth is not None:
        
        lookahead = min(30, max(12, len(gates) // 2))
        depth_weight = 0.3
    else:
        
        lookahead = min(20, max(6, len(gates) // 2))
        depth_weight = 0.0

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

            dist_cost = _compute_cost(
                gates, new_log, dist, num_q, lookahead)

            cost = dist_cost

            if qubit_depth is not None:
                depth_penalty = depth_weight * (
                    qubit_depth[p0] + qubit_depth[p1])
                cost += depth_penalty

            if cost < best_cost:
                best_cost = cost
                best_swap = (p0, p1)

    return best_swap



#  第四部分：核心映射循环


def _run_mapping(gates_in, adj, edge_set, dist, num_q, use_depth):
    
    log_to_phy = list(range(num_q))
    phy_to_log = list(range(num_q))
    qubit_depth = [0] * num_q if use_depth else None

    gates = list(gates_in)
    swaps_out = []

    max_iter = len(gates) * 200
    it = 0

    while gates:
        it += 1
        if it > max_iter:
            break

        exec_idx = _find_executable(gates, log_to_phy, edge_set, num_q)

        if exec_idx >= 0:
            l0, l1 = gates.pop(exec_idx)
            if qubit_depth is not None:
                p0, p1 = log_to_phy[l0], log_to_phy[l1]
                d = max(qubit_depth[p0], qubit_depth[p1]) + 1
                qubit_depth[p0] = qubit_depth[p1] = d
            continue

        best_swap = _select_swap(
            gates, log_to_phy, phy_to_log, adj, dist, num_q,
            qubit_depth)

        if best_swap is None:
            l0, l1 = gates[0]
            p0 = log_to_phy[l0] if l0 < num_q else l0
            p1 = log_to_phy[l1] if l1 < num_q else l1
            if p0 < num_q and p1 < num_q:
                path = _bfs_path(adj, p0, p1)
                if len(path) >= 2:
                    best_swap = (path[0], path[1])

        if best_swap is None:
            for p in range(num_q):
                if adj[p]:
                    best_swap = (p, adj[p][0])
                    break
        if best_swap is None:
            break

        s0, s1 = best_swap
        swaps_out.append(best_swap)

        l0, l1 = phy_to_log[s0], phy_to_log[s1]
        phy_to_log[s0], phy_to_log[s1] = l1, l0
        if l0 < num_q:
            log_to_phy[l0] = s1
        if l1 < num_q:
            log_to_phy[l1] = s0

        if qubit_depth is not None:
            d = max(qubit_depth[s0], qubit_depth[s1]) + 3
            qubit_depth[s0] = qubit_depth[s1] = d

    return swaps_out



#  第五部分：主函数


def main_qm(cnot_list, connectivities, obj):
    
    adj, edge_set, num_q = _build_adjacency(connectivities)
    dist = _bfs_distances(adj, num_q)
    use_depth = (obj == "depth")

    return _run_mapping(cnot_list, adj, edge_set, dist, num_q, use_depth)


def main_cs(full_path):
    
    return [0.1 + 2j, -2 - 3j]
