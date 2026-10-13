# 文章数值变更台账

旧值取自 Git 提交 `cfe3ee2004da60500140e6fa5ef2200cf3ca98a6`（`cfe3ee2`）；新值取自本次最终复跑的 [metrics.json](../results/metrics.json) 及对应原始文件。所有表格由这两组实际数据计算，未手填压缩尺寸或 token 数。

字节数为 UTF-8；字符数为 Unicode 码点；行数采用 `splitlines()`。表内 `旧 → 新` 对应两个版本。模块行数包含注释与空行，不含 `shop/__init__.py`。工具 token 的统计边界不同，不能跨行当作同一计费口径。

本次数值快照的 `results/metrics.json` SHA-256：`03b54d7018c3d5d9a9ab828bde8cced6aed5d0d0f188ed48bee3abf54a7b6478`。

## 项目规模与源码

| 指标 | 旧 → 新 |
| --- | --- |
| 业务模块数 | 5 → 5 |
| 业务源码行数 | 288 → 288 |
| 测试文件数 | 4 → 4 |
| 测试源码行数 | 323 → 300 |
| 测试函数数（参数化展开前） | 54 → 46 |
| pytest 收集实例数（参数化展开后） | 87 → 67 |
| 通过实例 | 86 → 66 |
| 失败实例 | 1 → 1 |

| 业务文件 | 字节 | 字符 | 行 |
| --- | --- | --- | --- |
| `shop/models.py` | 1,584 → 1,584 | 1,584 → 1,584 | 68 → 68 |
| `shop/coupons.py` | 2,066 → 2,066 | 2,066 → 2,066 | 67 → 67 |
| `shop/shipping.py` | 818 → 818 | 818 → 818 | 27 → 27 |
| `shop/tax.py` | 556 → 556 | 556 → 556 | 15 → 15 |
| `shop/cart.py` | 3,817 → 3,817 | 3,817 → 3,817 | 111 → 111 |

## 输入尺寸

RTK 自己执行 pytest，并注入 `--tb=short -q -rxX`；它的 token 输入估计对应 recalled 文件，而不是共享的 verbose pytest 文本。

| 输入 | 字节 | 字符 | 行 |
| --- | --- | --- | --- |
| [data/issues.json](../data/issues.json) | 38,361 → 34,259 | 38,361 → 34,259 | 1,265 → 1,265 |
| [data/app.log](../data/app.log) | 30,553 → 30,553 | 30,553 → 30,553 | 300 → 300 |
| [data/app_synonyms.log](../data/app_synonyms.log) | 30,982 → 30,982 | 30,982 → 30,982 | 303 → 303 |
| [results/pytest/raw.txt](../results/pytest/raw.txt) | 8,087 → 6,426 | 8,087 → 6,426 | 109 → 89 |
| [RTK recalled pytest](../results/rtk/pytest.recalled.txt) | 1,053 → 1,026 | 1,053 → 1,026 | 19 → 19 |

## 压缩或筛选输出尺寸

“字节减少”是从该工具对应的输入文件尺寸计算的派生百分比；RTK pytest 使用其 recalled 输入。它不等于 token 减少百分比。

| 输出 | 字节 | 字符 | 行 | 字节减少 |
| --- | --- | --- | --- | --- |
| [rtk/pytest](../results/rtk/pytest.txt) | 279 → 279 | 279 → 279 | 8 → 8 | 73.50% → 72.81% |
| [rtk/issues](../results/rtk/issues.txt) | 461 → 493 | 461 → 493 | 23 → 23 | 98.80% → 98.56% |
| [headroom/pytest](../results/headroom/pytest.txt) | 8,087 → 6,426 | 8,087 → 6,426 | 109 → 89 | 0.00% → 0.00% |
| [headroom/issues](../results/headroom/issues.txt) | 22,610 → 18,530 | 22,610 → 18,530 | 61 → 61 | 41.06% → 45.91% |
| [headroom/smartcrusher_no_query](../results/headroom/smartcrusher_no_query.txt) | 7,701 → 26,313 | 7,701 → 26,313 | 1 → 1 | 79.92% → 23.19% |
| [headroom/smartcrusher_query](../results/headroom/smartcrusher_query.txt) | 7,615 → 26,313 | 7,615 → 26,313 | 1 → 1 | 80.15% → 23.19% |
| [caveman/pytest_auto](../results/caveman/pytest_auto.txt) | 8,087 → 6,426 | 8,087 → 6,426 | 109 → 89 | 0.00% → 0.00% |
| [caveman/pytest_terminal](../results/caveman/pytest_terminal.txt) | 7,194 → 6,093 | 7,146 → 6,065 | 101 → 85 | 11.04% → 5.18% |
| [caveman/issues_no_query](../results/caveman/issues_no_query.txt) | 7,903 → 34,259 | 7,897 → 34,259 | 1 → 1,265 | 79.40% → 0.00% |
| [caveman/issues_query](../results/caveman/issues_query.txt) | 7,903 → 34,259 | 7,897 → 34,259 | 1 → 1,265 | 79.40% → 0.00% |
| [caveman/app_no_query](../results/caveman/app_no_query.txt) | 753 → 753 | 733 → 733 | 6 → 6 | 97.54% → 97.54% |
| [caveman/app_query](../results/caveman/app_query.txt) | 4,778 → 4,778 | 4,672 → 4,672 | 38 → 38 | 84.36% → 84.36% |
| [caveman/app_synonyms_query](../results/caveman/app_synonyms_query.txt) | 4,911 → 4,911 | 4,803 → 4,803 | 39 → 39 | 84.15% → 84.15% |
| [codemode/issues](../results/codemode/issues.txt) | 53 → 53 | 53 → 53 | 1 → 1 | 99.86% → 99.85% |

## 工具报告的 token

RTK 为自己的估计；Headroom `compress` 覆盖完整三条消息；Caveman 使用 `o200k_base` 统计传入内容。直接调用 SmartCrusher 不报告 token；CodeGraph 与 codemode 也没有本次可用的工具 token 数。

| 工具 / 场景 | 输入 token | 输出 token | 减少 token |
| --- | --- | --- | --- |
| `rtk pytest -v` | 264 → 257 | 70 → 70 | 194 → 187 |
| `rtk json` | 9,591 → 8,565 | 115 → 123 | 9,476 → 8,442 |
| `headroom/pytest` | 2,271 → 1,779 | 2,271 → 1,779 | 0 → 0 |
| `headroom/issues` | 11,484 → 10,450 | 6,563 → 5,536 | 4,921 → 4,914 |
| `headroom/smartcrusher_no_query` | 未报告 → 未报告 | 未报告 → 未报告 | 未报告 → 未报告 |
| `headroom/smartcrusher_query` | 未报告 → 未报告 | 未报告 → 未报告 | 未报告 → 未报告 |
| `caveman/pytest_auto` | 2,230 → 1,738 | 2,230 → 1,738 | 0 → 0 |
| `caveman/pytest_terminal` | 2,230 → 1,738 | 1,961 → 1,634 | 269 → 104 |
| `caveman/issues_no_query` | 11,442 → 10,408 | 2,309 → 10,408 | 9,133 → 0 |
| `caveman/issues_query` | 11,442 → 10,408 | 2,309 → 10,408 | 9,133 → 0 |
| `caveman/app_no_query` | 10,790 → 10,790 | 239 → 239 | 10,551 → 10,551 |
| `caveman/app_query` | 10,790 → 10,790 | 1,585 → 1,585 | 9,205 → 9,205 |
| `caveman/app_synonyms_query` | 10,913 → 10,913 | 1,622 → 1,622 | 9,291 → 9,291 |

## Issue 保留、删除与折叠

“保留标题”使用原始完整标题的精确匹配；Caveman 的对象数和标记组数另外解析 JSON。SmartCrusher 的 skip 表示未选删记录，仍可能移除 JSON 空白。

| 输出 | 保留标题 / 60 | 未保留标题 / 60 | #42 标题保留 |
| --- | --- | --- | --- |
| `rtk/issues` | 1 → 1 | 59 → 59 | 否 → 否 |
| `headroom/issues` | 60 → 60 | 0 → 0 | 是 → 是 |
| `headroom/smartcrusher_no_query` | 15 → 60 | 45 → 0 | 是 → 是 |
| `headroom/smartcrusher_query` | 15 → 60 | 45 → 0 | 是 → 是 |
| `caveman/issues_no_query` | 14 → 60 | 46 → 0 | 是 → 是 |
| `caveman/issues_query` | 14 → 60 | 46 → 0 | 是 → 是 |
| `codemode/issues` | 1 → 1 | 59 → 59 | 是 → 是 |

| Caveman JSON 场景 | 保留对象 | 折叠对象 | 折叠标记组 |
| --- | --- | --- | --- |
| `caveman/issues_no_query` | 14 → 60 | 46 → 0 | 5 → 0 |
| `caveman/issues_query` | 14 → 60 | 46 → 0 | 5 → 0 |

| SmartCrusher 场景 | 旧策略 | 新策略 |
| --- | --- | --- |
| `headroom/smartcrusher_no_query` | `smart_sample(60->15)` | `skip:unique_entities_no_signal(60->60)` |
| `headroom/smartcrusher_query` | `smart_sample(60->15)` | `skip:unique_entities_no_signal(60->60)` |

## Pytest 判型与终端折叠

| 场景 | 判型 | 原样输出 | PASSED 输入 | PASSED 保留 | PASSED 折叠 | 全部折叠行 | 标记数 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `caveman/pytest_auto` | text → text | 是 → 是 | 86 → 66 | 86 → 66 | 0 → 0 | 0 → 0 | 0 → 0 |
| `caveman/pytest_terminal` | terminal → terminal | 否 → 否 | 86 → 66 | 70 → 59 | 16 → 7 | 20 → 11 | 12 → 7 |

每个折叠标记的源行数：`[1, 5, 2, 2, 1, 2, 1, 1, 2, 1, 1, 1]` → `[1, 3, 2, 2, 1, 1, 1]`。全部折叠行包括空白行，不全是 PASSED。

| 保护检查 | 旧 → 新 |
| --- | --- |
| Headroom error_output 保护记录 | 否 → 是 |
| Headroom pytest 字节原样保留 | 是 → 是 |
| pytest warning 行数 | 0 → 0 |

warning 行数为零表示该样本没有验证 warning 的保留行为。Headroom 路由阈值与判型根因见 [README](../README.md)，本表不把“输出相同”误当作“经过相同保护分支”。

## 日志证据与折叠

保留数要求完整原始记录逐字存在；`FREESHIP×3` 等不变量不算作三条原始记录。

| 输出 | FREESHIP 保留 / 3 | pricing 保留 / 3 | 折叠源行数 | 折叠标记数 |
| --- | --- | --- | --- | --- |
| `caveman/app_no_query` | 0 → 0 | 不适用 | 296 → 296 | 1 → 1 |
| `caveman/app_query` | 3 → 3 | 不适用 | 279 → 279 | 16 → 16 |
| `caveman/app_synonyms_query` | 3 → 3 | 1 → 1 | 281 → 281 | 16 → 16 |

| 源记录或标记 | 旧 → 新 |
| --- | --- |
| app.log 的 FREESHIP 异常记录 | 3 → 3 |
| app.log 的 total=-2.00 记录 | 3 → 3 |
| synonyms 的 pricing 因果记录 | 3 → 3 |
| 无查询输出的 FREESHIP×3 标记 | 1 → 1 |

## CodeGraph 索引、输出与 Read 基线

| 索引指标 | 旧 → 新 |
| --- | --- |
| 文件 | 10 → 10 |
| 节点 | 134 → 126 |
| 边 | 345 → 333 |

| 命令 | 字节 | 字符 | 行 | 返回符号 | 返回文件 |
| --- | --- | --- | --- | --- | --- |
| [cart_total](../results/codegraph/cart_total.txt) | 972 → 972 | 966 → 966 | 17 → 17 | CLI 未报告 | CLI 未报告 |
| [apply_coupon](../results/codegraph/apply_coupon.txt) | 970 → 970 | 964 → 964 | 21 → 21 | CLI 未报告 | CLI 未报告 |
| [explore](../results/codegraph/explore.txt) | 10,402 → 10,402 | 10,386 → 10,386 | 306 → 306 | 25 → 26 | 4 → 4 |

| Read 文件 | 行 | 原始字节 | 带行号字节 | 带行号字符 |
| --- | --- | --- | --- | --- |
| `shop/cart.py` | 111 → 111 | 3,817 → 3,817 | 4,594 → 4,594 | 4,594 → 4,594 |
| `shop/coupons.py` | 67 → 67 | 2,066 → 2,066 | 2,535 → 2,535 | 2,535 → 2,535 |
| 合计 | 178 → 178 | 5,883 → 5,883 | 7,129 → 7,129 | 7,129 → 7,129 |

| 派生比较 | 旧 → 新 |
| --- | --- |
| 两次 node 调用合计字节 | 1,942 → 1,942 |
| 两次 node / 带行号 Read 基线 | 27.24% → 27.24% |

| 源码定位 | 旧 → 新 |
| --- | --- |
| cart_total | `shop/cart.py:21` → `shop/cart.py:21` |
| apply_coupon | `shop/coupons.py:43` → `shop/coupons.py:43` |
| FREESHIP shipping 分支减法 | `shop/coupons.py:52` → `shop/coupons.py:52` |
| 唯一失败断言 | `tests/test_cart.py:52` → `tests/test_cart.py:52` |

Headroom error 保护与 SmartCrusher skip 已出现；Caveman 的自动类型、终端标记数及 JSON 标记行为均按实际输出记录。完整逐项判断见 [summary.md](../results/summary.md)。测试时长、RTK recall hash 和 CCR handle 是运行身份或耗时，另见机器独立性审计，不作为压缩质量指标。
