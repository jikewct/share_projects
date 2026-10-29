# Gamma Lab

使用 **Streamlit + pandas + Plotly** 的 Gamma 实验分析工作台。选择实验、字段或条件后，页面重新计算并渲染交互图表，不需要先保存 PNG。支持悬停、缩放、图例开关、PNG 导出和 CSV 下载。

## result 实验目录

应用默认动态扫描项目下的 `result/`。一级子目录名就是实验名，每个实验目录放置该实验的分析 DataFrame 文件：

```text
result/
├── EXP-001_基准/
│   ├── global.csv
│   ├── global.df
│   ├── band.csv
│   └── screen.csv
└── EXP-002_优化A/
    ├── global.csv
    ├── global.df
    ├── band.csv
    └── screen.csv
```

“实验总览”读取 `global.csv`，“全局曲线”读取同目录的 `global.df`。`global.df` 需由 pandas `DataFrame.to_pickle()` 保存，页面通过 `pandas.read_pickle()` 加载。目录或文件更新后，点击“刷新实验 / 数据”即可重新读取。

全局统计页由吸顶实验总览和全局曲线组成：

- 实验总览：每个实验一行，合并屏幕数、总点数、OK 点数、OKR 均值、相对首个实验的变化率和完整绑点；随页面滚动吸顶，窄窗口支持横向滚动。
- OKR 曲线：固定灰阶横轴，可显示每个实验的均值虚线。
- Gamma 曲线：固定灰阶横轴，可切换自动或手动纵轴范围。两张图都使用最后一个选中实验的绑点作为刻度和垂直参考线。

侧栏按实验选择、条件筛选、数据配置排列，数据配置默认折叠。曲线图例位于图表上方；显示均值时，每个实验只保留一个带均值的图例条目。Gamma 仅在关闭“纵轴自动范围”后显示上下限输入框。总览表横向滚动时固定实验名列，纵向滚动时固定表头。

左侧“实验选择”是带复选框的目录树；右侧顶部横向排列全局统计、Band 维度、屏幕维度、实验对比、自定义分析和数据明细菜单。根节点“全部实验”可以统一勾选或取消，每个实验可以单独选择；所有页面使用同一实验选择范围。

绑点优先读取 `global.csv` 中的 `band_points`。旧格式 `bind_points.csv`（`position`、`point_value`）作为兼容回退；未提供时显示“未提供”占位值。绑点采用无空格逗号连接，完整单行展示。

全局统计 CSV 可提供 `band_points`、`screen_num`、`toal_num`（也兼容 `total_num`）、`ok_num`、`okr_mean`。实验总览直接读取这些字段，不随曲线条件筛选重新聚合；仅“相对首个实验”根据当前选择动态计算。正增长显示红色，下降显示绿色，第一个实验标记为基准。

示例目录中的 `SIMULATED_DATA.txt` 用于标明模拟数据。需要重新生成示例时运行：

```bash
.venv/bin/python generate_results.py --overwrite
```

## 启动

推荐 Python 3.10 或以上；本项目也可使用 Python 3.9。

```bash
cd /Users/changtaowang/Home/AI/gamma_vis
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

在浏览器打开终端显示的地址，通常为 `http://localhost:8501`。首次启动使用固定随机种子的**模拟数据**，包含三个实验、六块屏幕、RGB Band、两种刷新率与两档 DBV，不代表实际实验结果。

## 模块结构与页面接口

```text
app.py                         # 数据配置、字段映射、实验选择、筛选和路由
dashboard/
├── global_statistics.py       # 全局统计整页入口 render_page(df, ...)
├── data.py                    # global.csv / global.df 文件读取
├── overview.py                # 总览表、CSV 汇总字段、绑点解析和相对变化率
├── overview.css               # 总览表与吸顶浮层样式
├── ui.py                      # 公共标题、图表展示、指标卡片与下载
├── base.css                   # 全局布局与横向导航样式
├── dimensions.py             # Band / 屏幕维度页面
├── comparison.py             # 实验配对对比页面
├── explorer.py               # 自定义分析页面
└── details.py                # 数据明细页面
curves.py                      # 纯 Plotly 曲线构造与聚合，不依赖 Streamlit
analytics.py                   # DataFrame 清洗、字段映射与统计
```

`dashboard.global_statistics.render_page` 接收 DataFrame，统一处理页面标题、总览浮层、OKR/Gamma 曲线、均值开关、绑点刻度和纵轴控制。页面模块不导入 `app.py`，不从侧栏或 `session_state` 获取数据路径，不修改传入的 DataFrame。

可以用一个独立 Streamlit 脚本展示全局统计页：

```python
import pandas as pd
import streamlit as st
from dashboard.global_statistics import render_page
from dashboard.ui import apply_styles

st.set_page_config(page_title="全局统计", layout="wide")
apply_styles()
curve_df = pd.read_pickle("result/实验A/global.df")
summary_df = pd.read_csv("result/实验A/global.csv")
render_page(curve_df, summary_df=summary_df)
```

接口参数：

- `df`：曲线数据，列名为 `gray`、`OKR`、`RealGamma` 等标准字段；可先自行筛选。
- `summary_df`：未筛选的实验汇总数据，包含 `band_points`、`screen_num`、`toal_num`、`ok_num`、`okr_mean`。不提供时直接读取 `df` 中的汇总字段。
- `selected_experiments`：有序实验名列表；第一项为变化率基准，最后一项提供绑点；不提供时使用 DataFrame 中的所有实验。
- `result_root`：可选，仅用于旧格式 `bind_points.csv` 的显式路径回退。
- `source_label`：可选，标题旁显示的数据来源标签。

多个实验需在两份 DataFrame 中提供相同的 `experiment` 标识；单个实验可省略该列，自动使用“实验 01”。即使筛选后曲线数据为空，只要 `summary_df` 中仍有已选实验，总览表依然显示。

主入口调用示例：

```python
render_page(
    filtered_df,
    selected_experiments=selected,
    summary_df=unfiltered_df,
    source_label="result 实验目录",
)
```

`dashboard.data.load_global_experiment("result/实验A/global.csv")` 可显式读取同目录两种文件，将 CSV 汇总字段附加到曲线 DataFrame 后返回。目录扫描与实验命名由主入口统一管理。

## 接入已有 pandas DataFrame

新增自己的入口，例如 `my_dashboard.py`：

```python
import pandas as pd
import streamlit as st
from app import render_dashboard

@st.cache_data
def load_experiments():
    # 替换为你已有的数据加载、清洗代码
    df_a = pd.read_parquet("data/experiment_a.parquet")
    df_b = pd.read_parquet("data/experiment_b.parquet")
    return {"实验 A": df_a, "实验 B": df_b}

render_dashboard(load_experiments())
```

运行 `streamlit run my_dashboard.py`。字典的键作为实验名称；传入的 DataFrame 不会被修改。Streamlit 的脚本在选择条件后重新执行，所以建议缓存数据加载，数据更新时清理缓存或给加载函数加入版本参数。Notebook 中的内存变量无法被另一进程直接读取，可把加载逻辑移到上述入口，或先导出 Parquet。

也可以：

- 在侧栏选择「上传文件」，上传一个或多个 CSV、Parquet、XLSX 文件。XLSX 读取第一个工作表。
- 将文件放入项目 `data/` 目录，选择「本地 data 目录」，更新文件后点击「刷新数据」。文件按内容缓存，内容变化后会重新解析。
- 文件有实验列时按列区分实验；没有时以文件名作为实验名。多个文件名相同或实验标签相同将合并，需保持实验名称唯一。

上传数据仅由当前 Streamlit 服务进程处理，本应用不主动向第三方发送数据。上传限制为单文件 200 MB；聚合仍基于内存中的 pandas，实际容量取决于机器内存。

## 页面

| 菜单 | 功能 |
| --- | --- |
| 全局统计 | 多实验指标均值、箱线分布、按灰阶/DBV/刷新率的趋势、完整统计表 |
| Band 维度 | 每个 Band 内的实验对比、分组统计 |
| 屏幕维度 | 每块屏幕的实验对比、屏幕 × Band 热力图 |
| 实验对比 | 选择基准与对比实验、按条件配对、散点、差值分布及完整配对导出 |
| 自定义分析 | 选择任意数值指标、横轴、分组与聚合方式，支持五类图表 |
| 数据明细 | 筛选后记录、字段类型和缺失率、完整 CSV 导出 |

左侧的实验、Band、屏幕、刷新率、DBV、灰阶筛选作用于所有页面。实验选择为空时不显示数据；其他多选筛选为空表示全部。页面顶部的指标选择控制当前分析；自定义分析还提供自己的纵轴字段选择。

## 字段与计算口径

侧栏「字段映射与计算口径」可调整自动识别结果。截图列名以实际上传文件为准，不根据截图中被截断的表头推测规格列。

| 标准字段 | 自动识别示例 | 用途 |
| --- | --- | --- |
| `experiment` | `experiment_id`, `exp_id`, `实验名称` | 实验标识 |
| `band` | `band_id`, `BandName` | Band 标识 |
| `screen` | `screen_id`, `panel_id`, `sn` | 屏幕标识 |
| `gray`, `freq`, `dbv` | `grey`, `frequency`, `brightness` | 灰阶、刷新率、亮度档位 |
| `RealGamma` | `GammaCurv`, `GammaCurve`, `real_gamma` | Gamma 测量值 |
| `Mesure_L/x/y` | `Measure_L/x/y` | 兼容截图中 Mesure 的拼写 |
| `OKR` | `ok_rate`, `pass_rate` | 已有合格率 |
| `LSpecIn`, `XSpecIn`, `YSpecIn`, `GammaIn` | 同名字段 | 0/1 判定 |
| `SpecGammaMin/Max` | 同名或 `SpecGammaLower/Upper` | Gamma 趋势规格参考线 |

没有 Band 或屏幕标识时，对应页面提示补充字段，不会把 `freq` 当作 Band 或虚构屏幕编号。单文件没有实验列时仍可查看单实验统计，比较两个实验需提供两个文件或实验列。自定义非数值列如果混合了数字与文本，数值分析会将不能解析的值视为缺失；建议在上游清洗为一致类型。

### RealGamma

这是原始 Gamma 测量列的映射，**不是从亮度自动反算的 Gamma**。负值视为无效；默认排除 `0`（截图中黑阶存在此值），可取消勾选「RealGamma=0 视为无效值」。`NaN` 与正负无穷不参与统计。

### OKR

有两种明确口径：

1. 使用已有 `OKR` 列：在映射面板指定数值范围 `0–1` 或 `0–100`，统一成 0–1 分析，按百分比展示；越界值、缺失值无效。
2. 根据判定列计算：所有**已映射且存在**的判定列都为 1，该测量行才合格；任意一个为 0 则不合格。任一参与列为 -1、缺失或非 0/1 时，该行不参与 OKR。不存在任何判定列时无法计算，不用 Gamma 或其他指标猜测。页面显示具体参与列，按需要取消映射。

OKR = 有效测量行中合格行的比例，**不是整块屏幕良率**。顶部覆盖率 = 当前指标的有效行数 / 筛选后的总行数。均值、箱线图和趋势均基于当前指标的有效值，不填充缺失值。规格参考线在混合条件下按横轴取规格均值，仅供参考；不会据此重新判定 OKR。要查看单一条件的规格，请固定其他筛选项。

### 实验配对

默认使用存在的 `screen + band + freq + dbv + gray` 配对，可手动调整。同一实验内重复组合先取指标均值，再做一对一外连接，避免多对多连接放大样本。只有两边都有效的共同条件组参与差值，每个组等权。页面保留仅基准、仅对比、无效行和合并重复行的数量，并可导出完整结果。

差值 = 对比 − 基准。OKR 使用**百分点**，例如 90% → 95% 为 +5 pp。其他字段同时导出相对变化率；基准为 0 时变化率为空。差值正负本身不代表质量好坏，Gamma 应结合目标与规格判断。两个实验使用不同屏幕编号时，可取消 `screen`，此时对比的是相同其余条件下的组均值。

## 验证

```bash
python -m pip install 'pytest>=8,<9'
python -m pytest -q
```

测试覆盖无效判定值、OKR 百分比范围、映射、重复组合安全配对、无交集条件，以及 Streamlit 各分析页面的运行。图表使用当前筛选数据的聚合；散点图超过 20,000 行时固定随机抽样，页面会提示，统计与下载仍使用完整数据。

本项目需要 Python 服务运行，可部署在支持 Streamlit 的主机、容器或 Streamlit Community Cloud；不能直接作为纯静态 HTML 网站托管。
