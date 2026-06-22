"""
硬件拓扑结构
支持邻接查询、最短路径计算等操作
"""

from typing import List, Tuple, Dict, Set, Optional
from collections import deque


class TopologyGraph:
    """量子计算机硬件拓扑图（无向图）"""
    
    def __init__(self, edges: List[Tuple[int, int]]):
        """
        初始化拓扑图
        
        Args:
            edges: 边列表，每条边 (u, v) 表示物理比特 u 和 v 连通
        """
        self.edges = edges
        self.adj: Dict[int, Set[int]] = {}
        self._build_graph()
    
    def _build_graph(self):
        """构建邻接表"""
        for u, v in self.edges:
            if u not in self.adj:
                self.adj[u] = set()
            if v not in self.adj:
                self.adj[v] = set()
            self.adj[u].add(v)
            self.adj[v].add(u)
    
    @property
    def num_qubits(self) -> int:
        """返回物理比特数量"""
        return len(self.adj)
    
    @property
    def qubit_list(self) -> List[int]:
        """返回所有物理比特列表"""
        return list(self.adj.keys())
    
    def are_adjacent(self, u: int, v: int) -> bool:
        """判断两个物理比特是否相邻（可直接执行2-qubit门）"""
        return v in self.adj.get(u, set())
    
    def get_neighbors(self, q: int) -> Set[int]:
        """获取某物理比特的所有邻居"""
        return self.adj.get(q, set()).copy()
    
    def shortest_path(self, start: int, end: int) -> List[int]:
        """
        BFS 计算两点间最短路径
        
        Returns:
            从 start 到 end 的路径节点列表（含两端点）
            若不存在路径则返回空列表
        """
        if start == end:
            return [start]
        
        queue = deque([(start, [start])])
        visited = {start}
        
        while queue:
            node, path = queue.popleft()
            for neighbor in self.adj.get(node, set()):
                if neighbor == end:
                    return path + [neighbor]
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        
        return []  # 不可达
    
    def distance(self, u: int, v: int) -> int:
        """返回两物理比特间的最短距离"""
        path = self.shortest_path(u, v)
        return len(path) - 1 if path else float('inf')
    
    def all_pairs_shortest_paths(self) -> Dict[Tuple[int, int], List[int]]:
        """预计算所有节点对的最短路径（缓存用）"""
        paths = {}
        qubits = self.qubit_list
        for i, u in enumerate(qubits):
            for v in qubits[i:]:
                paths[(u, v)] = self.shortest_path(u, v)
                paths[(v, u)] = self.shortest_path(v, u)
        return paths
    
    def __repr__(self) -> str:
        return f"TopologyGraph(qubits={self.num_qubits}, edges={len(self.edges)})"


# 预定义的测试拓扑
TOPOLOGY_4x4: List[Tuple[int, int]] = [
    (0, 1), (0, 4), (1, 2), (1, 5), (2, 3), (2, 6),
    (3, 7), (4, 5), (4, 8), (5, 6), (5, 9), (6, 7),
    (6, 10), (7, 11), (8, 9), (8, 12), (9, 10), (9, 13),
    (10, 11), (10, 14), (11, 15), (12, 13), (13, 14), (14, 15)
]

TOPOLOGY_5x4: List[Tuple[int, int]] = [
    (0, 1), (0, 5), (1, 2), (1, 6), (1, 7), (2, 3), (2, 7),
    (2, 6), (3, 4), (3, 8), (3, 9), (4, 9), (4, 8), (5, 6),
    (5, 10), (5, 11), (6, 7), (6, 11), (6, 10), (7, 8), (7, 12),
    (7, 13), (8, 9), (8, 13), (8, 12), (9, 14), (10, 11), (10, 15),
    (11, 12), (11, 16), (11, 17), (12, 13), (12, 17), (12, 16),
    (13, 14), (13, 18), (13, 19), (14, 19), (14, 18), (15, 16),
    (16, 17), (17, 18), (18, 19)
]
