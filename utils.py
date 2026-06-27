# ============================================================
# utils.py — 数据处理与绘图函数
# 此模块被 app.py 和 notebooks 共用
# ============================================================
import pandas as pd
import numpy as np
from pathlib import Path
import json

# ---------- 数据目录 ----------
DATA_DIR = Path(__file__).resolve().parent / "data"

# ============================================================
# 第一部分：数据加载与清洗
# ============================================================

def load_and_clean_main(data_dir: Path = None) -> pd.DataFrame:
    """
    读取并清洗全市年度主表 (wenzhou_population.csv)

    清洗步骤：
    1. 读 CSV，自动解析年份为整数
    2. 检查缺失值并报告
    3. 确保所有数值列为正确类型
    4. 派生额外分析列（净流入人口、总抚养比、老龄化速度）

    返回：清洗后的 DataFrame
    """
    if data_dir is None:
        data_dir = DATA_DIR

    filepath = data_dir / "wenzhou_population.csv"

    if not filepath.exists():
        raise FileNotFoundError(
            f"数据文件不存在: {filepath}\n"
            f"请先运行 generate_sample_data.py 生成样本数据，"
            f"或将真实数据放入 {data_dir} 目录。"
        )

    df = pd.read_csv(filepath, encoding="utf-8-sig")

    # --- 缺失值检查 ---
    missing = df.isnull().sum()
    missing = missing[missing > 0]
    if len(missing) > 0:
        print("[WARN]   发现缺失值，将用前向填充处理：")
        print(missing)
        df = df.ffill().bfill()
    else:
        print("[OK]  主表无缺失值")

    # --- 类型转换 ---
    df["year"] = df["year"].astype(int)
    float_cols = [c for c in df.columns if c != "year"]
    for col in float_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # --- 派生列 ---
    df["net_inflow_rough"] = df["total_resident"] - df["total_registered"]
    df["dependency_ratio"] = (
        (df["child_ratio"] + df["elderly_ratio"]) / df["working_age_ratio"] * 100
    )
    df["elderly_delta"] = df["elderly_ratio"].diff()

    return df


def load_and_clean_district(data_dir: Path = None) -> pd.DataFrame:
    """
    读取并清洗分区县年度副表 (wenzhou_district_population.csv)

    清洗步骤同上，额外：
    - 确保 district 列为字符串类型
    - 标记核心城区 vs 郊县

    返回：清洗后的 DataFrame
    """
    if data_dir is None:
        data_dir = DATA_DIR

    filepath = data_dir / "wenzhou_district_population.csv"

    if not filepath.exists():
        raise FileNotFoundError(f"数据文件不存在: {filepath}")

    df = pd.read_csv(filepath, encoding="utf-8-sig")

    missing = df.isnull().sum()
    missing = missing[missing > 0]
    if len(missing) > 0:
        print("[WARN]   区县数据发现缺失值，将分组填充处理")
        df = df.groupby("district", group_keys=False).apply(
            lambda g: g.ffill().bfill()
        ).reset_index(drop=True)
    else:
        print("[OK]  区县数据无缺失值")

    df["year"] = df["year"].astype(int)
    df["district"] = df["district"].astype(str)
    float_cols = [c for c in df.columns if c not in ("year", "district")]
    for col in float_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    urban_core = ["鹿城区", "龙湾区", "瓯海区", "龙港市"]
    df["area_type"] = df["district"].apply(
        lambda d: "核心城区" if d in urban_core else "郊县"
    )

    return df


# ============================================================
# 第二部分：GeoJSON 数据（温州 12 个区县 — 简化轮廓）
# 数据来源：DataV.GeoAtlas + 手工整理
# 正式使用时请替换为高精度 GeoJSON 文件
# ============================================================

def load_wenzhou_geojson() -> dict:
    """
    加载温州区县 GeoJSON 数据。
    优先从 data/ 目录读取外部文件；如不存在则使用内置简化版。

    获取完整 GeoJSON 的途径：
    1. https://datav.aliyun.com/portal/school/atlas/area_selector
       → 选择「浙江省 → 温州市」→ 下载 GeoJSON
    2. GitHub: https://github.com/xinwen-ma/geojson-china
       下载 city 层级 GeoJSON 后筛选温州各区县
    3. 将下载的 .json 文件放入 data/wenzhou_districts.geojson
    """
    geojson_path = DATA_DIR / "wenzhou_districts.geojson"

    if geojson_path.exists():
        with open(geojson_path, "r", encoding="utf-8") as f:
            return json.load(f)

    # ---------- 内置简化 GeoJSON ----------
    # 注意：以下为简化示意坐标（非精确地理边界），仅用于功能测试
    # 正式项目请替换为真实 GeoJSON 文件
    districts_geojson = {
        "type": "FeatureCollection",
        "features": [
            # 每个区县一个 Feature，coordinates 为简化的多边形
            # 实际坐标来自公开 GeoJSON 数据集的手工简化
            {
                "type": "Feature",
                "properties": {"name": "鹿城区", "center": [120.65, 28.02]},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [120.55, 27.95], [120.75, 27.95], [120.75, 28.10],
                        [120.55, 28.10], [120.55, 27.95]
                    ]]
                }
            },
            {
                "type": "Feature",
                "properties": {"name": "龙湾区", "center": [120.81, 27.93]},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [120.73, 27.88], [120.90, 27.88], [120.90, 27.98],
                        [120.73, 27.98], [120.73, 27.88]
                    ]]
                }
            },
            {
                "type": "Feature",
                "properties": {"name": "瓯海区", "center": [120.62, 27.97]},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [120.53, 27.90], [120.70, 27.90], [120.70, 28.02],
                        [120.53, 28.02], [120.53, 27.90]
                    ]]
                }
            },
            {
                "type": "Feature",
                "properties": {"name": "洞头区", "center": [121.15, 27.84]},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [121.05, 27.78], [121.25, 27.78], [121.25, 27.90],
                        [121.05, 27.90], [121.05, 27.78]
                    ]]
                }
            },
            {
                "type": "Feature",
                "properties": {"name": "永嘉县", "center": [120.68, 28.15]},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [120.60, 28.05], [120.82, 28.05], [120.82, 28.28],
                        [120.60, 28.28], [120.60, 28.05]
                    ]]
                }
            },
            {
                "type": "Feature",
                "properties": {"name": "平阳县", "center": [120.56, 27.66]},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [120.40, 27.58], [120.70, 27.58], [120.70, 27.75],
                        [120.40, 27.75], [120.40, 27.58]
                    ]]
                }
            },
            {
                "type": "Feature",
                "properties": {"name": "苍南县", "center": [120.40, 27.52]},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [120.30, 27.42], [120.55, 27.42], [120.55, 27.60],
                        [120.30, 27.60], [120.30, 27.42]
                    ]]
                }
            },
            {
                "type": "Feature",
                "properties": {"name": "文成县", "center": [120.09, 27.79]},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [119.92, 27.70], [120.25, 27.70], [120.25, 27.90],
                        [119.92, 27.90], [119.92, 27.70]
                    ]]
                }
            },
            {
                "type": "Feature",
                "properties": {"name": "泰顺县", "center": [119.72, 27.56]},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [119.60, 27.44], [119.85, 27.44], [119.85, 27.68],
                        [119.60, 27.68], [119.60, 27.44]
                    ]]
                }
            },
            {
                "type": "Feature",
                "properties": {"name": "瑞安市", "center": [120.65, 27.78]},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [120.52, 27.70], [120.78, 27.70], [120.78, 27.88],
                        [120.52, 27.88], [120.52, 27.70]
                    ]]
                }
            },
            {
                "type": "Feature",
                "properties": {"name": "乐清市", "center": [120.98, 28.12]},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [120.85, 28.00], [121.15, 28.00], [121.15, 28.28],
                        [120.85, 28.28], [120.85, 28.00]
                    ]]
                }
            },
            {
                "type": "Feature",
                "properties": {"name": "龙港市", "center": [120.53, 27.57]},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [120.48, 27.52], [120.58, 27.52], [120.58, 27.62],
                        [120.48, 27.62], [120.48, 27.52]
                    ]]
                }
            },
        ]
    }
    return districts_geojson


# ============================================================
# 第三部分：Plotly 交互图表函数（每张图一个函数）
# 注意：全部返回 plotly.graph_objects.Figure 或 plotly.express 对象
# ============================================================
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# -------- 图 1：常住人口 vs 户籍人口趋势线 --------
def plot_population_trend(df: pd.DataFrame, year_range: tuple = None) -> go.Figure:
    """
    折线图：常住人口 vs 户籍人口 + 净流入填充

    参数：
        df: 全市主表 DataFrame
        year_range: (min_year, max_year) 过滤范围
    返回：
        plotly.graph_objects.Figure
    """
    if year_range:
        df = df[(df["year"] >= year_range[0]) & (df["year"] <= year_range[1])]

    fig = go.Figure()

    # 常住人口实线
    fig.add_trace(go.Scatter(
        x=df["year"], y=df["total_resident"],
        mode="lines+markers",
        name="常住人口（万人）",
        line=dict(color="#2878B5", width=3),
        marker=dict(size=8, color="#2878B5"),
        hovertemplate="<b>%{x} 年</b><br>常住人口: %{y:.1f} 万人<extra></extra>",
    ))

    # 户籍人口虚线
    fig.add_trace(go.Scatter(
        x=df["year"], y=df["total_registered"],
        mode="lines+markers",
        name="户籍人口（万人）",
        line=dict(color="#F4A261", width=2, dash="dash"),
        marker=dict(size=6, color="#F4A261"),
        hovertemplate="<b>%{x} 年</b><br>户籍人口: %{y:.1f} 万人<extra></extra>",
    ))

    # 净流入填充区域
    fig.add_trace(go.Scatter(
        x=df["year"].tolist() + df["year"].tolist()[::-1],
        y=df["total_resident"].tolist() + df["total_registered"].tolist()[::-1],
        fill="toself",
        fillcolor="rgba(40,120,181,0.12)",
        line=dict(width=0),
        name="净流入人口（差值）",
        hoverinfo="skip",
        showlegend=True,
    ))

    fig.update_layout(
        title=dict(
            text="<b>温州常住人口 vs 户籍人口变化趋势</b>",
            font=dict(size=16),
            x=0.5,
        ),
        xaxis=dict(title="年份", dtick=1, gridcolor="rgba(0,0,0,0.08)"),
        yaxis=dict(title="人口（万人）", gridcolor="rgba(0,0,0,0.08)"),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        plot_bgcolor="#F8F9FA",
        paper_bgcolor="#F8F9FA",
        margin=dict(l=40, r=40, t=60, b=30),
    )
    return fig


# -------- 图 2：出生率 / 死亡率 / 自然增长率趋势 --------
def plot_vital_rates(df: pd.DataFrame, year_range: tuple = None) -> go.Figure:
    """
    多线图：出生率、死亡率、自然增长率，含零值参考线

    参数：
        df: 全市主表 DataFrame
        year_range: (min_year, max_year) 过滤范围
    返回：
        plotly.graph_objects.Figure
    """
    if year_range:
        df = df[(df["year"] >= year_range[0]) & (df["year"] <= year_range[1])]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["year"], y=df["birth_rate"],
        mode="lines+markers",
        name="出生率 (‰)",
        line=dict(color="#E63946", width=2.5),
        marker=dict(size=7, symbol="circle"),
        hovertemplate="<b>%{x} 年</b><br>出生率: %{y:.2f}‰<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x=df["year"], y=df["death_rate"],
        mode="lines+markers",
        name="死亡率 (‰)",
        line=dict(color="#457B9D", width=2.5),
        marker=dict(size=7, symbol="diamond"),
        hovertemplate="<b>%{x} 年</b><br>死亡率: %{y:.2f}‰<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x=df["year"], y=df["natural_growth_rate"],
        mode="lines+markers",
        name="自然增长率 (‰)",
        line=dict(color="#2A9D8F", width=3),
        marker=dict(size=8, symbol="square"),
        hovertemplate="<b>%{x} 年</b><br>自然增长率: %{y:.2f}‰<extra></extra>",
        fill="tozeroy", fillcolor="rgba(42,157,143,0.08)",
    ))

    # 零值参考线
    fig.add_hline(
        y=0, line_dash="dash", line_color="gray", line_width=1.2,
        annotation_text="零增长线", annotation_position="bottom right",
    )

    fig.update_layout(
        title=dict(
            text="<b>出生率 / 死亡率 / 自然增长率变化趋势</b>",
            font=dict(size=16), x=0.5,
        ),
        xaxis=dict(title="年份", dtick=1, gridcolor="rgba(0,0,0,0.08)"),
        yaxis=dict(title="率 (‰)", gridcolor="rgba(0,0,0,0.08)"),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        plot_bgcolor="#F8F9FA",
        paper_bgcolor="#F8F9FA",
        margin=dict(l=40, r=40, t=60, b=30),
    )
    return fig


# -------- 图 3：人口年龄结构堆叠面积图 --------
def plot_age_structure(df: pd.DataFrame, year_range: tuple = None) -> go.Figure:
    """
    堆叠面积图：0-14 岁 / 15-64 岁 / 65 岁及以上占比

    参数：
        df: 全市主表 DataFrame
        year_range: (min_year, max_year) 过滤范围
    返回：
        plotly.graph_objects.Figure
    """
    if year_range:
        df = df[(df["year"] >= year_range[0]) & (df["year"] <= year_range[1])]

    # 全国老龄化参考（2020 七普数据）
    CHINA_ELDERLY_2020 = 13.5

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["year"], y=df["child_ratio"],
        mode="lines",
        name="0-14 岁少儿占比",
        line=dict(width=1, color="#A8DADC"),
        stackgroup="one",
        hovertemplate="<b>%{x} 年</b><br>少儿占比: %{y:.1f}%<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x=df["year"], y=df["working_age_ratio"],
        mode="lines",
        name="15-64 岁劳动年龄占比",
        line=dict(width=1, color="#457B9D"),
        stackgroup="one",
        hovertemplate="<b>%{x} 年</b><br>劳动年龄占比: %{y:.1f}%<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x=df["year"], y=df["elderly_ratio"],
        mode="lines",
        name="65 岁及以上老年占比",
        line=dict(width=1, color="#E63946"),
        stackgroup="one",
        hovertemplate="<b>%{x} 年</b><br>老年占比: %{y:.1f}%<extra></extra>",
    ))

    # 全国参考线
    fig.add_hline(
        y=CHINA_ELDERLY_2020, line_dash="dash", line_color="#E63946", line_width=1.5,
        annotation_text=f"全国 65+ 占比 (2020≈{CHINA_ELDERLY_2020}%)",
        annotation_position="top left",
    )

    fig.update_layout(
        title=dict(
            text="<b>温州人口年龄结构演变（堆叠 100%）</b>",
            font=dict(size=16), x=0.5,
        ),
        xaxis=dict(title="年份", dtick=1, gridcolor="rgba(0,0,0,0.08)"),
        yaxis=dict(title="占比 (%)", range=[0, 100], gridcolor="rgba(0,0,0,0.08)"),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        plot_bgcolor="#F8F9FA",
        paper_bgcolor="#F8F9FA",
        margin=dict(l=40, r=40, t=60, b=30),
    )
    return fig


# -------- 图 4：区县老龄化 vs 城镇化率散点图（带动画） --------
def plot_elderly_urbanization(
    df_dist: pd.DataFrame,
    selected_districts: list = None,
    selected_year: int = None,
) -> go.Figure:
    """
    散点图：各区县老龄化率 vs 城镇化率

    参数：
        df_dist: 分区县 DataFrame
        selected_districts: 可选区县列表（None=全部）
        selected_year: 指定年份则显示静态散点图；None 则显示带动画的历年图
    返回：
        plotly.graph_objects.Figure
    """
    df = df_dist.copy()
    if selected_districts:
        df = df[df["district"].isin(selected_districts)]

    # 如果指定了年份，过滤到该年份并做静态散点图
    if selected_year is not None:
        df = df[df["year"] == selected_year]
        fig = px.scatter(
            df,
            x="urbanization_rate",
            y="elderly_ratio",
            size="total_resident",
            color="district",
            hover_name="district",
            size_max=40,
            labels={
                "urbanization_rate": "城镇化率 (%)",
                "elderly_ratio": "65 岁及以上人口占比 (%)",
                "district": "区县",
            },
            title=f"<b>各区县老龄化率 vs 城镇化率（{selected_year} 年）</b>",
        )
        fig.update_traces(marker=dict(opacity=0.8, line=dict(width=1, color="white")))
        fig.update_layout(
            xaxis=dict(gridcolor="rgba(0,0,0,0.08)", zeroline=True),
            yaxis=dict(gridcolor="rgba(0,0,0,0.08)", zeroline=True),
            plot_bgcolor="#F8F9FA",
            paper_bgcolor="#F8F9FA",
            margin=dict(l=40, r=40, t=60, b=30),
        )
        return fig

    # 否则显示带动画的历年图
    fig = px.scatter(
        df,
        x="urbanization_rate",
        y="elderly_ratio",
        size="total_resident",
        color="district",
        animation_frame="year",
        hover_name="district",
        size_max=40,
        labels={
            "urbanization_rate": "城镇化率 (%)",
            "elderly_ratio": "65 岁及以上人口占比 (%)",
            "district": "区县",
            "year": "年份",
        },
        title="<b>各区县老龄化率 vs 城镇化率（动画播放）</b>",
    )

    fig.update_traces(marker=dict(opacity=0.8, line=dict(width=1, color="white")))

    fig.update_layout(
        xaxis=dict(gridcolor="rgba(0,0,0,0.08)", zeroline=True),
        yaxis=dict(gridcolor="rgba(0,0,0,0.08)", zeroline=True),
        plot_bgcolor="#F8F9FA",
        paper_bgcolor="#F8F9FA",
        margin=dict(l=40, r=40, t=60, b=30),
        updatemenus=[dict(
            type="buttons",
            showactive=False,
            buttons=[
                dict(label="▶ 播放", method="animate",
                     args=[None, dict(frame=dict(duration=800, redraw=True))]),
                dict(label="⏸ 暂停", method="animate",
                     args=[[None], dict(frame=dict(duration=0, redraw=True))]),
            ],
            x=1.05, y=1.15,
        )],
    )

    # 移除自动生成的滑块（用按钮控制）
    fig["layout"].pop("sliders", None)
    return fig


# -------- 图 5：分区县人口对比水平柱状图 --------
def plot_district_comparison(
    df_dist: pd.DataFrame,
    year_range: tuple = None,
    metric: str = "total_resident",
    selected_districts: list = None,
) -> go.Figure:
    """
    水平柱状图：分区县指标对比

    参数：
        df_dist: 分区县 DataFrame
        year_range: 年份范围过滤
        metric: 展示指标（total_resident / urbanization_rate / elderly_ratio / population_density）
        selected_districts: 可选区县列表
    返回：
        plotly.graph_objects.Figure
    """
    df = df_dist.copy()
    if year_range:
        df = df[df["year"] >= year_range[0]]

    # 取最新年份数据
    latest_year = df["year"].max()
    df_latest = df[df["year"] == latest_year]
    if selected_districts:
        df_latest = df_latest[df_latest["district"].isin(selected_districts)]

    # 计算变化量：2010 → 最新年
    df_2010 = df[df["year"] == 2010].set_index("district")
    df_compare = df_latest.set_index("district")
    df_compare["change"] = df_compare[metric] - df_2010[metric].reindex(df_compare.index)

    # 排序
    df_compare = df_compare.sort_values(metric, ascending=True)

    # 指标中文映射
    metric_labels = {
        "total_resident": "常住人口（万人）",
        "urbanization_rate": "城镇化率（%）",
        "elderly_ratio": "65 岁及以上占比（%）",
        "population_density": "人口密度（人/km²）",
        "natural_growth_rate": "自然增长率（‰）",
    }
    metric_label = metric_labels.get(metric, metric)

    # 颜色：正变化蓝，负变化红
    colors = ["#E63946" if v < 0 else "#2878B5" for v in df_compare["change"]]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=df_compare.index,
        x=df_compare[metric],
        orientation="h",
        marker=dict(color=colors, opacity=0.85, line=dict(width=0)),
        text=[f"{v:.1f}" for v in df_compare[metric]],
        textposition="outside",
        textfont=dict(size=11),
        hovertemplate=(
            "<b>%{y}</b><br>" + metric_label + ": %{x:.1f}<br>"
            "较 2010 变化: %{customdata:+.1f}<extra></extra>"
        ),
        customdata=df_compare["change"],
    ))

    fig.update_layout(
        title=dict(
            text=f"<b>温州各区县 {metric_label} 对比（{latest_year} 年）</b>",
            font=dict(size=16), x=0.5,
        ),
        xaxis=dict(title=metric_label, gridcolor="rgba(0,0,0,0.08)"),
        yaxis=dict(title="", autorange="reversed"),
        plot_bgcolor="#F8F9FA",
        paper_bgcolor="#F8F9FA",
        margin=dict(l=20, r=60, t=60, b=30),
    )
    return fig


# -------- 图 6：城镇化率 vs 人均 GDP 双轴图 --------
def plot_urbanization_gdp(df: pd.DataFrame, year_range: tuple = None) -> go.Figure:
    """
    双 Y 轴折线图：城镇化率（左轴）+ 人均 GDP（右轴）

    参数：
        df: 全市主表 DataFrame
        year_range: (min_year, max_year) 过滤范围
    返回：
        plotly.graph_objects.Figure
    """
    if year_range:
        df = df[(df["year"] >= year_range[0]) & (df["year"] <= year_range[1])]

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Scatter(
            x=df["year"], y=df["urbanization_rate"],
            mode="lines+markers",
            name="城镇化率 (%)",
            line=dict(color="#2878B5", width=3),
            marker=dict(size=8, color="#2878B5"),
            hovertemplate="<b>%{x} 年</b><br>城镇化率: %{y:.1f}%<extra></extra>",
        ),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(
            x=df["year"], y=df["gdpp"] / 10000,
            mode="lines+markers",
            name="人均 GDP（万元）",
            line=dict(color="#E76F51", width=2.5, dash="dashdot"),
            marker=dict(size=7, symbol="diamond", color="#E76F51"),
            hovertemplate="<b>%{x} 年</b><br>人均 GDP: %{y:.2f} 万元<extra></extra>",
        ),
        secondary_y=True,
    )

    # 双轴颜色标记
    fig.update_yaxes(title_text="<span style='color:#2878B5'>城镇化率 (%)</span>",
                     secondary_y=False, gridcolor="rgba(0,0,0,0.08)")
    fig.update_yaxes(title_text="<span style='color:#E76F51'>人均 GDP（万元）</span>",
                     secondary_y=True, gridcolor="rgba(0,0,0,0.04)")

    fig.update_layout(
        title=dict(
            text="<b>温州城镇化率与人均 GDP 协同增长</b>",
            font=dict(size=16), x=0.5,
        ),
        xaxis=dict(title="年份", dtick=1, gridcolor="rgba(0,0,0,0.08)"),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        plot_bgcolor="#F8F9FA",
        paper_bgcolor="#F8F9FA",
        margin=dict(l=40, r=40, t=60, b=30),
    )
    return fig


# -------- 图 7：分区县人口密度地图 --------
def plot_population_map(
    df_dist: pd.DataFrame,
    selected_year: int = None,
    map_metric: str = "population_density",
) -> go.Figure:
    """
    Choropleth 地图：温州各区县人口指标地理分布
    使用 Mapbox 底图渲染自定义 GeoJSON，无需 Token

    参数：
        df_dist: 分区县 DataFrame
        selected_year: 展示年份（默认最新）
        map_metric: 着色指标（population_density / total_resident / elderly_ratio）
    返回：
        plotly.graph_objects.Figure
    """
    geojson = load_wenzhou_geojson()
    if geojson is None:
        return None

    if selected_year is None:
        selected_year = int(df_dist["year"].max())

    df_year = df_dist[df_dist["year"] == selected_year].copy()

    # 指标中文映射
    metric_labels = {
        "population_density": "人口密度（人/km²）",
        "total_resident": "常住人口（万人）",
        "elderly_ratio": "65 岁及以上占比 (%)",
        "urbanization_rate": "城镇化率 (%)",
        "natural_growth_rate": "自然增长率 (‰)",
    }
    metric_label = metric_labels.get(map_metric, map_metric)

    # 使用 choropleth_mapbox —— 对自定义 GeoJSON 渲染更可靠
    fig = px.choropleth_mapbox(
        df_year,
        geojson=geojson,
        locations="district",
        featureidkey="properties.name",
        color=map_metric,
        color_continuous_scale=["#F7FBFF", "#2878B5", "#08306B"],
        labels={map_metric: metric_label},
        hover_name="district",
        hover_data={
            "total_resident": ":.1f",
            "urbanization_rate": ":.1f",
            "elderly_ratio": ":.1f",
            map_metric: ":.1f",
        },
        title=f"<b>温州各区县 {metric_label} 地理分布（{selected_year} 年）</b>",
        mapbox_style="carto-positron",
        center={"lat": 27.9, "lon": 120.65},
        zoom=7.8,
        opacity=0.75,
    )

    fig.update_layout(
        margin=dict(l=10, r=10, t=60, b=10),
        paper_bgcolor="#F8F9FA",
        coloraxis_colorbar=dict(
            title=metric_label,
            len=0.6,
            thickness=15,
        ),
    )
    return fig


# ============================================================
# 如果直接运行此文件，做一次快速验证
# ============================================================
if __name__ == "__main__":
    df_main = load_and_clean_main()
    df_dist = load_and_clean_district()

    print("\n===== 全市主表信息 =====")
    print(df_main.info())
    print(f"年份范围: {df_main['year'].min()} – {df_main['year'].max()}")

    print("\n===== 分区县副表信息 =====")
    print(f"区县数量: {df_dist['district'].nunique()}")
    print(f"年份范围: {df_dist['year'].min()} – {df_dist['year'].max()}")

    print("\n===== 所有绘图函数已就绪 =====")
    print("[1] plot_population_trend(df_main)")
    print("[2] plot_vital_rates(df_main)")
    print("[3] plot_age_structure(df_main)")
    print("[4] plot_elderly_urbanization(df_dist)")
    print("[5] plot_district_comparison(df_dist)")
    print("[6] plot_urbanization_gdp(df_main)")
    print("[7] plot_population_map(df_dist)")
