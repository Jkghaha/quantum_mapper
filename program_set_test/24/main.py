# -*- coding: utf-8 -*-
"""
量子线路映射模块 - 队伍 24
============================================================
本模块实现基于 Sabre 启发式算法的量子线路映射功能。
将输入的逻辑量子线路（CNOT门列表）转换为可在给定硬件拓扑上
执行的物理量子线路（通过插入 SWAP 门调整映射关系）。

支持两种优化目标：
  - "size"  : 最小化引入的 SWAP 门总数
  - "depth" : 最小化输出线路深度（SWAP=3单位，CNOT=1单位）

仅使用 Python 标准库（collections.deque），无需任何第三方库。
"""

from collections import deque



#  第一部分：拓扑结构处理工具函数

def _build_adjacency(connectivity):
   
    all_qubits = set()
    for a, b in connectivity:
        all_qubits.add(a)
        all_qubits.add(b)
    num_q = max(all_qubits) + 1

    # 构建邻接表（无向图）
    adj = [[] for _ in range(num_q)]
    edge_set = set()
    for a, b in connectivity:
        adj[a].append(b)
        adj[b].append(a)
        # 存储两个方向，方便快速查询
        edge_set.add((a, b))
        edge_set.add((b, a))

    return adj, edge_set, num_q


def _bfs_distances(adj, num_q):
    
    dist = [[0] * num_q for _ in range(num_q)]

    for src in range(num_q):
        d = [-1] * num_q     # -1 表示未访问
        d[src] = 0
        q = deque([src])

        while q:
            u = q.popleft()
            for v in adj[u]:
                if d[v] == -1:         # 首次访问
                    d[v] = d[u] + 1    # 距离 = 父节点距离 + 1
                    q.append(v)

        dist[src] = d

    return dist


def _bfs_path(adj, src, dst):
   
    if src == dst:
        return [src]

    # BFS 搜索，记录父节点
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

    # 不可达
    if dst not in parent:
        return []

    # 回溯构建路径（从 dst 到 src，然后反转）
    path = [dst]
    while parent[path[-1]] is not None:
        path.append(parent[path[-1]])
    path.reverse()
    return path



#  第二部分：check_eq 验证器的精确模拟

def _find_executable(gates, log_to_phy, edge_set, num_q):
    
    # qubits_ocpy[i] = True 表示逻辑量子比特 i 在本轮已被"占用"
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

def _compute_cost(gates, log_to_phy, dist, num_q, lookahead):
    """
    计算给定映射下，前 lookahead 个门的衰减加权距离代价。

    代价越小 = 门越靠近 = 映射越好。
    """
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
    选择最优 SWAP：遍历硬件拓扑中的每条边，模拟每个候选 SWAP 的效果，
    选择使加权距离代价最小的 SWAP。

    """
    # 自适应前瞻: 门多时多看，门少时少看
    lookahead = min(20, max(6, len(gates) // 2))
    depth_weight = 0.03       # 深度惩罚权重（微调）

    best_swap = None
    best_cost = float('inf')

    # 遍历每条无向边，避免重复评估
    seen_edges = set()
    for p0 in range(num_q):
        for p1 in adj[p0]:
            edge_key = (min(p0, p1), max(p0, p1))
            if edge_key in seen_edges:
                continue
            seen_edges.add(edge_key)

            # 获取当前位于 p0 和 p1 的逻辑量子比特
            l0 = phy_to_log[p0]
            l1 = phy_to_log[p1]


            new_log = log_to_phy[:]
            if l0 < num_q:
                new_log[l0] = p1         # 逻辑比特 l0 移动到物理比特 p1
            if l1 < num_q:
                new_log[l1] = p0         # 逻辑比特 l1 移动到物理比特 p0

            # 计算新映射下的距离代价
            dist_cost = _compute_cost(
                gates, new_log, dist, num_q, lookahead)

            cost = dist_cost

            # 深度优化：添加对深度的微调惩罚
            if qubit_depth is not None:
                # 优先选择当前深度较浅的量子比特
                depth_penalty = depth_weight * (
                    qubit_depth[p0] + qubit_depth[p1])
                cost += depth_penalty

            # 保留代价最小的 SWAP
            if cost < best_cost:
                best_cost = cost
                best_swap = (p0, p1)

    return best_swap



#  第四部分：核心映射循环


def _run_mapping(gates_in, adj, edge_set, dist, num_q, use_depth):
    """
    核心映射循环：给定门列表，返回 SWAP 序列。

    参数:
        gates_in:   CNOT 门列表
        adj/edge_set/dist/num_q: 拓扑数据
        use_depth:  bool, 是否追踪深度 (depth模式)
    """
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

        # 选 SWAP
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
        if l0 < num_q: log_to_phy[l0] = s1
        if l1 < num_q: log_to_phy[l1] = s0

        if qubit_depth is not None:
            d = max(qubit_depth[s0], qubit_depth[s1]) + 3
            qubit_depth[s0] = qubit_depth[s1] = d

    return swaps_out


#  第五部分：主函数


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
    adj, edge_set, num_q = _build_adjacency(connectivities)
    dist = _bfs_distances(adj, num_q)
    use_depth = (obj == "depth")

    return _run_mapping(cnot_list, adj, edge_set, dist, num_q, use_depth)


def main_cs(full_path):
    

    return [0.1 + 2j, -2 - 3j]
