# -*- coding: utf-8 -*-
"""
check_eq 语义模拟模块
"""


def find_executable(gates, log_to_phy, edge_set, num_q):
    
    qubits_ocpy = [False] * num_q

    for i, (l0, l1) in enumerate(gates):
        # 所有 qubit 都已占用 → 不可能再找到可执行门
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
