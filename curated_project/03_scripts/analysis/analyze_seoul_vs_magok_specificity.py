from pathlib import Path
import re
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager, rcParams

ROOT = Path(__file__).resolve().parents[2]
OUT_TABLE = ROOT / "04_outputs" / "tables"
OUT_FIG = ROOT / "04_outputs" / "figures"
OUT_REPORT = ROOT / "04_outputs" / "reports"
for d in [OUT_TABLE, OUT_FIG, OUT_REPORT]:
    d.mkdir(parents=True, exist_ok=True)

# Font setup for Korean labels. Apply style first because matplotlib styles can reset fonts.
plt.style.use("seaborn-v0_8-whitegrid")
font_candidates = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]
for fp in font_candidates:
    if Path(fp).exists():
        font_manager.fontManager.addfont(fp)
        rcParams["font.family"] = font_manager.FontProperties(fname=fp).get_name()
        break
rcParams["axes.unicode_minus"] = False

# -----------------------------
# 1. Load existing curated data
# -----------------------------
one_metrics = pd.read_csv(ROOT / "02_processed_data/one_person_households/magok_specificity_one_person_metrics.csv")
one_by_dong = pd.read_csv(ROOT / "02_processed_data/one_person_households/gangseo_one_person_households_by_dong_2024.csv")
demo_comp = pd.read_csv(ROOT / "02_processed_data/demographics/magok_demographic_specificity_comparison.csv")
airport = pd.read_csv(ROOT / "02_processed_data/airport/kac_airport_year_stats_tidy_2016_2025.csv")

# Values from one-person metrics
metric_map = dict(zip(one_metrics["metric"], one_metrics["value"]))
seoul_total_one = int(metric_map["서울 전체 1인가구"])
seoul_avg_one = int(metric_map["서울 자치구 평균 1인가구"])
gangseo_one = int(metric_map["강서구 1인가구"])
magok_related_one = int(metric_map["마곡 관련 후보 행정동 1인가구"])

# Magok-related dongs: prefer flag column when available
magok_dongs = one_by_dong[one_by_dong["magok_related_flag"] == True].copy()
magok_dongs = magok_dongs.sort_values("one_person_households", ascending=False)

# Airport: Gimpo total passenger latest and baseline
airport_total = airport[(airport["airport_code"] == "GMP") & (airport["line_type"] == "total")].copy()
latest_year = int(airport_total["year"].max())
baseline_year = 2019 if 2019 in set(airport_total["year"]) else int(airport_total["year"].min())
gmp_latest = int(airport_total.loc[airport_total["year"] == latest_year, "passenger_total_current"].iloc[0])
gmp_baseline = int(airport_total.loc[airport_total["year"] == baseline_year, "passenger_total_current"].iloc[0])
gmp_change_pct = (gmp_latest / gmp_baseline - 1) * 100

# Domestic/international share in latest year if line_type exists
airport_gmp_latest = airport[(airport["airport_code"] == "GMP") & (airport["year"] == latest_year)]
domestic_val = airport_gmp_latest.loc[airport_gmp_latest["line_type"].astype(str).str.contains("domestic|국내", case=False, regex=True), "passenger_total_current"].sum()
international_val = airport_gmp_latest.loc[airport_gmp_latest["line_type"].astype(str).str.contains("international|국제", case=False, regex=True), "passenger_total_current"].sum()
if domestic_val == 0 or international_val == 0:
    # Fallback from previous synthesis table when tidy line labels differ
    domestic_share_latest = 80.674
else:
    domestic_share_latest = domestic_val / (domestic_val + international_val) * 100

# KAC share in latest year: Gimpo total / all airports total
all_latest_total = int(airport[(airport["airport_code"] == "ALL") & (airport["line_type"] == "total") & (airport["year"] == latest_year)]["passenger_total_current"].iloc[0])
gmp_kac_share = gmp_latest / all_latest_total * 100

# Industrial and hospital values from previously verified source notes/synthesis table
magok_workers_2025 = 39966
magok_rd_workers_2025 = 18301
magok_rd_share = magok_rd_workers_2025 / magok_workers_2025 * 100
hospital_beds = 1014

# ------------------------------------
# 2. Build comparison-ready data tables
# ------------------------------------
seoul_comparison_rows = [
    {
        "comparison_axis": "1인가구 기반",
        "metric": "2024년 1인가구 수",
        "seoul_baseline": f"서울 자치구 평균 {seoul_avg_one:,}가구",
        "target_unit": "강서구",
        "target_value": f"{gangseo_one:,}가구",
        "ratio_vs_seoul_avg": round(gangseo_one / seoul_avg_one, 2),
        "interpretation": "강서구는 서울 평균 자치구보다 1인가구 규모가 약 1.61배 크다.",
    },
    {
        "comparison_axis": "마곡권 1인가구",
        "metric": "마곡 관련 후보 행정동 1인가구 합계",
        "seoul_baseline": f"강서구 전체 {gangseo_one:,}가구",
        "target_unit": "마곡 관련 후보 행정동",
        "target_value": f"{magok_related_one:,}가구",
        "ratio_vs_seoul_avg": round(magok_related_one / gangseo_one, 3),
        "interpretation": "마곡 관련 후보 행정동만으로도 강서구 전체 1인가구의 23.35%를 차지한다.",
    },
    {
        "comparison_axis": "청년·직장인 구조",
        "metric": "20~39세 인구 비중",
        "seoul_baseline": "강서구 전체 30.39%",
        "target_unit": "마곡핵심권(발산1동+가양1동)",
        "target_value": "35.53%",
        "ratio_vs_seoul_avg": round(35.525230 / 30.385117, 2),
        "interpretation": "마곡핵심권의 20~39세 비중은 강서구 전체보다 약 5.14%p 높다.",
    },
    {
        "comparison_axis": "공항 거점성",
        "metric": f"{latest_year}년 김포공항 총여객",
        "seoul_baseline": "서울 일반 생활권에는 없는 광역 공항 기능",
        "target_unit": "김포공항",
        "target_value": f"{gmp_latest:,}명",
        "ratio_vs_seoul_avg": None,
        "interpretation": f"김포공항은 {latest_year}년에도 약 {gmp_latest/10000:.0f}만 명의 여객을 처리해 이동 전후 대기 수요를 만든다.",
    },
    {
        "comparison_axis": "병원·응급 기능",
        "metric": "이대서울병원 병상 규모",
        "seoul_baseline": "일반 상권과 차별되는 광역 의료 기능",
        "target_unit": "이대서울병원",
        "target_value": f"{hospital_beds:,}병상",
        "ratio_vs_seoul_avg": None,
        "interpretation": "1,000병상급 대학병원과 지역응급의료센터 기능은 보호자 체류·의료진 교대근무 수요를 설명하는 핵심 근거다.",
    },
    {
        "comparison_axis": "기업/R&D 집적",
        "metric": "2025년 마곡사업장 근무인원",
        "seoul_baseline": "일반 주거지와 차별되는 R&D 업무 기능",
        "target_unit": "마곡산업단지",
        "target_value": f"{magok_workers_2025:,}명",
        "ratio_vs_seoul_avg": None,
        "interpretation": f"마곡산단은 약 {magok_workers_2025/10000:.1f}만 명 근무 기반을 가지며, 이 중 R&D 인력이 {magok_rd_share:.1f}%다.",
    },
]
comparison = pd.DataFrame(seoul_comparison_rows)
comparison["ratio_vs_seoul_avg"] = comparison["ratio_vs_seoul_avg"].apply(lambda x: "비교단위 다름" if pd.isna(x) else x)
comparison.to_csv(OUT_TABLE / "seoul_vs_magok_specificity_comparison.csv", index=False, encoding="utf-8-sig")
comparison.to_markdown(OUT_TABLE / "seoul_vs_magok_specificity_comparison.md", index=False)

# Detail table: magok-related one-person households by admin dong
magok_dongs_out = magok_dongs[["dong", "one_person_households", "share_of_gangseo_pct"]].copy()
magok_dongs_out["rank_within_gangseo"] = magok_dongs_out["one_person_households"].rank(ascending=False, method="min").astype(int)
magok_dongs_out = magok_dongs_out.sort_values("one_person_households", ascending=False)
magok_dongs_out.to_csv(OUT_TABLE / "magok_related_one_person_households_by_dong.csv", index=False, encoding="utf-8-sig")
magok_dongs_out.to_markdown(OUT_TABLE / "magok_related_one_person_households_by_dong.md", index=False)

# ------------------------------------
# 3. Charts for presentation
# ------------------------------------
# Chart 1: One-person households comparison
fig, ax = plt.subplots(figsize=(9, 5.5))
labels = ["서울 자치구 평균", "강서구", "마곡 관련\n후보 행정동"]
values = [seoul_avg_one, gangseo_one, magok_related_one]
colors = ["#9CA3AF", "#2563EB", "#10B981"]
bars = ax.bar(labels, values, color=colors)
ax.set_title("서울 평균 대비 강서구·마곡권 1인가구 규모", fontsize=15, weight="bold")
ax.set_ylabel("1인가구 수(가구)")
ax.set_ylim(0, max(values) * 1.28)
for b, v in zip(bars, values):
    ax.text(b.get_x() + b.get_width()/2, v + max(values)*0.03, f"{v:,}", ha="center", fontsize=11, weight="bold")
ax.text(1, gangseo_one + max(values)*0.15, f"서울 평균 대비 {gangseo_one/seoul_avg_one:.2f}배", ha="center", color="#1D4ED8", fontsize=11, weight="bold")
ax.text(2, magok_related_one + max(values)*0.15, f"강서구의 {magok_related_one/gangseo_one*100:.1f}%", ha="center", color="#047857", fontsize=11, weight="bold")
fig.tight_layout()
fig.savefig(OUT_FIG / "seoul_vs_gangseo_magok_one_person_households.png", dpi=220)
plt.close(fig)

# Chart 2: Demographic specificity: 20~39 share and household change
plot_demo = demo_comp[demo_comp["comparison_unit"].isin(["마곡핵심권(발산1동+가양1동)", "공항연계권(공항동+방화1동)", "강서구 전체"])]
fig, ax = plt.subplots(figsize=(10, 5.8))
x = range(len(plot_demo))
bar1 = ax.bar([i - 0.18 for i in x], plot_demo["share_20_39_latest_pct"], width=0.36, label="20~39세 비중(%)", color="#7C3AED")
bar2 = ax.bar([i + 0.18 for i in x], plot_demo["households_change_pct"], width=0.36, label="2019~최근 세대 증가율(%)", color="#F59E0B")
ax.set_xticks(list(x))
ax.set_xticklabels(plot_demo["comparison_unit"], rotation=0)
ax.set_title("마곡핵심권은 강서구 평균보다 젊고, 세대 증가 신호가 크다", fontsize=15, weight="bold")
ax.set_ylabel("비율(%)")
ax.legend(loc="upper right")
for bars in [bar1, bar2]:
    for b in bars:
        v = b.get_height()
        ax.text(b.get_x()+b.get_width()/2, v + (1 if v >= 0 else -2), f"{v:.1f}", ha="center", va="bottom" if v>=0 else "top", fontsize=10)
fig.tight_layout()
fig.savefig(OUT_FIG / "magok_core_demographic_specificity_vs_gangseo.png", dpi=220)
plt.close(fig)

# Chart 3: Functional demand cards as horizontal bars with independent units noted
func = pd.DataFrame([
    {"label": f"김포공항 {latest_year}년 총여객", "value": gmp_latest/10000, "unit": "만 명", "color": "#2563EB"},
    {"label": "이대서울병원 병상", "value": hospital_beds, "unit": "병상", "color": "#DC2626"},
    {"label": "마곡산단 근무인원", "value": magok_workers_2025, "unit": "명", "color": "#059669"},
    {"label": "마곡산단 R&D 인력", "value": magok_rd_workers_2025, "unit": "명", "color": "#0F766E"},
])
fig, ax = plt.subplots(figsize=(10, 5.8))
ypos = range(len(func))
# normalize widths for visual comparability while annotating original values
func["norm"] = func["value"] / func["value"].max() * 100
bars = ax.barh(list(ypos), func["norm"], color=func["color"])
ax.set_yticks(list(ypos))
ax.set_yticklabels(func["label"])
ax.invert_yaxis()
ax.set_xlim(0, 120)
ax.set_xlabel("시각화를 위한 상대 길이: 실제 단위는 막대 옆 표기")
ax.set_title("마곡 주변 특수 기능시설이 만드는 수요 규모", fontsize=15, weight="bold")
for b, (_, r) in zip(bars, func.iterrows()):
    if r["unit"] == "만 명":
        txt = f"{r['value']:.0f}{r['unit']}"
    else:
        txt = f"{int(r['value']):,}{r['unit']}"
    ax.text(b.get_width() + 2, b.get_y()+b.get_height()/2, txt, va="center", fontsize=11, weight="bold")
fig.tight_layout()
fig.savefig(OUT_FIG / "magok_functional_demand_scale_indicators.png", dpi=220)
plt.close(fig)

# ------------------------------------
# 4. Write a concise presentation memo
# ------------------------------------
report = f"""# 서울 평균 대비 마곡 특수성 수치 비교 메모

## 1. 핵심 결론

마곡은 단순히 유동인구가 많은 역세권으로 설명하기보다, **서울 평균보다 큰 1인가구 기반을 가진 강서구 안에서 공항·대학병원·R&D 산업단지 기능이 한꺼번에 중첩된 지역**으로 설명하는 것이 데이터 발표에 적합하다.

가장 먼저 제시할 수 있는 수치는 1인가구다. 2024년 서울 전체 1인가구는 **{seoul_total_one:,}가구**이고, 서울 25개 자치구 단순 평균은 **{seoul_avg_one:,}가구**다. 강서구의 1인가구는 **{gangseo_one:,}가구**로, 서울 자치구 평균의 **{gangseo_one/seoul_avg_one:.2f}배**다. 또한 마곡 관련 후보 행정동의 1인가구는 **{magok_related_one:,}가구**로 강서구 전체의 **{magok_related_one/gangseo_one*100:.2f}%**를 차지한다.

| 비교 항목 | 기준값 | 마곡·강서 관련 값 | 해석 |
|---|---:|---:|---|
| 1인가구 기반 | 서울 자치구 평균 {seoul_avg_one:,}가구 | 강서구 {gangseo_one:,}가구 | 서울 평균 대비 {gangseo_one/seoul_avg_one:.2f}배 |
| 마곡 관련 행정동 1인가구 | 강서구 전체 {gangseo_one:,}가구 | {magok_related_one:,}가구 | 강서구의 {magok_related_one/gangseo_one*100:.2f}% |
| 청년·직장인 비중 | 강서구 전체 30.39% | 마곡핵심권 35.53% | 강서구보다 5.14%p 높음 |
| 공항 수요 | 일반 생활권에는 없는 기능 | 김포공항 {latest_year}년 {gmp_latest:,}명 | 이동 전후 대기·단기 체류 수요 근거 |
| 병원 수요 | 일반 상권과 차별 기능 | 이대서울병원 {hospital_beds:,}병상 | 보호자 체류·응급·교대근무 수요 근거 |
| 업무/R&D 수요 | 일반 주거지와 차별 기능 | 마곡산단 근무인원 {magok_workers_2025:,}명 | 직장인·방문객·야근·출장 수요 근거 |

## 2. 발표에서 사용할 문장

> **강서구는 2024년 1인가구가 106,748가구로 서울 자치구 평균의 1.61배이며, 마곡 관련 후보 행정동만으로도 강서구 1인가구의 23.35%를 차지한다. 여기에 김포공항 연 2,296만 명 여객, 이대서울병원 1,014병상, 마곡산업단지 근무인원 39,966명이 중첩되기 때문에, 마곡은 단순 역세권이 아니라 이동·의료·업무·1인가구 생활 수요가 겹치는 복합 체류 생활권으로 볼 수 있다.**

## 3. 주의할 점

모든 지표를 서울 평균과 동일한 방식으로 비교할 수는 없다. 1인가구와 인구구조는 서울 평균 또는 강서구 평균과 직접 비교할 수 있지만, 공항 여객·병원 병상·산업단지 근무인원은 서울 평균 행정동과 동일 단위 비교가 어렵다. 따라서 발표에서는 이들을 **서울 일반 생활권에는 없는 기능적 수요 발생 장치**로 제시하는 것이 적절하다.

## 4. 생성 파일

| 파일 | 설명 |
|---|---|
| `04_outputs/tables/seoul_vs_magok_specificity_comparison.md` | 서울 평균 대비 마곡 특수성 비교표 |
| `04_outputs/tables/magok_related_one_person_households_by_dong.md` | 마곡 관련 행정동별 1인가구 세부표 |
| `04_outputs/figures/seoul_vs_gangseo_magok_one_person_households.png` | 1인가구 비교 차트 |
| `04_outputs/figures/magok_core_demographic_specificity_vs_gangseo.png` | 마곡핵심권·공항연계권·강서구 인구구조 비교 차트 |
| `04_outputs/figures/magok_functional_demand_scale_indicators.png` | 공항·병원·산업단지 기능 규모 차트 |
"""
(OUT_REPORT / "seoul_vs_magok_specificity_presentation_memo.md").write_text(report, encoding="utf-8")

print("Generated:")
for p in [
    OUT_TABLE / "seoul_vs_magok_specificity_comparison.md",
    OUT_TABLE / "magok_related_one_person_households_by_dong.md",
    OUT_REPORT / "seoul_vs_magok_specificity_presentation_memo.md",
    OUT_FIG / "seoul_vs_gangseo_magok_one_person_households.png",
    OUT_FIG / "magok_core_demographic_specificity_vs_gangseo.png",
    OUT_FIG / "magok_functional_demand_scale_indicators.png",
]:
    print(p.relative_to(ROOT))
