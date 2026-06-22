"""
SABRE 算法实现
参考论文: SABRE: Toward Practical Quantum Circuit Mapping
"""

from typing import List, Tuple, Dict, Set, Optional
from random import choice, randint, random

from .base_mapper import BaseMapper
from ..core.topology import TopologyGraph
from ..core.circuit import MappingState, QuantumCircuit


class SabreMapper(BaseMapper):
    """
    SABRE (Swapping Based Routing) 映射算法
    
    特点:
    - 基于启发式的 SWAP 插入策略
    - 考虑未来门的影响（lookahead）
    - 支持 decay 机制动态调整权重
    """
    
    def __init__(self, 
                 topology: TopologyGraph,
                 decay: float = 0.6,
                 decay_interval: int = 10,
                 use_lookahead: bool = True,
                 lookahead_window: int = 20):
        """
        初始化 SABRE 映射器
        
        Args:
            topology: 硬件拓扑
            decay: 衰减系数 (0-1)，控制权重更新速率
            decay_interval: 衰减间隔（处理多少门后衰减一次）
            use_lookahead: 是否使用前视窗口
            lookahead_window: 前视窗口大小
        """
        super().__init__(topology)
        self.decay = decay
        self.decay_interval = decay_interval
        self.use_lookahead = use_lookahead
        self.lookahead_window = lookahead_window
    
    def map(self, 
            gate_list: List[Tuple[int, int]], 
            objective: str = "size") -> List[Tuple[int, int]]:
        """执行 SABRE 映射"""
        
        num_qubits = self._get_num_logical_qubits(gate_list)
        state = MappingState(self.topology, num_qubits)
        
        # 初始映射：使用简单贪心策略
        initial_mapping = self._compute_initial_mapping(gate_list, num_qubits)
        state.initialize_mapping(initial_mapping)
        
        # 初始化 SWAP 权重（用于打破平局）
        swap_weight: Dict[Tuple[int, int], float] = {}
        for edge in self.topology.edges:
            key = tuple(sorted(edge))
            swap_weight[key] = 1.0
        
        # 遍历每个门
        gate_idx = 0
        for lq0, lq1 in gate_list:
            # 如果当前映射下可以执行，继续
            if state.can_execute_gate(lq0, lq1):
                gate_idx += 1
                continue
            
            # 需要插入 SWAP
            best_swap = self._select_swap(
                state, lq0, lq1, gate_list, gate_idx, 
                swap_weight, objective
            )
            
            if best_swap:
                state.apply_swap(best_swap[0], best_swap[1])
                
                # 更新 SWAP 权重
                key = tuple(sorted(best_swap))
                swap_weight[key] *= self.decay
                
                # 周期性重置权重
                if gate_idx % self.decay_interval == 0:
                    for k in swap_weight:
                        swap_weight[k] = max(swap_weight[k], 1.0)
            
            # 再次检查是否可执行
            if not state.can_execute_gate(lq0, lq1):
                # 可能需要多个SWAP，简化处理：再试一次
                best_swap = self._select_swap(
                    state, lq0, lq1, gate_list, gate_idx,
                    swap_weight, objective
                )
                if best_swap:
                    state.apply_swap(best_swap[0], best_swap[1])
            
            gate_idx += 1
        
        return state.swap_list
    
    def _compute_initial_mapping(
        self, 
        gate_list: List[Tuple[int, int]], 
        num_qubits: int
    ) -> Dict[int, int]:
        """
        计算初始映射
        使用简单的频率分析：将交互频繁的逻辑比特映射到相邻的物理比特
        """
        # 统计每对逻辑比特的交互次数
        interaction_count: Dict[Tuple[int, int], int] = {}
        for q0, q1 in gate_list:
            key = tuple(sorted([q0, q1]))
            interaction_count[key] = interaction_count.get(key, 0) + 1
        
        # 按交互频次排序逻辑比特对
        sorted_pairs = sorted(interaction_count.items(), key=lambda x: -x[1])
        
        # 简化策略：使用顺序映射作为初始值
        physical = self.topology.qubit_list[:num_qubits]
        return {i: p for i, p in enumerate(physical)}
    
    def _select_swap(
        self,
        state: MappingState,
        current_lq0: int,
        current_lq1: int,
        gate_list: List[Tuple[int, int]],
        current_gate_idx: int,
        swap_weight: Dict[Tuple[int, int], float],
        objective: str
    ) -> Optional[Tuple[int, int]]:
        """
        选择最优 SWAP 门
        
        使用启发式函数评估候选 SWAP 的效果
        """
        p0 = state.get_physical_position(current_lq0)
        p1 = state.get_physical_position(current_lq1)
        
        if p0 is None or p1 is None:
            return None
        
        # 获取候选 SWAP（两个物理比特邻居的并集）
        candidates: Set[Tuple[int, int]] = set()
        
        # 在 p0 的邻居中寻找有利的 SWAP
        for neighbor in self.topology.get_neighbors(p0):
            candidates.add(tuple(sorted((p0, neighbor))))
        
        for neighbor in self.topology.get_neighbors(p1):
            candidates.add(tuple(sorted((p1, neighbor))))
        
        if not candidates:
            return None
        
        # 评估每个候选 SWAP
        best_score = float('inf')
        best_swap = None
        
        for swap in candidates:
            score = self._evaluate_swap(
                state, swap, current_lq0, current_lq1,
                gate_list, current_gate_idx, objective
            )
            
            # 加入权重扰动（避免局部最优）
            weighted_score = score / swap_weight.get(swap, 1.0)
            
            if weighted_score < best_score:
                best_score = weighted_score
                best_swap = swap
        
        return best_swap
    
    def _evaluate_swap(
        self,
        state: MappingState,
        swap: Tuple[int, int],
        current_lq0: int,
        current_lq1: int,
        gate_list: List[Tuple[int, int]],
        current_gate_idx: int,
        objective: str
    ) -> float:
        """
        评估执行某个 SWAP 后的效果
        返回分数，越低越好
        """
        sp0, sp1 = swap
        
        # 模拟执行该 SWAP 后的状态变化
        l0_at_sp0 = state.physical_to_logical.get(sp0)
        l0_at_sp1 = state.physical_to_logical.get(sp1)
        
        # 计算交换后当前门的距离改善
        new_p_for_lq0 = sp1 if l0_at_sp0 == current_lq0 else (
                         sp0 if l0_at_sp1 == current_lq0 else
                         state.get_physical_position(current_lq0))
        
        new_p_for_lq1 = sp0 if l0_at_sp1 == current_lq1 else (
                         sp1 if l0_at_sp0 == current_lq1 else
                         state.get_physical_position(current_lq1))
        
        if new_p_for_lq0 is None or new_p_for_lq1 is None:
            return float('inf')
        
        old_dist = self.topology.distance(
            state.get_physical_position(current_lq0),
            state.get_physical_position(current_lq1)
        ) if state.get_physical_position(current_lq0) is not None and \
           state.get_physical_position(current_lq1) is not None else float('inf')
        
        new_dist = self.topology.distance(new_p_for_lq0, new_p_for_lq1)
        
        # 基础分数：距离改善
        score = new_dist
        
        # 如果使用前视窗口，考虑未来门的影响
        if self.use_lookahead:
            future_impact = 0.0
            end_idx = min(current_gate_idx + self.lookahead_window, len(gate_list))
            weight_factor = 1.0
            
            for idx in range(current_gate_idx, end_idx):
                fq0, fq1 = gate_list[idx]
                
                # 模拟后的位置估算
                fp0 = sp1 if l0_at_sp0 == fq0 else (
                      sp0 if l0_at_sp1 == fq0 else
                      state.get_physical_position(fq0))
                
                fp1 = sp0 if l0_at_sp1 == fq1 else (
                      sp1 if l0_at_sp0 == fq1 else
                      state.get_physical_position(fq1))
                
                if fp0 is not None and fp1 is not None:
                    future_dist = self.topology.distance(fp0, fp1)
                    future_impact += weight_factor * future_dist
                
                weight_factor *= 0.9  # 衰减因子
            
            score += 0.5 * future_impact
        
        return score


class RandomSabreMapper(SabreMapper):
    """
    带随机重启的 SABRE 映射器
    通过多次随机初始化选择最优结果
    """
    
    def __init__(self, 
                 topology: TopologyGraph,
                 num_trials: int = 10,
                 **kwargs):
        super().__init__(topology, **kwargs)
        self.num_trials = num_trials
    
    def map(self,
            gate_list: List[Tuple[int, int]], 
            objective: str = "size") -> List[Tuple[int, int]]:
        """多次运行取最优"""
        best_result = None
        best_cost = float('inf')
        
        for _ in range(self.num_trials):
            result = super().map(gate_list, objective)
            
            # 计算代价
            if objective == "size":
                cost = len(result)
            else:  # depth
                cost = self._estimate_depth(result)
            
            if cost < best_cost:
                best_cost = cost
                best_result = result
        
        return best_result if best_result else []
    
    def _estimate_depth(self, swap_list: List[Tuple[int, int]]) -> int:
        """粗略估计线路深度（简化计算）"""
        if not swap_list:
            return 0
        
        # 相邻非冲突SWAP可并行执行
        depth = 1
        last_swaps = {swap_list[0]}
        
        for swap in swap_list[1:]:
            s0, s1 = swap
            # 检查是否与上一层的所有SWAP冲突
            conflict = any(s0 in ls or s1 in ls for ls in last_swaps)
            if conflict:
                depth += 1
                last_swaps = {swap}
            else:
                last_swaps.add(swap)
        
        return depth
