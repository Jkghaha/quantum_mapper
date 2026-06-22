"""
优化策略模块
提供多种优化方法改进映射结果质量
"""

from typing import List, Tuple, Dict, Optional, Callable
from random import random, randint, shuffle

from ..core.topology import TopologyGraph


def optimize_by_random_restart(
    mapper_func: Callable,
    gate_list: List[Tuple[int, int]],
    topology: TopologyGraph,
    objective: str = "size",
    num_iterations: int = 20,
    seed: int = None
) -> List[Tuple[int, int]]:
    """
    随机重启优化
    
    多次运行映射算法，选择最优结果
    """
    if seed is not None:
        import random as rnd
        rnd.seed(seed)
    
    best_result = None
    best_cost = float('inf')
    
    for i in range(num_iterations):
        result = mapper_func(gate_list, topology, objective)
        cost = len(result) if objective == "size" else estimate_depth(result)
        
        if cost < best_cost:
            best_cost = cost
            best_result = result
    
    return best_result if best_result else []


def optimize_swap_sequence(
    swap_list: List[Tuple[int, int]],
    topology: TopologyGraph,
    max_iterations: int = 100
) -> List[Tuple[int, int]]:
    """
    局部搜索优化已生成的 SWAP 序列
    尝试消除冗余 SWAP（如连续相同SWAP的对消）
    """
    if not swap_list:
        return swap_list
    
    optimized = list(swap_list)
    improved = True
    iteration = 0
    
    while improved and iteration < max_iterations:
        improved = False
        iteration += 1
        
        # 消除相邻的逆操作 (a,b) -> (a,b) 可对消
        i = 0
        while i < len(optimized) - 1:
            s1 = tuple(sorted(optimized[i]))
            s2 = tuple(sorted(optimized[i + 1]))
            
            if s1 == s2:
                # 检查是否为逆操作
                if (optimized[i] == optimized[i+1].__class__(optimized[i+1][1], optimized[i+0][0]) or
                    sorted(optimized[i]) == sorted(optimized[i+1])):
                    optimized.pop(i)
                    optimized.pop(i)
                    improved = True
                    continue
            i += 1
    
    return optimized


def estimate_depth(swap_list: List[Tuple[int, int]]) -> int:
    """
    估计 SWAP 序列对应的线路深度
    考虑并行执行可能性
    """
    if not swap_list:
        return 0
    
    layers: List[set] = []
    
    for swap in swap_list:
        s0, s1 = swap
        placed = False
        
        for layer in layers:
            # 检查是否与层内所有SWAP无冲突（不共享物理比特）
            conflict = any(
                s0 in existing_swap or s1 in existing_swap 
                for existing_swap in layer
            )
            if not conflict:
                layer.add(swap)
                placed = True
                break
        
        if not placed:
            layers.append({swap})
    
    return len(layers)


def compute_cost(
    swap_list: List[Tuple[int, int]], 
    objective: str
) -> float:
    """计算 SWAP 序列的代价"""
    if objective == "size":
        return len(swap_list)
    elif objective == "depth":
        return estimate_depth(swap_list)
    else:
        return len(swap_list)


# ==================== 高级优化策略 ====================

class SimulatedAnnealingOptimizer:
    """
    模拟退火优化器
    用于在已有解的基础上进行局部优化
    """
    
    def __init__(
        self,
        topology: TopologyGraph,
        initial_temp: float = 100.0,
        cooling_rate: float = 0.95,
        min_temp: float = 1.0,
        iterations_per_temp: int = 50
    ):
        self.topology = topology
        self.initial_temp = initial_temp
        self.cooling_rate = cooling_rate
        self.min_temp = min_temp
        self.iterations_per_temp = iterations_per_temp
    
    def optimize(
        self,
        initial_solution: List[Tuple[int, int]],
        gate_list: List[Tuple[int, int]],
        objective: str = "size"
    ) -> List[Tuple[int, int]]:
        """
        执行模拟退火优化
        """
        current = list(initial_solution)
        best = list(initial_solution)
        
        current_cost = compute_cost(current, objective)
        best_cost = current_cost
        
        temp = self.initial_temp
        
        while temp > self.min_temp:
            for _ in range(self.iterations_per_temp):
                # 生成邻域解：随机交换/插入/删除一个SWAP
                neighbor = self._generate_neighbor(current)
                
                neighbor_cost = compute_cost(neighbor, objective)
                delta = neighbor_cost - current_cost
                
                # 接受准则
                if delta < 0 or random() < self._exp(-delta / temp):
                    current = neighbor
                    current_cost = neighbor_cost
                    
                    if current_cost < best_cost:
                        best = list(current)
                        best_cost = current_cost
            
            temp *= self.cooling_rate
        
        return best
    
    def _generate_neighbor(self, solution: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """生成邻域解"""
        if not solution:
            return solution
        
        neighbor = list(solution)
        action = randint(0, 2)
        
        if action == 0 and len(neighbor) > 1:
            # 随机交换两个SWAP的位置
            i, j = randint(0, len(neighbor)-1), randint(0, len(neighbor)-1)
            neighbor[i], neighbor[j] = neighbor[j], neighbor[i]
        elif action == 1:
            # 随机修改一个SWAP
            if neighbor and self.topology.edges:
                idx = randint(0, len(neighbor)-1)
                new_swap = choice(self.topology.edges)
                neighbor[idx] = new_swap
        else:
            # 随机删除或添加一个SWAP
            if len(neighbor) > 0 and random() < 0.5:
                idx = randint(0, len(neighbor)-1)
                neighbor.pop(idx)
            elif self.topology.edges:
                new_swap = choice(self.topology.edges)
                insert_pos = randint(0, len(neighbor))
                neighbor.insert(insert_pos, new_swap)
        
        return neighbor
    
    @staticmethod
    def _exp(x: float) -> float:
        """安全的指数计算"""
        try:
            import math
            return math.exp(x)
        except OverflowError:
            return float('inf')
