# -*- coding: utf-8 -*-
"""
BFS 搜索模块 - bfs.py 
基于广度优先搜索的图算法：
  - 全源最短路径距离矩阵（预处理，O(Q*E)）
  - 单源最短路径（回退策略用）
"""

from collections import deque


def all_pairs_distance(adj, num_q):
    
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


def shortest_path(adj, src, dst):
    
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

    # 回溯重建路径
    path = [dst]
    while parent[path[-1]] is not None:
        path.append(parent[path[-1]])
    path.reverse()
    return path
