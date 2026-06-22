"""
通用工具函数
"""

from typing import List, Tuple, Dict, Any
import json


def format_swap_list(swap_list: List[Tuple[int, int]], indent: int = 0) -> str:
    """格式化 SWAP 列表为可读字符串"""
    prefix = " " * indent
    if not swap_list:
        return f"{prefix}[]"
    
    items = [f"({s0}, {s1})" for s0, s1 in swap_list]
    return f"{prefix}[{', '.join(items)}]"


def validate_gate_format(gate_list: List[Tuple[int, int]]) -> Tuple[bool, str]:
    """
    验证门列表格式是否合法
    
    Returns:
        (is_valid, error_message)
    """
    if not isinstance(gate_list, list):
        return False, "gate_list must be a list"
    
    for i, gate in enumerate(gate_list):
        if not isinstance(gate, tuple) and not isinstance(gate, list):
            return False, f"gate[{i}] must be a tuple or list"
        if len(gate) != 2:
            return False, f"gate[{i}] must have exactly 2 elements"
        if not isinstance(gate[0], int) or not isinstance(gate[1], int):
            return False, f"gate[{i}] qubits must be integers"
        if gate[0] < 0 or gate[1] < 0:
            return False, f"gate[{i}] qubit indices must be non-negative"
        if gate[0] == gate[1]:
            return False, f"gate[{i]} cannot operate on same qubit"
    
    return True, ""


def validate_topology_format(topology: List[Tuple[int, int]]) -> Tuple[bool, str]:
    """验证拓扑结构格式"""
    if not isinstance(topology, list):
        return False, "topology must be a list"
    
    seen_edges = set()
    for i, edge in enumerate(topology):
        if len(edge) != 2:
            return False, f"edge[{i}] must have exactly 2 nodes"
        
        sorted_edge = tuple(sorted(edge))
        if sorted_edge in seen_edges:
            # 允许重复边，但给出警告
            pass
        seen_edges.add(sorted_edge)
    
    return True, ""


def validate_output_format(swap_list: List[Tuple[int, int]]) -> Tuple[bool, str]:
    """验证输出 SWAP 列表格式"""
    if not isinstance(swap_list, list):
        return False, "output must be a list"
    
    for i, swap in enumerate(swap_list):
        if not isinstance(swap, tuple) and not isinstance(swap, list):
            return False, f"swap[{i}] must be a tuple or list"
        if len(swap) != 2:
            return False, f"swap[{i}] must have exactly 2 elements"
    
    return True, ""


def count_gates_by_qubit(gate_list: List[Tuple[int, int]]) -> Dict[int, int]:
    """统计每个逻辑比特参与的门数量"""
    counts: Dict[int, int] = {}
    for q0, q1 in gate_list:
        counts[q0] = counts.get(q0, 0) + 1
        counts[q1] = counts.get(q1, 0) + 1
    return counts


def get_interaction_graph(gate_list: List[Tuple[int, int]]) -> Dict[int, Set[int]]:
    """构建门交互图：如果两个逻辑比特有直接交互则相连"""
    graph: Dict[int, Set[int]] = {}
    for q0, q1 in gate_list:
        if q0 not in graph:
            graph[q0] = set()
        if q1 not in graph:
            graph[q1] = set()
        graph[q0].add(q1)
        graph[q1].add(q0)
    return graph


def compute_circuit_stats(
    original_gates: List[Tuple[int, int]],
    swap_list: List[Tuple[int, int]]
) -> Dict[str, Any]:
    """
    计算线路统计信息
    
    Returns:
        包含各种统计指标的字典
    """
    stats = {
        'original_gate_count': len(original_gates),
        'swap_count': len(swap_list),
        'total_operations': len(original_gates) + len(swap_list),
        'num_logical_qubits': 0,
        'overhead_ratio': 0.0,
    }
    
    if original_gates:
        max_q = max(max(q0, q1) for q0, q1 in original_gates)
        stats['num_logical_qubits'] = max_q + 1
        stats['overhead_ratio'] = len(swap_list) / len(original_gates)
    
    return stats


class Timer:
    """简单计时器上下文管理器"""
    
    import time
    
    def __enter__(self):
        self.start = self.time.perf_counter()
        return self
    
    def __exit__(self, *args):
        self.elapsed = self.time.perf_counter() - self.start
    
    @property
    def seconds(self) -> float:
        return getattr(self, 'elapsed', 0.0)
    
    def __str__(self) -> str:
        elapsed = getattr(self, 'elapsed', 0.0)
        if elapsed < 1.0:
            return f"{elapsed * 1000:.2f} ms"
        elif elapsed < 60.0:
            return f"{elapsed:.2f} s"
        else:
            minutes = int(elapsed // 60)
            seconds = elapsed % 60
            return f"{minutes}m {seconds:.1f}s"
