"""
量子线路表示与操作
"""

from typing import List, Tuple, Dict, Optional
from .gate import QuantumGate
from .topology import TopologyGraph


class QuantumCircuit:
    """量子线路表示"""
    
    def __init__(self, 
                 gates: List[Tuple[int, int]] = None,
                 num_logical_qubits: int = 0):
        """
        初始化量子线路
        
        Args:
            gates: 2-qubit门列表
            num_logical_qubits: 逻辑比特数（0表示自动推断）
        """
        self.gates: List[QuantumGate] = []
        self.num_logical_qubits = num_logical_qubits
        
        if gates:
            for q0, q1 in gates:
                self.add_gate(q0, q1)
            
            if num_logical_qubits == 0:
                self._infer_num_qubits()
    
    def _infer_num_qubits(self):
        """从门列表推断逻辑比特数"""
        if not self.gates:
            self.num_logical_qubits = 0
            return
        max_q = max(max(g.q0, g.q1) for g in self.gates)
        self.num_logical_qubits = max_q + 1
    
    def add_gate(self, q0: int, q1: int, gate_type: str = "CNOT"):
        """添加一个2-量子比特门"""
        gate = QuantumGate(q0, q1, gate_type)
        self.gates.append(gate)
        
        new_max = max(q0, q1) + 1
        if new_max > self.num_logical_qubits:
            self.num_logical_qubits = new_max
    
    def get_gate_list(self) -> List[Tuple[int, int]]:
        """获取门列表的元组形式"""
        return [g.to_tuple() for g in self.gates]
    
    def __len__(self):
        return len(self.gates)
    
    def __repr__(self) -> str:
        return f"QuantumCircuit(qubits={self.num_logical_qubits}, gates={len(self.gates)})"


class MappingState:
    """
    映射状态追踪
    维护逻辑比特到物理比特的映射关系
    """
    
    def __init__(self, topology: TopologyGraph, logical_qubits: int):
        """
        初始化映射状态
        
        Args:
            topology: 硬件拓扑图
            logical_qubits: 逻辑比特数量
        """
        self.topology = topology
        self.logical_qubits = logical_qubits
        # 逻辑 → 物理映射
        self.logical_to_physical: Dict[int, int] = {}
        # 物理 → 逻辑反向映射
        self.physical_to_logical: Dict[int, int] = {}
        # 已插入的 SWAP 门列表
        self.swap_list: List[Tuple[int, int]] = []
    
    def initialize_mapping(self, mapping: Dict[int, int] = None):
        """
        初始化比特映射
        
        Args:
            mapping: {逻辑比特: 物理比特}，None则使用顺序映射
        """
        physical_qubits = self.topology.qubit_list[:self.logical_qubits]
        
        if mapping is None:
            # 默认顺序映射
            for i, p in enumerate(physical_qubits):
                self.logical_to_physical[i] = p
                self.physical_to_logical[p] = i
        else:
            self.logical_to_physical = dict(mapping)
            self.physical_to_logical = {v: k for k, v in mapping.items()}
    
    def apply_swap(self, p0: int, p1: int):
        """
        应用 SWAP 门，更新映射状态
        
        Args:
            p0, p1: 交换的两个物理比特
        """
        # 更新映射：交换两个物理比特对应的逻辑比特
        l0 = self.physical_to_logical.get(p0)
        l1 = self.physical_to_logical.get(p1)
        
        if l0 is not None:
            self.logical_to_physical[l0] = p1
        if l1 is not None:
            self.logical_to_logical[l1] = p0
        
        # 更新反向映射
        self.physical_to_logical[p0] = l1
        self.physical_to_logical[p1] = l0
        
        # 记录 SWAP
        self.swap_list.append((p0, p1))
    
    def get_physical_position(self, logical_qubit: int) -> Optional[int]:
        """获取逻辑比特当前映射到的物理比特位置"""
        return self.logical_to_physical.get(logical_qubit)
    
    def can_execute_gate(self, lq0: int, lq1: int) -> bool:
        """判断当前映射下是否可以直接执行该门（两物理比特相邻）"""
        p0 = self.get_physical_position(lq0)
        p1 = self.get_physical_position(lq1)
        
        if p0 is None or p1 is None:
            return False
        
        return self.topology.are_adjacent(p0, p1)
