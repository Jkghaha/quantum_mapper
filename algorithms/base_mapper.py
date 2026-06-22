"""
映射算法基类
定义所有映射算法的通用接口
"""

from typing import List, Tuple, Dict
from abc import ABC, abstractmethod

from ..core.topology import TopologyGraph
from ..core.circuit import MappingState


class BaseMapper(ABC):
    """量子线路映射算法基类"""
    
    def __init__(self, topology: TopologyGraph):
        self.topology = topology
    
    @abstractmethod
    def map(self, 
            gate_list: List[Tuple[int, int]], 
            objective: str = "size") -> List[Tuple[int, int]]:
        """
        执行线路映射
        
        Args:
            gate_list: 2-qubit门列表
            objective: 优化目标 "size" 或 "depth"
        
        Returns:
            SWAP门列表
        """
        pass
    
    def _get_num_logical_qubits(self, gate_list: List[Tuple[int, int]]) -> int:
        """从门列表推断逻辑比特数"""
        if not gate_list:
            return 0
        return max(max(q0, q1) for q0, q1 in gate_list) + 1
    
    def _initialize_mapping(self, num_qubits: int) -> Dict[int, int]:
        """
        生成初始映射策略（可被子类重写）
        默认使用顺序映射
        """
        physical = self.topology.qubit_list[:num_qubits]
        return {i: p for i, p in enumerate(physical)}
