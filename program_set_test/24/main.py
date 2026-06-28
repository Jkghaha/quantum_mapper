# -*- coding: utf-8 -*-
"""
量子线路映射模块  - 队伍 24


仅使用 Python 标准库。
"""

from collections import deque



#  第一部分：拓扑结构处理


def _build_adjacency(connectivity):
    all_qubits = set()
    for a, b in connectivity:
        all_qubits.add(a); all_qubits.add(b)
    num_q = max(all_qubits) + 1
    adj = [[] for _ in range(num_q)]
    edge_set = set()
    for a, b in connectivity:
        adj[a].append(b); adj[b].append(a)
        edge_set.add((a, b)); edge_set.add((b, a))
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



#  第二部分：check_eq 兼容的执行模型


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



#  第三部分：SWAP 选择策略


def _scan_executable(gates, log_to_phy, edge_set, num_q):
   
    qubits_ocpy = [False] * num_q
    for i, (l0, l1) in enumerate(gates):
        if all(qubits_ocpy):
            break
        if l0 < num_q and l1 < num_q:
            if (not qubits_ocpy[l0]) and (not qubits_ocpy[l1]):
                p0, p1 = log_to_phy[l0], log_to_phy[l1]
                if (p0, p1) in edge_set:
                    return i
        if l0 < num_q:
            qubits_ocpy[l0] = True
        if l1 < num_q:
            qubits_ocpy[l1] = True
    return -1


def _distance_cost(gates, log_to_phy, dist, num_q, lookahead):
   
    cost = 0.0
    weight = 1.0
    for i, (l0, l1) in enumerate(gates):
        if i >= lookahead:
            break
        if l0 >= num_q or l1 >= num_q:
            continue
        cost += weight * dist[log_to_phy[l0]][log_to_phy[l1]]
        weight *= 0.5
    return cost


def _select_swap_size(gates, log_to_phy, phy_to_log, adj, edge_set, dist, num_q):
  
    G = len(gates)
    lookahead = min(20, max(6, G // 2))

    best_swap = None
    best_score = float('inf')
    seen = set()

    for p0 in range(num_q):
        for p1 in adj[p0]:
            key = (min(p0, p1), max(p0, p1))
            if key in seen:
                continue
            seen.add(key)

            l0, l1 = phy_to_log[p0], phy_to_log[p1]
            new_log = log_to_phy[:]
            if l0 < num_q:
                new_log[l0] = p1
            if l1 < num_q:
                new_log[l1] = p0

            exec_pos = _scan_executable(gates, new_log, edge_set, num_q)

            if exec_pos >= 0:
                score = exec_pos * 1000.0
                score += _distance_cost(gates, new_log, dist, num_q, lookahead) * 0.001
            else:
                score = 1000000.0 + _distance_cost(gates, new_log, dist, num_q, lookahead)

            if score < best_score:
                best_score = score
                best_swap = (p0, p1)

    return best_swap


def _select_swap_depth(gates, log_to_phy, phy_to_log, adj, dist, num_q,
                       qubit_depth):
   
    G = len(gates)
    lookahead = min(30, max(12, G // 2))
    depth_weight = 0.3

    best_swap = None
    best_score = float('inf')
    seen = set()

    for p0 in range(num_q):
        for p1 in adj[p0]:
            key = (min(p0, p1), max(p0, p1))
            if key in seen:
                continue
            seen.add(key)

            l0, l1 = phy_to_log[p0], phy_to_log[p1]
            new_log = log_to_phy[:]
            if l0 < num_q:
                new_log[l0] = p1
            if l1 < num_q:
                new_log[l1] = p0

            # 加权距离代价
            dist_cost = _distance_cost(gates, new_log, dist, num_q, lookahead)
            # 深度惩罚
            score = dist_cost + depth_weight * (qubit_depth[p0] + qubit_depth[p1])

            if score < best_score:
                best_score = score
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

        
        if qubit_depth is not None:
            best_swap = _select_swap_depth(
                gates, log_to_phy, phy_to_log, adj, dist, num_q, qubit_depth)
        else:
            best_swap = _select_swap_size(
                gates, log_to_phy, phy_to_log, adj, edge_set, dist, num_q)

        
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



#  第五部分：后处理 —— SWAP 化简


def _internal_check_eq(cnot_list, connectivity, swaps):
   
    gate_list = list(cnot_list)
    swaps_copy = list(swaps)

    
    edge_set = set()
    all_q = set()
    for a, b in connectivity:
        edge_set.add((a, b))
        edge_set.add((b, a))
        all_q.add(a)
        all_q.add(b)
    num_q = max(all_q) + 1

   
    for s0, s1 in swaps_copy:
        if (s0, s1) not in edge_set:
            return False

    phy_to_log = list(range(num_q))

    while gate_list:
        qubits_ocpy = [False] * num_q
        exe_idx = -1
        for i, (q0, q1) in enumerate(gate_list):
            if all(qubits_ocpy):
                break
            if (not qubits_ocpy[q0]) and (not qubits_ocpy[q1]):
                q_phy0 = phy_to_log.index(q0)
                q_phy1 = phy_to_log.index(q1)
                if (q_phy0, q_phy1) in edge_set:
                    exe_idx = i
                    break
            qubits_ocpy[q0] = True
            qubits_ocpy[q1] = True

        if exe_idx >= 0:
            gate_list.pop(exe_idx)
        else:
            if not swaps_copy:
                return False
            s0, s1 = swaps_copy.pop(0)
            q0, q1 = phy_to_log[s0], phy_to_log[s1]
            phy_to_log[s0], phy_to_log[s1] = q1, q0

    return True


def _internal_get_depth(cnot_list, connectivity, swaps):
    
    gate_list = list(cnot_list)
    swaps_copy = list(swaps)

    # 构建边集
    edge_set = set()
    all_q = set()
    for a, b in connectivity:
        edge_set.add((a, b))
        edge_set.add((b, a))
        all_q.add(a)
        all_q.add(b)
    num_q = max(all_q) + 1

    qbt_depth = [0] * num_q
    phy_to_log = list(range(num_q))

    while gate_list:
        
        qubits_ocpy = [False] * num_q
        exe_idx = -1
        for i, (q0, q1) in enumerate(gate_list):
            if all(qubits_ocpy):
                break
            if (not qubits_ocpy[q0]) and (not qubits_ocpy[q1]):
                q_phy0 = phy_to_log.index(q0)
                q_phy1 = phy_to_log.index(q1)
                if (q_phy0, q_phy1) in edge_set:
                    exe_idx = i
                    break
            qubits_ocpy[q0] = True
            qubits_ocpy[q1] = True

        if exe_idx >= 0:
            q0, q1 = gate_list.pop(exe_idx)
            q0_phy = phy_to_log.index(q0)
            q1_phy = phy_to_log.index(q1)
            depth_nex = max(qbt_depth[q0_phy], qbt_depth[q1_phy]) + 1
            qbt_depth[q0_phy] = qbt_depth[q1_phy] = depth_nex
        else:
            if not swaps_copy:
                return 10 ** 9  
            s0, s1 = swaps_copy.pop(0)
            q0, q1 = phy_to_log[s0], phy_to_log[s1]
            phy_to_log[s0], phy_to_log[s1] = q1, q0
            depth_nex = max(qbt_depth[s0], qbt_depth[s1]) + 3
            qbt_depth[s0] = qbt_depth[s1] = depth_nex

    return max(qbt_depth) if qbt_depth else 0


def _simplify_swaps(swaps, cnot_list, connectivity, use_depth=False):
    
    if not swaps:
        return swaps

    original_depth = None
    if use_depth:
        original_depth = _internal_get_depth(cnot_list, connectivity, swaps)

    for _ in range(10):
        changed = False

        i = len(swaps) - 1
        while i >= 0:
            candidate = swaps[:i] + swaps[i + 1:]
            if _internal_check_eq(cnot_list, connectivity, candidate):
                if use_depth:
                    new_depth = _internal_get_depth(cnot_list, connectivity, candidate)
                    if new_depth > original_depth:
                        i -= 1
                        continue  
                swaps.pop(i)
                changed = True
            i -= 1

        if not changed:
            break

    return swaps



#  第六部分：主函数


def main_qm(cnot_list, connectivities, obj):
    """
    量子线路映射模块主函数。

    参数:
        cnot_list:     CNOT 门列表 [(逻辑qubit, 逻辑qubit), ...]
        connectivities: 硬件拓扑连通性 [(物理qubit, 物理qubit), ...]
        obj:           "size" 优化 SWAP 数量 / "depth" 优化线路深度

    返回:
        SWAP 门列表 [(物理qubit, 物理qubit), ...]
    """
    adj, edge_set, num_q = _build_adjacency(connectivities)
    dist = _bfs_distances(adj, num_q)
    use_depth = (obj == "depth")

    swaps = _run_mapping(cnot_list, adj, edge_set, dist, num_q, use_depth)

  
    swaps = _simplify_swaps(swaps, cnot_list, connectivities, use_depth)

    return swaps


def main_cs(full_path):
    
    return [0.1 + 2j, -2 - 3j]
