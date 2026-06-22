# Quantum Mapper - 量子线路编译工具

## 项目简介

基于 Python 的量子线路映射模块，用于将逻辑量子线路转换为符合硬件拓扑约束的物理线路，并针对 **SWAP 门数量** 和 **线路深度** 进行优化。

## 课程信息

- 课程: 应用开发实践
- 团队: [待填写]
- 时间: 2026年6月

## 目录结构

```
quantum_mapper/
├── main.py                 # 入口文件，包含 main_qm 函数
├── core/                   # 核心数据结构
│   ├── gate.py            # 量子门定义
│   ├── topology.py        # 硬件拓扑图
│   └── circuit.py         # 量子线路表示
├── algorithms/             # 映射算法
│   ├── base_mapper.py     # 基类定义
│   ├── sabre.py           # SABRE 算法
│   └── optimizer.py       # 优化策略
├── utils/                  # 工具函数
└── tests/                  # 测试代码
```

## 接口规范

```python
def main_qm(gate_list: List[Tuple[int, int]],
            topology: List[Tuple[int, int]],
            objective: str) -> List[Tuple[int, int]]:
    """
    量子线路映射主函数
    
    Args:
        gate_list: 2量子比特门列表 [(q0, q1), ...]
        topology:  硬件拓扑边列表 [(p0, p1), ...]
        objective: 优化目标 "size" 或 "depth"
    
    Returns:
        SWAP门列表 [(s_i0, s_i1), ...]
    """
```

## 测试环境

- OS: Windows
- Python: Anaconda (标准库)
- CPU: Intel i9-14900k
- RAM: 128GB

## 运行时间限制

5 分钟 / 20 个测试线路（每线路 ≤ 200 门）

## Git 提交规范

```
feat: 新功能
fix: 修复bug
refactor: 重构
perf: 性能优化
test: 测试相关
docs: 文档更新
```

## 开发日志

### 2026-06-22
- [x] 初始化项目结构
- [x] 创建 Git 仓库
