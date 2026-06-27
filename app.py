"""
=============================================================================
app.py — 温州人口变迁 · 交互式数据可视化仪表板
=============================================================================
基于 Streamlit 构建，支持年份筛选、指标切换、区县对比、地图探索。
运行方式：streamlit run app.py
=============================================================================
"""
import streamlit as st
import pandas as pd
from pathlib import Path

# 导入自定义模块
from utils import (
    load_and_clean_main,
    load_and_clean_district,
    plot_population_trend,
    plot_vital_rates,
    plot_age_structure,
    plot_elderly_urbanization,
    plot_district_comparison,
    plot_urbanization_gdp,
    plot_population_map,
)

# ============================================================
# 页面配置
# ============================================================
st.set_page_config(
    page_title="温州人口变迁 · 数据可视化",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# 数据加载（带缓存）
# ============================================================
@st.cache_data(ttl=3600)
def load_data():
    """加载并缓存全市和区县数据"""
    df_main = load_and_clean_main()
    df_dist = load_and_clean_district()
    return df_main, df_dist


df_main, df_dist = load_data()

# 年份范围
YEAR_MIN = int(df_main["year"].min())
YEAR_MAX = int(df_main["year"].max())

# ============================================================
# 侧边栏 :: 控件区
# ============================================================
with st.sidebar:
    st.image(
        "https://img.icons8.com/color/96/statistics.png",
        width=64,
    )
    st.title("📊 温州人口变迁")
    st.caption("2010–2023 年交互式数据可视化仪表板")
    st.markdown("---")

    # ---- 年份范围滑块 ----
    st.subheader("🎚️ 年份范围")
    year_range = st.slider(
        "拖动滑块选择起止年份",
        min_value=YEAR_MIN,
        max_value=YEAR_MAX,
        value=(YEAR_MIN, YEAR_MAX),
        step=1,
        help="所有图表将根据所选年份范围动态更新",
    )

    # ---- 区县多选 ----
    st.subheader("🗺️ 区县筛选")
    all_districts = sorted(df_dist["district"].unique())
    selected_districts = st.multiselect(
        "选择要对比的区县（默认全选）",
        options=all_districts,
        default=all_districts,
        help="影响「区县对比柱状图」和「老龄化散点图」",
    )

    # ---- 指标切换 ----
    st.subheader("📊 柱状图指标")
    bar_metric = st.selectbox(
        "选择区县对比柱状图的展示指标",
        options=[
            "total_resident",
            "urbanization_rate",
            "elderly_ratio",
            "natural_growth_rate",
            "population_density",
        ],
        format_func=lambda x: {
            "total_resident": "常住人口（万人）",
            "urbanization_rate": "城镇化率（%）",
            "elderly_ratio": "65 岁及以上占比（%）",
            "natural_growth_rate": "自然增长率（‰）",
            "population_density": "人口密度（人/km²）",
        }[x],
        help="切换柱状图展示的指标维度",
    )

    # ---- 地图指标 ----
    st.subheader("🗺️ 地图着色指标")
    map_metric = st.radio(
        "选择地图的颜色映射指标",
        options=["population_density", "urbanization_rate", "elderly_ratio"],
        format_func=lambda x: {
            "population_density": "人口密度",
            "urbanization_rate": "城镇化率",
            "elderly_ratio": "老龄化率",
        }[x],
        help="地图中各区域的颜色深浅将根据所选指标变化",
    )

    # ---- 数据来源 ----
    st.markdown("---")
    st.caption("📌 数据来源：温州市统计局、浙江省统计年鉴")
    st.caption("📌 样本数据基于公开趋势估算，正式使用请替换为官方统计")
    st.caption(f"📌 当前数据范围：{YEAR_MIN}–{YEAR_MAX} 年")

# ============================================================
# 主区域 :: 标题
# ============================================================
st.title("🏙️ 温州人口变迁 (2010–2023)")
st.markdown(
    """
    <div style="font-size:1.05em; line-height:1.8; color:#444;">
    温州——这座以民营经济闻名的沿海城市，在 2010 至 2023 年间经历了深刻的人口转型：
    <b>总量增长放缓、出生率断崖下降、老龄化加速加深、区县分化加剧</b>。
    本仪表板通过 <b>7 张交互式图表</b>，按照 <b>"总览 → 结构 → 区域"</b> 的故事线，
    带领您从数据中读出温州人口的过去、现在与未来。
    </div>
    """,
    unsafe_allow_html=True,
)

# ---- 关键数字卡片 ----
col1, col2, col3, col4 = st.columns(4)
latest = df_main[df_main["year"] == YEAR_MAX].iloc[0]
first = df_main[df_main["year"] == YEAR_MIN].iloc[0]

with col1:
    delta_total = latest["total_resident"] - first["total_resident"]
    st.metric(
        "常住人口（2023）",
        f"{latest['total_resident']:.0f} 万人",
        delta=f"{delta_total:+.0f} 万 (vs 2010)",
    )
with col2:
    delta_ur = latest["urbanization_rate"] - first["urbanization_rate"]
    st.metric(
        "城镇化率（2023）",
        f"{latest['urbanization_rate']:.1f}%",
        delta=f"{delta_ur:+.1f} pp",
    )
with col3:
    delta_elderly = latest["elderly_ratio"] - first["elderly_ratio"]
    st.metric(
        "65 岁及以上占比",
        f"{latest['elderly_ratio']:.1f}%",
        delta=f"{delta_elderly:+.1f} pp",
        delta_color="inverse",
    )
with col4:
    delta_gdpp = latest["gdpp"] - first["gdpp"]
    st.metric(
        "人均 GDP（2023）",
        f"{latest['gdpp']:,} 元",
        delta=f"增长 {delta_gdpp/10000:.1f} 万元",
    )

st.markdown("---")

# ============================================================
# 标签页结构
# ============================================================
tab1, tab2, tab3 = st.tabs([
    "📈 人口总览",
    "🧬 人口结构",
    "🗺️ 区域对比",
])

# ============================================================
# Tab 1：人口总览
# ============================================================
with tab1:
    st.subheader("人口规模与增长动力")

    # 叙事过渡
    st.markdown(
        """
        > **📖 故事线**：温州常住人口 14 年间从 911 万增至 976 万，表面看增长平稳，
        > 但仔细拆解会发现两个截然不同的故事：一方面，出生率从 13.6‰ 骤降至 6.5‰，
        > 自然增长率已逼近"零增长线"；另一方面，常住与户籍人口的差值从 114 万扩大到
        > 143 万，说明**机械增长（外来人口净流入）已成为维持温州人口正增长的唯一引擎**。
        > 这意味着温州的人口未来将越来越依赖城市吸引力而非自然生育。
        """
    )

    # 两列布局：左图 1（人口趋势），右图 2（出生死亡）
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### ① 常住人口 vs 户籍人口")
        fig1 = plot_population_trend(df_main, year_range)
        st.plotly_chart(fig1, width="stretch", key="chart1")
        with st.expander("📖 图表解读（点击展开）"):
            st.markdown(
                """
                这张图揭示了温州人口增长的"双引擎"结构。**蓝色实线**代表常住人口
                （实际居住在温州的所有人），**橙色虚线**代表户籍人口（仅拥有温州户口者），
                两者之间的**蓝色半透明填充区域**即为外来净流入人口——他们生活在温州但
                户口不在温州。2010 至 2023 年间，这个差值从约 114 万扩大至约 143 万，
                增长了近 30 万人，说明温州的就业机会和城市服务对外来人口的"拉力"在持续
                增强。同时请注意常住人口曲线的斜率在逐渐变小——年均增量从早期的 6 万降
                至近期的不足 3 万，这意味着即使外来人口持续流入，总人口增长也已进入平台期。
                """
            )

    with col_right:
        st.markdown("#### ② 出生率 / 死亡率 / 自然增长率")
        fig2 = plot_vital_rates(df_main, year_range)
        st.plotly_chart(fig2, width="stretch", key="chart2")
        with st.expander("📖 图表解读（点击展开）"):
            st.markdown(
                """
                三线汇聚讲述了一个令人警醒的故事。**红色线**（出生率）从 2010 年的 13.6‰
                一路下滑至 2023 年的 6.5‰，降幅超过 52%，即便 2016 年"全面二孩"政策
                实施也未能扭转颓势。**蓝色线**（死亡率）则因人口老龄化而缓慢爬升，从
                4.9‰ 升至 5.9‰。两条线的"剪刀差"不断收窄，**绿色线**（自然增长率 =
                出生率 - 死亡率）从 8.7‰ 骤降至 0.6‰，几乎触及灰色零值虚线。
                
                这意味着温州已进入"低出生、低死亡、低增长"的人口新常态。若出生率继续
                下行而死亡率随老龄化持续攀升，温州可能在不久的将来迎来首次**人口自然负增长**，
                届时全部人口增量都将依赖外来机械增长。
                """
            )

# ============================================================
# Tab 2：人口结构
# ============================================================
with tab2:
    st.subheader("年龄结构与老龄化")

    # 叙事过渡
    st.markdown(
        """
        > **📖 故事线**：如果说人口总量是"量变"，那年龄结构就是更深层的"质变"。
        > 温州 65 岁及以上老年人口占比从 7.8% 翻倍至 14.0%，平均每年上升 0.5 个
        > 百分点，速度快于全国同期。劳动年龄人口（15–64 岁）占比从 77.7% 降至 74.0%，
        > 意味着每 100 个劳动人口需要抚养的人数从 29 人增至 35 人。更值得警惕的是，
        > **郊县的老龄化程度并不低于城区**——文成、泰顺等山区县在城镇化水平较低的情况
        > 下就已进入深度老龄化，呈现出典型的"未富先老"特征。
        """
    )

    # 图 3：年龄结构堆叠面积图（全宽）
    st.markdown("#### ③ 人口年龄结构演变")
    fig3 = plot_age_structure(df_main, year_range)
    st.plotly_chart(fig3, width="stretch", key="chart3")

    col_info1, col_info2 = st.columns(2)
    with col_info1:
        with st.expander("📖 图表解读（点击展开）"):
            st.markdown(
                """
                这张堆叠面积图是温州人口结构转型最直观的"快照"。**浅蓝色区域**
                （0–14 岁少儿）从 14.5% 缩至 12.0%，**中蓝色区域**（15–64 岁劳动年龄）
                从 77.7% 缩至 74.0%，而**红色区域**（65 岁及以上老年）则从 7.8% 扩张
                至 14.0%——几乎翻了一倍。红色虚线标注了 2020 年全国 65+ 平均占比 13.5%，
                温州约在 2021 年前后超越全国线。
                
                "上下挤压"效应清晰可见：顶部红色向上蚕食、底部浅蓝向下退缩，中间的
                劳动年龄层被两面夹击。这直接推高了社会抚养比，给养老、医疗和社保体系
                带来持续压力。
                """
            )
    with col_info2:
        # 抚养比摘要
        latest_yr = min(year_range[1], YEAR_MAX)
        current_dep = df_main[df_main["year"] == latest_yr]["dependency_ratio"].values[0]
        st.info(
            f"📊 **{latest_yr} 年总抚养比：{current_dep:.1f}%**\n\n"
            f"即每 100 名劳动年龄人口需抚养约 {int(current_dep)} 名非劳动年龄人口"
            f"（少儿 + 老年），较 2010 年的 "
            f"{df_main[df_main['year']==YEAR_MIN]['dependency_ratio'].values[0]:.1f}% "
            f"上升了 {current_dep - df_main[df_main['year']==YEAR_MIN]['dependency_ratio'].values[0]:.1f} 个百分点。"
        )

    # 图 4：老龄化 vs 城镇化散点图
    st.markdown("#### ④ 各区县老龄化率 vs 城镇化率")
    selected_year_scatter = st.selectbox(
        "选择散点图年份（或选择「全部」观看动画）",
        options=["全部"] + list(range(year_range[0], year_range[1] + 1)),
        key="scatter_year",
    )
    scatter_year = None if selected_year_scatter == "全部" else selected_year_scatter
    fig4 = plot_elderly_urbanization(
        df_dist,
        selected_districts=selected_districts,
        selected_year=scatter_year,
    )
    st.plotly_chart(fig4, width="stretch", key="chart4")

    with st.expander("📖 图表解读（点击展开）"):
        st.markdown(
            """
            散点图揭示了温州人口空间分化的一个**反直觉规律**：城镇化率越高的区县，
            老龄化率反而越低。**蓝色圆点**（核心城区：鹿城、龙湾、瓯海、龙港）集中在
            图的右下区域——高城镇化、相对低老龄化；**橙色方点**（郊县：文成、泰顺、
            永嘉等）分布在左上区域——低城镇化、高老龄化。
            
            原因在于"劳动力虹吸效应"：核心城区凭借更好的就业机会和公共服务，持续吸引
            年轻劳动力流入，稀释了老年人口占比；而郊县年轻人外出务工，留下老年人口，
            老龄化率被"被动推高"。
            """
        )

# ============================================================
# Tab 3：区域对比
# ============================================================
with tab3:
    st.subheader("区县差异与空间分布")

    # 叙事过渡
    st.markdown(
        """
        > **📖 故事线**：将镜头从全市拉近到 12 个区县，分化格局一目了然。沿海经济
        > 强县（瑞安、乐清）凭借制造业集群持续吸纳人口，而海岛（洞头）和山区县
        > （文成、泰顺）因地理限制和产业单一，人口吸引力不足。这种"马太效应"正在
        > 重塑温州的人口地理版图——人口向沿海城市带集中，内陆山区逐渐空心化。
        > 同时，各区县的城镇化进程与经济发展紧密挂钩，形成了"越发达越聚集、越聚集
        > 越发达"的正反馈循环。
        """
    )

    # 左右两列
    col_left2, col_right2 = st.columns(2)

    with col_left2:
        st.markdown("#### ⑤ 分区县人口指标对比")
        fig5 = plot_district_comparison(df_dist, year_range, bar_metric, selected_districts)
        st.plotly_chart(fig5, width="stretch", key="chart5")
        with st.expander("📖 图表解读（点击展开）"):
            metric_names = {
                "total_resident": "常住人口（万人）",
                "urbanization_rate": "城镇化率（%）",
                "elderly_ratio": "65 岁及以上占比（%）",
                "natural_growth_rate": "自然增长率（‰）",
                "population_density": "人口密度（人/km²）",
            }
            st.markdown(
                f"""
                水平柱状图展示各区县在 **{metric_names.get(bar_metric, bar_metric)}**
                指标上的差异。蓝色（正值）表示增长，红色（负值）表示收缩。
                
                通过左侧边栏可切换 5 种指标，从不同维度对比各区县：
                - **常住人口**：瑞安、乐清以超 150 万人口遥遥领先
                - **城镇化率**：鹿城、龙湾、龙港超过 90%，文成、泰顺不足 50%
                - **老龄化率**：瓯海、平阳突破 13%，乐清、苍南低于 8%
                - **自然增长率**：核心城区仍为正增长，部分郊县已接近零或负增长
                
                这种"核心城区 vs 郊县"的分化格局是温州人口变迁最核心的空间特征。
                """
            )

    with col_right2:
        st.markdown("#### ⑥ 城镇化率与人均 GDP")
        fig6 = plot_urbanization_gdp(df_main, year_range)
        st.plotly_chart(fig6, width="stretch", key="chart6")
        with st.expander("📖 图表解读（点击展开）"):
            filtered = df_main[
                (df_main["year"] >= year_range[0]) & (df_main["year"] <= year_range[1])
            ]
            corr = filtered["urbanization_rate"].corr(filtered["gdpp"])
            gdp_per_ur = filtered["gdpp"].diff().mean() / filtered["urbanization_rate"].diff().mean()
            st.markdown(
                f"""
                双 Y 轴图展示了城镇化率（**蓝色实线**，左轴）与人均 GDP（**橙色虚线**，
                右轴）在 2010–2023 年间的协同增长轨迹。两条曲线几乎平行上升，Pearson
                相关系数达到 **r = {corr:.3f}**（极高相关）。
                
                从数据来看，城镇化率每提升 1 个百分点，人均 GDP 约增长 **{gdp_per_ur:.0f}
                元**。这一方面反映了城镇化带来的产业集聚效应——人口向城市集中降低了交易
                成本、扩大了市场规模；另一方面也说明经济发展反过来推动了城市建设，吸引
                更多农村人口进城。两者形成了"城镇化 → 经济增长 → 更多城镇化"的正反馈
                循环，是理解温州过去 14 年发展的核心经济逻辑。
                """
            )

    # 图 7：地图（全宽）
    st.markdown("#### ⑦ 分区县人口密度地图")
    map_year = st.slider(
        "选择地图年份",
        min_value=year_range[0],
        max_value=year_range[1],
        value=year_range[1],
        step=1,
        key="map_year",
    )
    fig7 = plot_population_map(df_dist, map_year, map_metric)
    if fig7 is not None:
        st.plotly_chart(fig7, width="stretch", key="chart7")
    else:
        st.warning(
            "⚠️ 地图数据暂不可用。请确保 `data/wenzhou_districts.geojson` 文件存在。"
            "\n\n> 可以从 [DataV.GeoAtlas](https://datav.aliyun.com/portal/school/atlas/area_selector) "
            "下载温州各区县的真实 GeoJSON 数据替换。"
        )

    with st.expander("📖 图表解读"):
        map_metric_label = {
            'population_density': '人口密度',
            'urbanization_rate': '城镇化率',
            'elderly_ratio': '老龄化率',
        }.get(map_metric, map_metric)
        st.markdown(
            f"""
            地图直观展示了温州 12 个区县的 **{map_metric_label}** 空间分布。
            
            - **颜色越深**表示数值越高。可悬停各区县查看详细数值卡片。
            - 通过左侧边栏可切换地图的着色指标。
            - 通过上方滑块可切换年份，观察空间格局的逐年变化。
            
            """
        )

# ============================================================
# 页脚
# ============================================================
st.markdown("---")
st.markdown(
    """
    <div style="text-align:center; color: #888; font-size: 0.85em;">
    📊 温州人口变迁 · 数据可视化课程项目 &nbsp;|&nbsp;
    数据来源：温州市统计局、浙江省统计年鉴 &nbsp;|&nbsp;
    样本数据基于公开趋势估算，正式使用请替换为官方统计
    </div>
    """,
    unsafe_allow_html=True,
)
