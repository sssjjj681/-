# ============================================================
# 阶段 1.3：构造温州人口变迁样本数据集
# 说明：基于公开趋势估算，用于 Streamlit 应用开发和测试。
#       正式项目请替换为真实统计数据。
# ============================================================
import pandas as pd
import numpy as np
import os

# ---------- 1. 全市年度主表 ----------
np.random.seed(42)

years = list(range(2010, 2024))  # 2010-2023 共 14 年
n = len(years)

# 基于真实趋势构造（温州市常住人口约 900-970 万区间）
total_resident = np.round(np.linspace(912, 976, n) + np.random.uniform(-2, 2, n), 1)
total_registered = np.round(np.linspace(798, 832, n) + np.random.uniform(-1, 1, n), 1)
urban_pop = np.round(total_resident * np.linspace(0.66, 0.735, n), 1)
rural_pop = np.round(total_resident - urban_pop, 1)
urbanization_rate = np.round(urban_pop / total_resident * 100, 2)

birth_rate = np.round(np.linspace(13.5, 6.5, n) + np.random.uniform(-0.3, 0.3, n), 2)
death_rate = np.round(np.linspace(5.0, 5.8, n) + np.random.uniform(-0.1, 0.1, n), 2)
natural_growth_rate = np.round(birth_rate - death_rate, 2)
net_migration = np.round(np.linspace(8.0, 3.5, n) + np.random.uniform(-1, 1, n), 1)

elderly_ratio = np.round(np.linspace(7.7, 14.2, n) + np.random.uniform(-0.2, 0.2, n), 2)
child_ratio = np.round(np.linspace(14.5, 12.0, n) + np.random.uniform(-0.1, 0.1, n), 2)
working_age_ratio = np.round(100 - elderly_ratio - child_ratio, 2)

gdpp = (np.linspace(37000, 85000, n) + np.random.uniform(-500, 500, n)).astype(int)

df_main = pd.DataFrame({
    "year": years,
    "total_resident": total_resident,
    "total_registered": total_registered,
    "urban_pop": urban_pop,
    "rural_pop": rural_pop,
    "urbanization_rate": urbanization_rate,
    "birth_rate": birth_rate,
    "death_rate": death_rate,
    "natural_growth_rate": natural_growth_rate,
    "net_migration": net_migration,
    "elderly_ratio": elderly_ratio,
    "child_ratio": child_ratio,
    "working_age_ratio": working_age_ratio,
    "gdpp": gdpp,
})

# ---------- 2. 分区县年度副表 ----------
districts = [
    "鹿城区", "龙湾区", "瓯海区", "洞头区",
    "永嘉县", "平阳县", "苍南县", "文成县", "泰顺县",
    "瑞安市", "乐清市", "龙港市"
]

rows = []
for year in years:
    for dist in districts:
        # 各区县人口基数不同（单位：万人）
        base_pop = {
            "鹿城区": 78, "龙湾区": 55, "瓯海区": 46, "洞头区": 16,
            "永嘉县": 87, "平阳县": 76, "苍南县": 84, "文成县": 29, "泰顺县": 26,
            "瑞安市": 152, "乐清市": 146, "龙港市": 47
        }
        pop = base_pop[dist] * (0.98 + 0.04 * (year - 2010) / 13)  # 温和增长
        pop += np.random.uniform(-1, 1)
        ur = {
            "鹿城区": 0.92, "龙湾区": 0.88, "瓯海区": 0.80, "洞头区": 0.60,
            "永嘉县": 0.55, "平阳县": 0.52, "苍南县": 0.54, "文成县": 0.43, "泰顺县": 0.40,
            "瑞安市": 0.68, "乐清市": 0.66, "龙港市": 0.92
        }[dist] + 0.005 * (year - 2010)
        ur = min(ur, 0.96)

        rows.append({
            "year": year,
            "district": dist,
            "total_resident": round(pop, 1),
            "urban_pop": round(pop * ur, 1),
            "rural_pop": round(pop * (1 - ur), 1),
            "urbanization_rate": round(ur * 100, 2),
            "population_density": round(pop / base_pop.get(dist, 50) * 1200 + np.random.uniform(-50, 50)),
            "natural_growth_rate": round(np.random.uniform(1, 6) if dist in ["鹿城区", "龙湾区", "龙港市"] else np.random.uniform(-1, 3), 2),
            "elderly_ratio": round(np.random.uniform(10, 18) if dist in ["文成县", "泰顺县"] else np.random.uniform(7, 14), 2),
            "net_migration": round(np.random.uniform(1, 4) if dist in ["鹿城区", "龙湾区", "瓯海区", "瑞安市"] else np.random.uniform(-2, 1), 1),
        })

df_district = pd.DataFrame(rows)

# ---------- 3. 保存到 data/ 目录 ----------
os.makedirs("wenzhou_population/data", exist_ok=True)
df_main.to_csv("wenzhou_population/data/wenzhou_population.csv", index=False, encoding="utf-8-sig")
df_district.to_csv("wenzhou_population/data/wenzhou_district_population.csv", index=False, encoding="utf-8-sig")

# ---------- 4. 验证数据 ----------
print("全市主表 shape:", df_main.shape)
print("区县副表 shape:", df_district.shape)
print("\n主表前 3 行：")
print(df_main.head(3))
print("\n区县表中的区县列表：", df_district["district"].unique().tolist())
print("\n数据已保存到 wenzhou_population/data/")
