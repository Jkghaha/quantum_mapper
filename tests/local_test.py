"""
本地测试脚本
用于验证 main_qm 函数的正确性和性能
"""

import sys
import os
import time

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import main_qm
from utils.helpers import (
    validate_gate_format, 
    validate_topology_format,
    validate_output_format,
    compute_circuit_stats,
    Timer
)
from core.topology import TOPOLOGY_4x4, TOPOLOGY_5x4


def run_basic_test():
    """基础功能测试"""
    print("=" * 60)
    print("基础功能测试")
    print("=" * 60)
    
    # 测试用例1: 简单3比特线路，线性拓扑
    test_cases = [
        {
            'name': '简单3比特-线性拓扑',
            'gates': [(0, 1), (1, 2), (0, 2)],
            'topology': [(0, 1), (1, 2), (2, 3)],
            'objective': 'size',
            'expected_swaps_min': 1,  # 至少需要1个SWAP让(0,2)可执行
        },
        {
            'name': '4比特-4x4网格',
            'gates': [(0, 1), (0, 5), (5, 10), (10, 15)],
            'topology': TOPOLOGY_4x4,
            'objective': 'depth',
            'expected_swaps_min': 0,  # 这些门可能已经满足拓扑
        },
        {
            'name': '远距离比特交互',
            'gates': [(0, 15), (1, 14), (7, 8)],
            'topology': TOPOLOGY_4x4,
            'objective': 'size',
            'expected_swaps_min': 2,  # 远距离需要多个SWAP
        },
    ]
    
    passed = 0
    failed = 0
    
    for tc in test_cases:
        print(f"\n[测试] {tc['name']}")
        print(f"  输入门: {tc['gates'][:3]}{'...' if len(tc['gates'])>3 else ''} "
              f"(共{len(tc['gates'])}个)")
        
        # 格式验证
        valid, msg = validate_gate_format(tc['gates'])
        if not valid:
            print(f"  ❌ 门格式错误: {msg}")
            failed += 1
            continue
        
        # 执行映射
        with Timer() as t:
            result = main_qm(tc['gates'], tc['topology'], tc['objective'])
        
        # 输出格式验证
        valid, msg = validate_output_format(result)
        if not valid:
            print(f"  ❌ 输出格式错误: {msg}")
            failed += 1
            continue
        
        stats = compute_circuit_stats(tc['gates'], result)
        
        print(f"  ✅ 执行成功")
        print(f"  SWAP数量: {len(result)}")
        print(f"  开销比: {stats['overhead_ratio']:.2%}")
        print(f"  耗时: {t}")
        
        if len(result) >= tc.get('expected_swaps_min', 0):
            passed += 1
        else:
            print(f"  ⚠️ SWAP数可能不足")
            failed += 1
    
    print(f"\n{'=' * 60}")
    print(f"结果: {passed} 通过, {failed} 失败")
    
    return passed, failed


def run_performance_test():
    """性能基准测试"""
    print("\n" + "=" * 60)
    print("性能基准测试")
    print("=" * 60)
    
    import random
    
    # 模拟大规模线路
    num_gates = 200
    num_qubits = 16
    random.seed(42)
    
    large_gates = [
        (random.randint(0, num_qubits-1), random.randint(0, num_qubits-1))
        for _ in range(num_gates)
    ]
    large_gates = [(q0, q1) for q0, q1 in large_gates if q0 != q1]
    
    print(f"\n[测试] 大规模线路 ({num_qubits}qubit, {len(large_gates)} gates)")
    
    objectives = ['size', 'depth']
    
    for obj in objectives:
        with Timer() as t:
            result = main_qm(large_gates, TOPOLOGY_4x4, obj)
        
        print(f"  目标={obj}: SWAP数={len(result)}, 耗时={t}")
        
        if t.seconds > 15:  # 单个测试不应超过15秒（留余量给完整20个）
            print(f"  ❌ 耗时过长！可能无法通过5分钟/20线路的约束")


def run_correctness_verification():
    """
    正确性验证辅助
    注意：完整的正确性检验需要教师提供的验证程序
    这里只做基本的一致性检查
    """
    print("\n" + "=" * 60)
    print("一致性检查（非完整正确性证明）")
    print("=" * 60)
    
    from core.topology import TopologyGraph
    from core.circuit import MappingState
    
    gates = [(0, 1), (2, 3), (0, 5), (3, 10)]
    topology_edges = TOPOLOGY_4x4
    objective = 'size'
    
    print(f"\n输入门: {gates}")
    
    # 获取映射结果
    swaps = main_qm(gates, topology_edges, objective)
    
    # 构建拓扑图并模拟执行
    topo = TopologyGraph(topology_edges)
    state = MappingState(topo, max(max(g[0], g[1]) for g in gates) + 1)
    state.initialize_mapping()
    
    # 应用SWAP
    for swap in swaps:
        state.apply_swap(swap[0], swap[1])
    
    # 验证每个门在最终映射下是否可执行
    all_executable = True
    for i, (lq0, lq1) in enumerate(gates):
        can_exec = state.can_execute_gate(lq0, lq1)
        status = "✅" if can_exec else "❌"
        print(f"  {status} Gate[{i}] ({lq0}, {lq1}): 可执行={can_exec}")
        if not can_exec:
            all_executable = False
    
    if all_executable:
        print("\n✅ 所有门在应用SWAP后均可执行")
    else:
        print("\n⚠️ 部分门仍不可执行，映射算法可能有误")


def main():
    """运行所有测试"""
    print("#" * 60)
    print("# Quantum Mapper 本地测试")
    print(f"# 运行时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("#" * 60)
    
    p1, f1 = run_basic_test()
    run_performance_test()
    run_correctness_verification()
    
    print("\n" + "#" * 60)
    print("# 测试完成")
    print("#" * 60)


if __name__ == "__main__":
    main()
