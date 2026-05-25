from __future__ import annotations

import zipfile
from pathlib import Path
import re

import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
RAW_ZIP = ROOT / "curated_project/01_raw_data/living_population/LOCAL_PEOPLE_DONG_202603.zip"
MOVEMENT_CSV = ROOT / "outputs/candidate_living_movement_avg_daily_direction.csv"
OUT_TABLE = ROOT / "curated_project/04_outputs/tables"
OUT_FIG = ROOT / "curated_project/04_outputs/figures"
OUT_REPORT = ROOT / "curated_project/04_outputs/reports"
for p in [OUT_TABLE, OUT_FIG, OUT_REPORT]:
    p.mkdir(parents=True, exist_ok=True)

FONT_CANDIDATES = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
]
plt.style.use("seaborn-v0_8-whitegrid")
for font_path in FONT_CANDIDATES:
    if Path(font_path).exists():
        mpl.font_manager.fontManager.addfont(font_path)
        mpl.rcParams["font.family"] = mpl.font_manager.FontProperties(fname=font_path).get_name()
        break
mpl.rcParams["axes.unicode_minus"] = False

# 기존 분석에서 사용한 마곡 관련 4개 행정동 기준을 유지한다.
MAGOK_CORE = {
    11500603: "가양1동",
    11500611: "발산1동",
    11500620: "공항동",
    11500630: "방화1동",
}
GANGSEO_PREFIX = "11500"

AGE_BANDS = [
    ("0-19세", ["0세부터9세", "10세부터14세", "15세부터19세"]),
    ("20대", ["20세부터24세", "25세부터29세"]),
    ("30대", ["30세부터34세", "35세부터39세"]),
    ("40대", ["40세부터44세", "45세부터49세"]),
    ("50대", ["50세부터54세", "55세부터59세"]),
    ("60대", ["60세부터64세", "65세부터69세"]),
    ("70세 이상", ["70세이상"]),
]


def read_population() -> pd.DataFrame:
    with zipfile.ZipFile(RAW_ZIP) as zf:
        name = zf.namelist()[0]
        with zf.open(name) as f:
            df = pd.read_csv(f, encoding="utf-8-sig", index_col=False)
    df["행정동코드"] = df["행정동코드"].astype(int)
    df["기준일"] = pd.to_datetime(df["기준일ID"].astype(str), format="%Y%m%d")
    df["요일"] = df["기준일"].dt.day_name()
    df["요일구분"] = np.where(df["기준일"].dt.weekday < 5, "평일", "주말")
    df["권역"] = np.where(df["행정동코드"].isin(MAGOK_CORE), "마곡권 4개 행정동", "기타")
    df["행정동명"] = df["행정동코드"].map(MAGOK_CORE)
    df["시간대구분"] = df["시간대구분"].astype(int)
    return df


def age_columns(df: pd.DataFrame) -> dict[str, list[str]]:
    mapping: dict[str, list[str]] = {}
    for band, pieces in AGE_BANDS:
        cols = []
        for c in df.columns:
            if c.endswith("생활인구수") and any(piece in c for piece in pieces):
                cols.append(c)
        mapping[band] = cols
    return mapping


def fmt_int(x: float) -> str:
    return f"{x:,.0f}"


def save_markdown_table(df: pd.DataFrame, path: Path) -> None:
    path.write_text(df.to_markdown(index=False) + "\n", encoding="utf-8")


def analyze() -> dict[str, float]:
    df = read_population()
    target = df[df["행정동코드"].isin(MAGOK_CORE)].copy()
    seoul_admin_count = df["행정동코드"].nunique()
    target_admin_count = len(MAGOK_CORE)

    # 시간대별 평일/주말: 일자별 시간대 총량을 먼저 만든 뒤 평균을 내야 월 누적합으로 부풀지 않는다.
    target_daily_hour = (
        target.groupby(["기준일", "요일구분", "시간대구분"], as_index=False)["총생활인구수"].sum()
        .rename(columns={"총생활인구수": "마곡권_4개동_총생활인구"})
    )
    target_hour = target_daily_hour.groupby(["요일구분", "시간대구분"], as_index=False)["마곡권_4개동_총생활인구"].mean()
    target_hour["마곡권_행정동당_생활인구"] = target_hour["마곡권_4개동_총생활인구"] / target_admin_count
    seoul_daily_hour = (
        df.groupby(["기준일", "요일구분", "시간대구분"], as_index=False)["총생활인구수"].sum()
        .rename(columns={"총생활인구수": "서울_총생활인구"})
    )
    seoul_hour = seoul_daily_hour.groupby(["요일구분", "시간대구분"], as_index=False)["서울_총생활인구"].mean()
    seoul_hour["서울_행정동당_생활인구"] = seoul_hour["서울_총생활인구"] / seoul_admin_count
    hour = target_hour.merge(seoul_hour, on=["요일구분", "시간대구분"])
    hour["마곡권_vs_서울평균_배율"] = hour["마곡권_행정동당_생활인구"] / hour["서울_행정동당_생활인구"]
    hour.to_csv(OUT_TABLE / "magok_living_population_hourly_weekday_weekend.csv", index=False, encoding="utf-8-sig")

    hour_md = hour.copy()
    for col in ["마곡권_4개동_총생활인구", "마곡권_행정동당_생활인구", "서울_총생활인구", "서울_행정동당_생활인구"]:
        hour_md[col] = hour_md[col].map(fmt_int)
    hour_md["마곡권_vs_서울평균_배율"] = hour_md["마곡권_vs_서울평균_배율"].map(lambda x: f"{x:.2f}배")
    save_markdown_table(hour_md, OUT_TABLE / "magok_living_population_hourly_weekday_weekend.md")

    # 피크·저점 요약
    summary_rows = []
    for day_type, sub in hour.groupby("요일구분"):
        peak = sub.loc[sub["마곡권_4개동_총생활인구"].idxmax()]
        trough = sub.loc[sub["마곡권_4개동_총생활인구"].idxmin()]
        daytime = sub[sub["시간대구분"].between(9, 18)]["마곡권_4개동_총생활인구"].mean()
        nighttime = pd.concat([sub[sub["시간대구분"].between(19, 23)], sub[sub["시간대구분"].between(0, 8)]])["마곡권_4개동_총생활인구"].mean()
        summary_rows.append({
            "요일구분": day_type,
            "피크시간": int(peak["시간대구분"]),
            "피크_마곡권_생활인구": peak["마곡권_4개동_총생활인구"],
            "최저시간": int(trough["시간대구분"]),
            "최저_마곡권_생활인구": trough["마곡권_4개동_총생활인구"],
            "주간_9_18시_평균": daytime,
            "야간_19_08시_평균": nighttime,
            "주간_야간_배율": daytime / nighttime,
        })
    peak_summary = pd.DataFrame(summary_rows)
    peak_summary.to_csv(OUT_TABLE / "magok_living_population_peak_summary.csv", index=False, encoding="utf-8-sig")
    peak_md = peak_summary.copy()
    for col in ["피크_마곡권_생활인구", "최저_마곡권_생활인구", "주간_9_18시_평균", "야간_19_08시_평균"]:
        peak_md[col] = peak_md[col].map(fmt_int)
    peak_md["주간_야간_배율"] = peak_md["주간_야간_배율"].map(lambda x: f"{x:.2f}배")
    save_markdown_table(peak_md, OUT_TABLE / "magok_living_population_peak_summary.md")

    # 행정동별 총 생활인구 평균
    dong_summary = (
        target.groupby(["행정동코드", "행정동명", "요일구분"], as_index=False)["총생활인구수"].mean()
        .rename(columns={"총생활인구수": "시간당_평균_생활인구"})
    )
    dong_summary.to_csv(OUT_TABLE / "magok_living_population_by_admin_dong.csv", index=False, encoding="utf-8-sig")
    dong_md = dong_summary.copy()
    dong_md["시간당_평균_생활인구"] = dong_md["시간당_평균_생활인구"].map(fmt_int)
    save_markdown_table(dong_md, OUT_TABLE / "magok_living_population_by_admin_dong.md")

    # 성·연령 구성: 야간과 주간을 구분해 '사는 사람'과 '머무는 사람' 해석에 활용한다.
    age_map = age_columns(target)
    part_frames = []
    for period_name, mask in {
        "주간(09-18시)": target["시간대구분"].between(9, 18),
        "야간(19-08시)": target["시간대구분"].between(19, 23) | target["시간대구분"].between(0, 8),
        "전체": pd.Series(True, index=target.index),
    }.items():
        sub = target[mask]
        total = sub["총생활인구수"].sum()
        for band, cols in age_map.items():
            val = sub[cols].sum().sum()
            part_frames.append({"시간범위": period_name, "연령대": band, "생활인구": val, "비중": val / total})
    age_summary = pd.DataFrame(part_frames)
    age_summary.to_csv(OUT_TABLE / "magok_living_population_age_structure.csv", index=False, encoding="utf-8-sig")
    age_md = age_summary.copy()
    age_md["생활인구"] = age_md["생활인구"].map(fmt_int)
    age_md["비중"] = age_md["비중"].map(lambda x: f"{x*100:.1f}%")
    save_markdown_table(age_md, OUT_TABLE / "magok_living_population_age_structure.md")

    gender_cols = {
        "남성": [c for c in target.columns if c.startswith("남자") and c.endswith("생활인구수")],
        "여성": [c for c in target.columns if c.startswith("여자") and c.endswith("생활인구수")],
    }
    gender_rows = []
    for period_name, mask in {
        "주간(09-18시)": target["시간대구분"].between(9, 18),
        "야간(19-08시)": target["시간대구분"].between(19, 23) | target["시간대구분"].between(0, 8),
        "전체": pd.Series(True, index=target.index),
    }.items():
        sub = target[mask]
        total = sub["총생활인구수"].sum()
        for gender, cols in gender_cols.items():
            val = sub[cols].sum().sum()
            gender_rows.append({"시간범위": period_name, "성별": gender, "생활인구": val, "비중": val / total})
    gender_summary = pd.DataFrame(gender_rows)
    gender_summary.to_csv(OUT_TABLE / "magok_living_population_gender_structure.csv", index=False, encoding="utf-8-sig")
    gender_md = gender_summary.copy()
    gender_md["생활인구"] = gender_md["생활인구"].map(fmt_int)
    gender_md["비중"] = gender_md["비중"].map(lambda x: f"{x*100:.1f}%")
    save_markdown_table(gender_md, OUT_TABLE / "magok_living_population_gender_structure.md")

    # 생활이동 후보 요약: 유입/유출/내부 이동 방향
    movement = pd.read_csv(MOVEMENT_CSV, encoding="utf-8-sig")
    movement_core = movement[movement["candidate_dong"].isin(MAGOK_CORE.values())].copy()
    movement_summary = movement_core.groupby("direction", as_index=False)["movement_population"].sum()
    direction_label = {
        "inbound_to_candidate": "마곡권으로 유입",
        "outbound_from_candidate": "마곡권에서 유출",
        "candidate_internal_or_between": "마곡권 내부·상호 이동",
    }
    movement_summary["방향"] = movement_summary["direction"].map(direction_label)
    movement_summary = movement_summary[["방향", "movement_population"]]
    movement_summary["비중"] = movement_summary["movement_population"] / movement_summary["movement_population"].sum()
    movement_summary.to_csv(OUT_TABLE / "magok_living_movement_direction_summary.csv", index=False, encoding="utf-8-sig")
    movement_md = movement_summary.copy()
    movement_md["movement_population"] = movement_md["movement_population"].map(fmt_int)
    movement_md["비중"] = movement_md["비중"].map(lambda x: f"{x*100:.1f}%")
    movement_md = movement_md.rename(columns={"movement_population": "평균_이동인구"})
    save_markdown_table(movement_md, OUT_TABLE / "magok_living_movement_direction_summary.md")

    movement_dong = movement_core.pivot_table(index="candidate_dong", columns="direction", values="movement_population", aggfunc="sum").reset_index()
    movement_dong["순유입"] = movement_dong.get("inbound_to_candidate", 0) - movement_dong.get("outbound_from_candidate", 0)
    movement_dong.to_csv(OUT_TABLE / "magok_living_movement_by_admin_dong.csv", index=False, encoding="utf-8-sig")
    movement_dong_md = movement_dong.rename(columns={
        "candidate_dong": "행정동",
        "candidate_internal_or_between": "내부·상호 이동",
        "inbound_to_candidate": "유입",
        "outbound_from_candidate": "유출",
    }).copy()
    for col in [c for c in movement_dong_md.columns if c != "행정동"]:
        movement_dong_md[col] = movement_dong_md[col].map(fmt_int)
    save_markdown_table(movement_dong_md, OUT_TABLE / "magok_living_movement_by_admin_dong.md")

    make_figures(hour, dong_summary, age_summary, movement_summary)

    metrics = {
        "weekday_peak_hour": int(peak_summary.loc[peak_summary["요일구분"] == "평일", "피크시간"].iloc[0]),
        "weekday_peak_pop": float(peak_summary.loc[peak_summary["요일구분"] == "평일", "피크_마곡권_생활인구"].iloc[0]),
        "weekend_peak_hour": int(peak_summary.loc[peak_summary["요일구분"] == "주말", "피크시간"].iloc[0]),
        "weekend_peak_pop": float(peak_summary.loc[peak_summary["요일구분"] == "주말", "피크_마곡권_생활인구"].iloc[0]),
        "weekday_day_night_ratio": float(peak_summary.loc[peak_summary["요일구분"] == "평일", "주간_야간_배율"].iloc[0]),
        "weekend_day_night_ratio": float(peak_summary.loc[peak_summary["요일구분"] == "주말", "주간_야간_배율"].iloc[0]),
        "movement_inbound": float(movement_summary.loc[movement_summary["방향"] == "마곡권으로 유입", "movement_population"].iloc[0]),
        "movement_outbound": float(movement_summary.loc[movement_summary["방향"] == "마곡권에서 유출", "movement_population"].iloc[0]),
    }
    return metrics


def make_figures(hour: pd.DataFrame, dong_summary: pd.DataFrame, age_summary: pd.DataFrame, movement_summary: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(11, 6))
    for day_type, color in [("평일", "#1f77b4"), ("주말", "#ff7f0e")]:
        sub = hour[hour["요일구분"] == day_type]
        ax.plot(sub["시간대구분"], sub["마곡권_4개동_총생활인구"], marker="o", label=f"마곡권 {day_type}", color=color)
    ax.set_title("마곡권 생활인구 시간대별 변화: 평일과 주말 비교", fontsize=16, weight="bold")
    ax.set_xlabel("시간대")
    ax.set_ylabel("마곡권 4개 행정동 총생활인구")
    ax.set_xticks(range(0, 24))
    ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter("{x:,.0f}"))
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT_FIG / "magok_living_population_hourly_weekday_weekend.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 6))
    pivot = dong_summary.pivot(index="행정동명", columns="요일구분", values="시간당_평균_생활인구").loc[list(MAGOK_CORE.values())]
    pivot.plot(kind="bar", ax=ax, color=["#4C78A8", "#F58518"])
    ax.set_title("마곡 관련 행정동별 시간당 평균 생활인구", fontsize=16, weight="bold")
    ax.set_xlabel("")
    ax.set_ylabel("시간당 평균 생활인구")
    ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter("{x:,.0f}"))
    ax.legend(title="요일구분")
    for container in ax.containers:
        ax.bar_label(container, fmt="%.0f", padding=3, fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT_FIG / "magok_living_population_by_admin_dong.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 6))
    age_plot = age_summary[age_summary["시간범위"].isin(["주간(09-18시)", "야간(19-08시)"])].copy()
    age_pivot = age_plot.pivot(index="연령대", columns="시간범위", values="비중").loc[[x[0] for x in AGE_BANDS]] * 100
    age_pivot.plot(kind="bar", ax=ax, color=["#59A14F", "#E15759"])
    ax.set_title("마곡권 생활인구 연령 구성: 주간과 야간 비교", fontsize=16, weight="bold")
    ax.set_xlabel("")
    ax.set_ylabel("비중(%)")
    ax.legend(title="시간범위")
    for container in ax.containers:
        ax.bar_label(container, fmt="%.1f", padding=2, fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT_FIG / "magok_living_population_age_structure.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 5.5))
    move_plot = movement_summary.copy()
    bars = ax.bar(move_plot["방향"], move_plot["movement_population"], color=["#4C78A8", "#72B7B2", "#F58518"])
    ax.set_title("마곡권 생활이동 방향 요약", fontsize=16, weight="bold")
    ax.set_ylabel("평균 이동인구")
    ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter("{x:,.0f}"))
    for bar in bars:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(), f"{bar.get_height():,.0f}", ha="center", va="bottom", fontsize=10)
    fig.tight_layout()
    fig.savefig(OUT_FIG / "magok_living_movement_direction_summary.png", dpi=180)
    plt.close(fig)


if __name__ == "__main__":
    metrics = analyze()
    for k, v in metrics.items():
        if isinstance(v, float):
            print(f"{k}: {v:,.2f}")
        else:
            print(f"{k}: {v}")
