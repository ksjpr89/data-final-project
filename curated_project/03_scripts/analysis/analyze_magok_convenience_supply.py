from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib import font_manager, rcParams
import seaborn as sns

ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "02_processed_data" / "store_and_facility" / "tableau_convenience_stores_gangseo.csv"
OUTPUT_TABLE_DIR = ROOT / "04_outputs" / "tables"
OUTPUT_FIG_DIR = ROOT / "04_outputs" / "figures"
OUTPUT_REPORT_DIR = ROOT / "04_outputs" / "reports"

for d in [OUTPUT_TABLE_DIR, OUTPUT_FIG_DIR, OUTPUT_REPORT_DIR]:
    d.mkdir(parents=True, exist_ok=True)

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

MAGOK_CORE = ["발산1동", "가양1동"]
AIRPORT_LINKED = ["공항동", "방화1동"]
MAGOK_RELATED = MAGOK_CORE + AIRPORT_LINKED

BRAND_ORDER = ["CU", "GS25", "세븐일레븐", "이마트24", "미니스톱", "기타/미분류"]
BRAND_COLORS = {
    "CU": "#6f42c1",
    "GS25": "#2f80ed",
    "세븐일레븐": "#00a65a",
    "이마트24": "#f2c94c",
    "미니스톱": "#eb5757",
    "기타/미분류": "#828282",
}
ZONE_COLORS = {
    "마곡핵심권": "#7c3aed",
    "공항연계권": "#0ea5e9",
    "기타 강서구": "#cbd5e1",
}


def assign_zone(admin_dong: str) -> str:
    if admin_dong in MAGOK_CORE:
        return "마곡핵심권"
    if admin_dong in AIRPORT_LINKED:
        return "공항연계권"
    return "기타 강서구"


def write_md_table(df: pd.DataFrame, path: Path) -> None:
    path.write_text(df.to_markdown(index=False), encoding="utf-8")


def main() -> None:
    df = pd.read_csv(DATA_PATH)
    df = df.dropna(subset=["longitude", "latitude", "admin_dong"]).copy()
    df["zone"] = df["admin_dong"].map(assign_zone)
    df["brand"] = df["brand"].fillna("기타/미분류")
    df.loc[~df["brand"].isin(BRAND_ORDER), "brand"] = "기타/미분류"

    total_gangseo = len(df)
    admin_counts = (
        df.groupby(["admin_dong", "zone"], as_index=False)
        .agg(store_count=("candidate_store_id", "count"), brand_count=("brand", "nunique"))
        .sort_values("store_count", ascending=False)
    )
    admin_counts["share_of_gangseo_pct"] = admin_counts["store_count"] / total_gangseo * 100
    gangseo_avg = admin_counts["store_count"].mean()
    admin_counts["ratio_vs_gangseo_admin_avg"] = admin_counts["store_count"] / gangseo_avg

    zone_summary = (
        df.groupby("zone", as_index=False)
        .agg(store_count=("candidate_store_id", "count"), brand_count=("brand", "nunique"))
    )
    zone_summary["share_of_gangseo_pct"] = zone_summary["store_count"] / total_gangseo * 100
    zone_order = pd.CategoricalDtype(["마곡핵심권", "공항연계권", "기타 강서구"], ordered=True)
    zone_summary["zone"] = zone_summary["zone"].astype(zone_order)
    zone_summary = zone_summary.sort_values("zone")

    magok_related = df[df["admin_dong"].isin(MAGOK_RELATED)].copy()
    magok_admin = admin_counts[admin_counts["admin_dong"].isin(MAGOK_RELATED)].copy()
    magok_admin["admin_dong"] = pd.Categorical(magok_admin["admin_dong"], MAGOK_RELATED, ordered=True)
    magok_admin = magok_admin.sort_values("admin_dong")

    brand_by_dong = (
        magok_related.pivot_table(
            index="admin_dong",
            columns="brand",
            values="candidate_store_id",
            aggfunc="count",
            fill_value=0,
        )
        .reindex(MAGOK_RELATED)
        .reindex(columns=BRAND_ORDER, fill_value=0)
        .reset_index()
    )
    brand_by_dong["total"] = brand_by_dong[BRAND_ORDER].sum(axis=1)

    summary_rows = [
        {
            "metric": "강서구 전체 편의점",
            "unit": "강서구",
            "value": total_gangseo,
            "comparison": "분석 기준 전체",
            "interpretation": "강서구 편의점 공급의 전체 모수다.",
        },
        {
            "metric": "강서구 행정동 평균 편의점",
            "unit": "20개 행정동 단순 평균",
            "value": round(gangseo_avg, 1),
            "comparison": "강서구 전체 / 행정동 수",
            "interpretation": "마곡권 행정동별 편의점 수를 비교하는 기준값이다.",
        },
        {
            "metric": "마곡핵심권 편의점",
            "unit": "발산1동+가양1동",
            "value": int(zone_summary.loc[zone_summary["zone"] == "마곡핵심권", "store_count"].iloc[0]),
            "comparison": f"강서구 전체의 {zone_summary.loc[zone_summary['zone'] == '마곡핵심권', 'share_of_gangseo_pct'].iloc[0]:.2f}%",
            "interpretation": "마곡역·발산역·업무지구와 맞닿은 핵심 생활권의 공급 규모다.",
        },
        {
            "metric": "공항연계권 편의점",
            "unit": "공항동+방화1동",
            "value": int(zone_summary.loc[zone_summary["zone"] == "공항연계권", "store_count"].iloc[0]),
            "comparison": f"강서구 전체의 {zone_summary.loc[zone_summary['zone'] == '공항연계권', 'share_of_gangseo_pct'].iloc[0]:.2f}%",
            "interpretation": "김포공항 접근성과 방화 생활권을 함께 보는 보조 권역의 공급 규모다.",
        },
        {
            "metric": "마곡 관련 4개 행정동 편의점",
            "unit": "발산1동+가양1동+공항동+방화1동",
            "value": len(magok_related),
            "comparison": f"강서구 전체의 {len(magok_related) / total_gangseo * 100:.2f}%",
            "interpretation": "기존 수요 분석에서 설정한 마곡 관련 후보 행정동의 편의점 공급 기반이다.",
        },
    ]
    supply_summary = pd.DataFrame(summary_rows)

    admin_counts_out = admin_counts.copy()
    for col in ["share_of_gangseo_pct", "ratio_vs_gangseo_admin_avg"]:
        admin_counts_out[col] = admin_counts_out[col].round(2)
    magok_admin_out = magok_admin.copy()
    for col in ["share_of_gangseo_pct", "ratio_vs_gangseo_admin_avg"]:
        magok_admin_out[col] = magok_admin_out[col].round(2)
    zone_summary_out = zone_summary.copy()
    zone_summary_out["share_of_gangseo_pct"] = zone_summary_out["share_of_gangseo_pct"].round(2)

    supply_summary.to_csv(OUTPUT_TABLE_DIR / "magok_convenience_supply_summary.csv", index=False, encoding="utf-8-sig")
    admin_counts_out.to_csv(OUTPUT_TABLE_DIR / "gangseo_convenience_count_by_admin_dong_updated.csv", index=False, encoding="utf-8-sig")
    magok_admin_out.to_csv(OUTPUT_TABLE_DIR / "magok_related_convenience_count_by_admin_dong.csv", index=False, encoding="utf-8-sig")
    zone_summary_out.to_csv(OUTPUT_TABLE_DIR / "magok_convenience_zone_summary.csv", index=False, encoding="utf-8-sig")
    brand_by_dong.to_csv(OUTPUT_TABLE_DIR / "magok_convenience_brand_by_admin_dong.csv", index=False, encoding="utf-8-sig")

    write_md_table(supply_summary, OUTPUT_TABLE_DIR / "magok_convenience_supply_summary.md")
    write_md_table(magok_admin_out, OUTPUT_TABLE_DIR / "magok_related_convenience_count_by_admin_dong.md")
    write_md_table(zone_summary_out, OUTPUT_TABLE_DIR / "magok_convenience_zone_summary.md")
    write_md_table(brand_by_dong, OUTPUT_TABLE_DIR / "magok_convenience_brand_by_admin_dong.md")

    # Figure 1: 행정동별 편의점 수 상위 비교
    plot_df = admin_counts.sort_values("store_count", ascending=True).copy()
    fig, ax = plt.subplots(figsize=(12, 10))
    colors = plot_df["zone"].map(ZONE_COLORS)
    ax.barh(plot_df["admin_dong"], plot_df["store_count"], color=colors, edgecolor="white")
    ax.axvline(gangseo_avg, color="#111827", linestyle="--", linewidth=1.5, label=f"강서구 행정동 평균 {gangseo_avg:.1f}개")
    for i, (_, row) in enumerate(plot_df.iterrows()):
        ax.text(row["store_count"] + 0.8, i, f"{int(row['store_count'])}개", va="center", fontsize=10)
    ax.set_title("강서구 행정동별 편의점 수: 마곡 관련 행정동은 상위권에 집중", fontsize=18, weight="bold", pad=15)
    ax.set_xlabel("편의점 수(개)")
    ax.set_ylabel("행정동")
    handles = [plt.Rectangle((0, 0), 1, 1, color=color) for color in ZONE_COLORS.values()]
    ax.legend(handles, list(ZONE_COLORS.keys()), loc="lower right")
    fig.tight_layout()
    fig.savefig(OUTPUT_FIG_DIR / "magok_convenience_admin_dong_counts.png", dpi=200)
    plt.close(fig)

    # Figure 2: 위치 분포도
    fig, ax = plt.subplots(figsize=(13, 11))
    other = df[df["zone"] == "기타 강서구"]
    ax.scatter(other["longitude"], other["latitude"], s=22, c="#d1d5db", alpha=0.55, label="기타 강서구")
    for brand in BRAND_ORDER:
        part = magok_related[magok_related["brand"] == brand]
        if not part.empty:
            ax.scatter(
                part["longitude"],
                part["latitude"],
                s=64,
                color=BRAND_COLORS[brand],
                alpha=0.85,
                edgecolor="white",
                linewidth=0.5,
                label=brand,
            )
    centroids = magok_related.groupby("admin_dong")[["longitude", "latitude"]].mean().reindex(MAGOK_RELATED)
    counts = magok_related.groupby("admin_dong").size().reindex(MAGOK_RELATED)
    for dong, row in centroids.dropna().iterrows():
        ax.text(row["longitude"], row["latitude"] + 0.0015, f"{dong}\n{int(counts.loc[dong])}개", ha="center", va="bottom", fontsize=12, weight="bold", color="#111827", bbox=dict(boxstyle="round,pad=0.25", facecolor="white", alpha=0.78, edgecolor="#e5e7eb"))
    ax.set_title("마곡 관련 행정동 편의점 위치 분포", fontsize=18, weight="bold", pad=15)
    ax.set_xlabel("경도")
    ax.set_ylabel("위도")
    ax.grid(True, alpha=0.35)
    ax.legend(title="마곡 관련 편의점 브랜드", loc="upper right", frameon=True)
    ax.set_xlim(df["longitude"].min() - 0.003, df["longitude"].max() + 0.003)
    ax.set_ylim(df["latitude"].min() - 0.003, df["latitude"].max() + 0.003)
    fig.tight_layout()
    fig.savefig(OUTPUT_FIG_DIR / "magok_convenience_location_distribution.png", dpi=220)
    plt.close(fig)

    # Figure 3: 권역 요약
    fig, ax = plt.subplots(figsize=(10, 6))
    zs = zone_summary_out.copy()
    bars = ax.bar(zs["zone"].astype(str), zs["store_count"], color=[ZONE_COLORS[z] for z in zs["zone"].astype(str)])
    for bar, pct in zip(bars, zs["share_of_gangseo_pct"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 4, f"{int(bar.get_height())}개\n({pct:.1f}%)", ha="center", va="bottom", fontsize=12, weight="bold")
    ax.set_title("마곡 관련 권역 편의점 공급 규모", fontsize=17, weight="bold", pad=12)
    ax.set_xlabel("권역")
    ax.set_ylabel("편의점 수(개)")
    ax.set_ylim(0, max(zs["store_count"]) * 1.2)
    fig.tight_layout()
    fig.savefig(OUTPUT_FIG_DIR / "magok_convenience_zone_supply_summary.png", dpi=200)
    plt.close(fig)

    memo = f"""# 마곡 주변 편의점 공급 분석 메모

## 1. 왜 편의점 위치를 확인해야 하는가

기존 분석은 마곡의 수요 측면, 즉 **공항 이동 수요, 이대서울병원 보호자·응급 수요, 마곡산업단지 R&D 근무·방문 수요, 강서구 1인가구 기반**을 검증하는 데 초점을 두었다. 그러나 실제 입지 판단에서는 수요만으로 충분하지 않다. 수요가 발생하는 지역 주변에 이를 받아낼 수 있는 **생활밀착형 공급 거점**이 얼마나 있고, 어디에 몰려 있는지도 함께 확인해야 한다.

편의점은 24시간 또는 장시간 운영 가능성이 높고, 1인가구·직장인·환자 보호자·공항 이동객이 모두 이용할 수 있는 기본 생활 인프라다. 따라서 마곡의 복합 체류 생활권 논리를 보완하려면, 마곡 주변 편의점 수와 위치 분포를 같이 제시하는 것이 타당하다.

## 2. 핵심 수치

| 지표 | 값 | 해석 |
|---|---:|---|
| 강서구 전체 편의점 | {total_gangseo:,}개 | 분석 기준 전체 모수다. |
| 강서구 행정동 평균 | {gangseo_avg:.1f}개 | 행정동별 편의점 수 비교 기준이다. |
| 마곡핵심권 편의점 | {int(zone_summary.loc[zone_summary['zone'] == '마곡핵심권', 'store_count'].iloc[0]):,}개 | 발산1동·가양1동의 공급 규모다. |
| 공항연계권 편의점 | {int(zone_summary.loc[zone_summary['zone'] == '공항연계권', 'store_count'].iloc[0]):,}개 | 공항동·방화1동의 공급 규모다. |
| 마곡 관련 4개 행정동 편의점 | {len(magok_related):,}개 | 강서구 전체의 {len(magok_related) / total_gangseo * 100:.2f}%다. |

마곡 관련 4개 행정동은 기존 수요 분석에서 사용한 생활권 후보 범위인 **발산1동, 가양1동, 공항동, 방화1동**이다. 이 네 행정동의 편의점은 총 **{len(magok_related):,}개**로, 강서구 전체 편의점의 **{len(magok_related) / total_gangseo * 100:.2f}%**를 차지한다. 특히 가양1동은 **{int(counts.loc['가양1동']):,}개**, 공항동은 **{int(counts.loc['공항동']):,}개**, 발산1동은 **{int(counts.loc['발산1동']):,}개**, 방화1동은 **{int(counts.loc['방화1동']):,}개**로 확인된다.

## 3. 발표용 해석

> **마곡의 특수성은 수요 측면에서만 나타나는 것이 아니라, 편의점 공급 분포에서도 확인된다. 강서구 전체 편의점 {total_gangseo:,}개 중 마곡 관련 4개 행정동에 {len(magok_related):,}개가 위치해 전체의 {len(magok_related) / total_gangseo * 100:.2f}%를 차지한다. 이는 공항·병원·R&D 업무지구·1인가구 수요가 발생하는 생활권 주변에 실제 생활밀착형 공급 거점도 함께 형성되어 있음을 보여준다.**

다만 편의점 수가 많다는 사실은 두 가지 의미를 동시에 가진다. 첫째, 수요를 받아낼 수 있는 후보 거점이 많다는 긍정적 의미가 있다. 둘째, 이미 공급이 밀집되어 있어 신규 진입이나 특정 프로그램 설치 시에는 **중복 경쟁, 거리별 공백, 건물 조건**을 추가로 확인해야 한다는 의미도 있다. 따라서 다음 단계에서는 단순 개수 비교를 넘어서, 편의점별 반경 300m 또는 500m 안의 병원·지하철역·주거·업무 수요를 결합해 **어떤 편의점 주변이 공급 공백 또는 프로그램 결합 가능성이 높은지**를 좁히는 분석이 필요하다.

## 4. 생성 파일

| 파일 | 설명 |
|---|---|
| `04_outputs/tables/magok_convenience_supply_summary.md` | 마곡 주변 편의점 공급 핵심 요약표 |
| `04_outputs/tables/magok_related_convenience_count_by_admin_dong.md` | 마곡 관련 행정동별 편의점 수 |
| `04_outputs/tables/magok_convenience_brand_by_admin_dong.md` | 마곡 관련 행정동별 브랜드 분포 |
| `04_outputs/figures/magok_convenience_admin_dong_counts.png` | 강서구 행정동별 편의점 수 비교 차트 |
| `04_outputs/figures/magok_convenience_location_distribution.png` | 마곡 관련 편의점 위치 분포도 |
| `04_outputs/figures/magok_convenience_zone_supply_summary.png` | 마곡핵심권·공항연계권·기타 강서구 권역별 요약 차트 |

## 5. 데이터 기준과 주의점

분석에는 프로젝트에 정리되어 있던 `tableau_convenience_stores_gangseo.csv`를 사용했다. 이 파일은 소상공인 상가업소 서울 원자료에서 강서구 편의점으로 추출된 점포 좌표 데이터이며, 현재 정리본 기준으로 좌표와 행정동이 있는 편의점 **{total_gangseo:,}개**가 분석에 사용되었다. 기존 메모에는 추출 단계의 원자료 기준 수량이 남아 있을 수 있으므로, 본 분석에서는 실제 `curated_project/02_processed_data/store_and_facility/tableau_convenience_stores_gangseo.csv` 파일의 현재 행 수를 기준으로 해석한다.
"""
    (OUTPUT_REPORT_DIR / "magok_convenience_supply_memo.md").write_text(memo, encoding="utf-8")

    print("분석 완료")
    print(f"강서구 전체 편의점: {total_gangseo}")
    print(f"마곡 관련 4개 행정동 편의점: {len(magok_related)}")
    print(magok_admin_out.to_string(index=False))


if __name__ == "__main__":
    main()
