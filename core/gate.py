"""
量子门数据结构
"""

from typing import Tuple, Optional
from dataclasses import dataclass


@dataclass
class QuantumGate:
    """2-量子比特门表示"""
    q0: int  # 第一个量子比特
    q1: int  # 第二个量子比特
    gate_type: str = "CNOT"  # 门类型，默认为CNOT
    
    def __post_init__(self):
        # 确保 q0 < q1 以便统一处理
        if self.q0 > self.q1:
            self.q0, self.q1 = self.q1, self.q0
    
    def to_tuple(self) -> Tuple[int, int]:
        """转换为元组形式"""
        return (self.q0, self.q1)
    
    def __repr__(self) -> str:
        return f"{self.gate_type}({self.q0}, {self.q1})"
