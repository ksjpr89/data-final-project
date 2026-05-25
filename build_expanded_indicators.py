from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, Iterable, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.ticker import FuncFormatter

BASE = Path('/home/ubuntu/data_final_analysis_work')
IN = BASE / 'expanded_inputs'
OUT = BASE / 'outputs' / 'expanded_multi_indicator_analysis_20260522'
FIG = OUT / 'figures'
OUT.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)

plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['font.family'] = 'Noto Sans CJK JP'
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 140

CANDIDATE_CENTROIDS = {
    '가양1동': (37.5688, 126.8404),
    '등촌3동': (37.5584, 126.8494),
    '발산1동': (37.5580, 126.8370),
    '공항동': (37.5627, 126.8107),
    '방화1동': (37.5733, 126.8146),
    '방화2동': (37.5682, 126.8065),
    '방화3동': (37.5781, 126.8133),
    '우장산동': (37.5484, 126.8360),
}

SUBWAY_DONG_MAP = {
    '가양1동': ['가양', '증미', '양천향교', '마곡나루'],
    '등촌3동': ['증미', '등촌'],
    '발산1동': ['발산', '마곡', '마곡나루', '우장산'],
    '공항동': ['공항시장', '송정', '김포공항'],
    '방화1동': ['개화산', '방화', '김포공항'],
    '방화2동': ['개화', '방화', '김포공항'],
    '방화3동': ['방화', '개화산'],
    '우장산동': ['우장산', '발산', '화곡'],
}

MAGOK_BACKING_WEIGHT = {
    '가양1동': 1.00,
    '발산1동': 1.00,
    '등촌3동': 0.35,
    '우장산동': 0.35,
    '공항동': 0.25,
    '방화1동': 0.15,
    '방화2동': 0.10,
    '방화3동': 0.10,
}

AIRPORT_BACKING_WEIGHT = {
    '공항동': 1.00,
    '방화1동': 0.75,
    '방화2동': 0.65,
    '방화3동': 0.45,
    '가양1동': 0.25,
    '발산1동': 0.20,
    '등촌3동': 0.10,
    '우장산동': 0.10,
}

BASE_WEIGHTS = {
    '상권성장': 0.25,
    '편의점경쟁': 0.20,
    '유동인구': 0.20,
    '인구구조': 0.15,
    '배후시설': 0.20,
}

SCENARIOS = {
    'base_balanced': BASE_WEIGHTS,
    'growth_demand_focused': {'상권성장': 0.30, '편의점경쟁': 0.15, '유동인구': 0.25, '인구구조': 0.10, '배후시설': 0.20},
    'competition_risk_focused': {'상권성장': 0.20, '편의점경쟁': 0.30, '유동인구': 0.15, '인구구조': 0.15, '배후시설': 0.20},
    'backing_facility_focused': {'상권성장': 0.20, '편의점경쟁': 0.15, '유동인구': 0.20, '인구구조': 0.15, '배후시설': 0.30},
}


def read_csv_smart(path: Path, **kwargs) -> pd.DataFrame:
    for enc in ['utf-8-sig', 'cp949', 'euc-kr', 'utf-8']:
        try:
            return pd.read_csv(path, encoding=enc, **kwargs)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(path, **kwargs)


def to_num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s.astype(str).str.replace(',', '', regex=False).str.replace('-', '0', regex=False), errors='coerce').fillna(0)


def haversine_km(lat1: float, lon1: float, lat2: pd.Series, lon2: pd.Series) -> pd.Series:
    r = 6371.0088
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = np.radians(lat2.astype(float))
    lon2_rad = np.radians(lon2.astype(float))
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2) ** 2
    return 2 * r * np.arcsin(np.sqrt(a))


def minmax(series: pd.Series, reverse: bool = False) -> pd.Series:
    s = pd.to_numeric(series, errors='coerce').astype(float)
    if s.max() == s.min():
        out = pd.Series(50.0, index=s.index)
    else:
        out = (s - s.min()) / (s.max() - s.min()) * 100
    if reverse:
        out = 100 - out
    return out.fillna(0)


def weighted_average(df: pd.DataFrame, columns: Iterable[str], weights: Iterable[float] | None = None) -> pd.Series:
    cols = list(columns)
    vals = df[cols].astype(float)
    if weights is None:
        return vals.mean(axis=1)
    w = np.array(list(weights), dtype=float)
    w = w / w.sum()
    return vals.mul(w, axis=1).sum(axis=1)


def build_hospital_access(candidates: List[str]) -> pd.DataFrame:
    clinic = read_csv_smart(IN / 'seoul_hospital_clinic_locations_20260508.csv')
    emergency = read_csv_smart(IN / 'seoul_emergency_room_locations_20260508.csv')
    clinic = clinic[clinic['주소'].astype(str).str.contains('강서구', na=False)].copy()
    emergency = emergency[emergency['주소'].astype(str).str.contains('강서구', na=False)].copy()
    for df in [clinic, emergency]:
        df['병원경도'] = pd.to_numeric(df['병원경도'], errors='coerce')
        df['병원위도'] = pd.to_numeric(df['병원위도'], errors='coerce')
        df.dropna(subset=['병원경도', '병원위도'], inplace=True)
    rows = []
    for dong in candidates:
        lat, lon = CANDIDATE_CENTROIDS[dong]
        clinic_dist = haversine_km(lat, lon, clinic['병원위도'], clinic['병원경도'])
        emergency_dist = haversine_km(lat, lon, emergency['병원위도'], emergency['병원경도'])
        rows.append({
            'admin_dong_norm': dong,
            'hospital_clinic_count_gangseo_1km': int((clinic_dist <= 1.0).sum()),
            'hospital_clinic_count_gangseo_2km': int((clinic_dist <= 2.0).sum()),
            'emergency_room_count_gangseo_2km': int((emergency_dist <= 2.0).sum()),
            'nearest_emergency_room_km': float(emergency_dist.min()) if len(emergency_dist) else np.nan,
        })
    return pd.DataFrame(rows)


def build_subway(candidates: List[str]) -> pd.DataFrame:
    subway = read_csv_smart(IN / 'seoul_subway_station_hourly_20260506.csv')
    subway['사용월_num'] = pd.to_numeric(subway['사용월'], errors='coerce')
    latest_month = subway['사용월_num'].max()
    subway = subway[subway['사용월_num'] == latest_month].copy()
    ride_cols = [c for c in subway.columns if '승차인원' in c]
    alight_cols = [c for c in subway.columns if '하차인원' in c]
    for c in ride_cols + alight_cols:
        subway[c] = to_num(subway[c])
    subway['monthly_boarding'] = subway[ride_cols].sum(axis=1)
    subway['monthly_alighting'] = subway[alight_cols].sum(axis=1)
    subway['monthly_total_riders'] = subway['monthly_boarding'] + subway['monthly_alighting']
    subway['am_peak_alighting'] = subway[[c for c in alight_cols if c.startswith(('07시', '08시', '09시'))]].sum(axis=1)
    subway['pm_peak_boarding'] = subway[[c for c in ride_cols if c.startswith(('17시', '18시', '19시'))]].sum(axis=1)
    rows = []
    station_lookup_rows = []
    for dong in candidates:
        stations = SUBWAY_DONG_MAP[dong]
        sub = subway[subway['지하철역'].astype(str).isin(stations)].copy()
        # 일부 노선 데이터에서 괄호 표기가 있을 경우를 대비한 보조 매칭
        if sub.empty:
            pattern = '|'.join(stations)
            sub = subway[subway['지하철역'].astype(str).str.contains(pattern, na=False)].copy()
        rows.append({
            'admin_dong_norm': dong,
            'mapped_station_names': ', '.join(stations),
            'subway_reference_month': int(latest_month),
            'subway_station_line_rows': int(len(sub)),
            'subway_monthly_boarding': float(sub['monthly_boarding'].sum()),
            'subway_monthly_alighting': float(sub['monthly_alighting'].sum()),
            'subway_monthly_total_riders': float(sub['monthly_total_riders'].sum()),
            'subway_am_peak_alighting': float(sub['am_peak_alighting'].sum()),
            'subway_pm_peak_boarding': float(sub['pm_peak_boarding'].sum()),
        })
        for _, r in sub[['호선명', '지하철역', 'monthly_total_riders']].iterrows():
            station_lookup_rows.append({'admin_dong_norm': dong, '호선명': r['호선명'], '지하철역': r['지하철역'], 'monthly_total_riders': r['monthly_total_riders']})
    pd.DataFrame(station_lookup_rows).to_csv(OUT / 'subway_station_mapping_used.csv', index=False, encoding='utf-8-sig')
    return pd.DataFrame(rows)


def build_magok(candidates: List[str]) -> pd.DataFrame:
    magok = pd.read_excel(IN / 'magok_tenant_companies_20260213.xlsx', sheet_name='현행화')
    magok = magok.dropna(subset=['기업명']).copy()
    total = len(magok)
    large = int(magok['기업규모'].astype(str).str.contains('대', na=False).sum())
    industries = int(magok['업종'].nunique(dropna=True))
    fields = int(magok['분야'].nunique(dropna=True))
    large_ratio = large / total if total else 0
    rows = []
    for dong in candidates:
        weight = MAGOK_BACKING_WEIGHT.get(dong, 0)
        rows.append({
            'admin_dong_norm': dong,
            'magok_backing_weight': weight,
            'magok_tenant_company_total': total,
            'magok_large_company_count': large,
            'magok_large_company_ratio': large_ratio,
            'magok_industry_diversity_count': industries,
            'magok_field_diversity_count': fields,
            'magok_backing_company_equivalent': total * weight,
        })
    magok[['기업명', '업종', '분야', '기업규모', '주소']].to_csv(OUT / 'magok_tenant_company_reference.csv', index=False, encoding='utf-8-sig')
    return pd.DataFrame(rows)


def build_airport(candidates: List[str]) -> pd.DataFrame:
    airport = read_csv_smart(IN / 'kac_airport_transport_statistics_20250915.csv')
    for c in ['도착운항기수', '출발운항기수', '도착여객수', '출발여객수']:
        airport[c] = to_num(airport[c])
    gimpo = airport[airport['공항'].astype(str).str.contains('김포', na=False)].copy()
    if gimpo.empty:
        gimpo = airport.copy()
    gimpo['total_passengers'] = gimpo['도착여객수'] + gimpo['출발여객수']
    gimpo['total_flights'] = gimpo['도착운항기수'] + gimpo['출발운항기수']
    latest_year = int(pd.to_numeric(gimpo['연도'], errors='coerce').max())
    latest = gimpo[pd.to_numeric(gimpo['연도'], errors='coerce') == latest_year]
    weekly_passengers = float(latest['total_passengers'].sum())
    weekly_flights = float(latest['total_flights'].sum())
    annualized_passengers = weekly_passengers * 52
    airport.groupby(['연도', '공항', '노선'], dropna=False)[['도착여객수', '출발여객수']].sum().reset_index().to_csv(OUT / 'airport_statistics_reference_summary.csv', index=False, encoding='utf-8-sig')
    rows = []
    for dong in candidates:
        weight = AIRPORT_BACKING_WEIGHT.get(dong, 0)
        rows.append({
            'admin_dong_norm': dong,
            'airport_backing_weight': weight,
            'gimpo_reference_year': latest_year,
            'gimpo_weekly_passenger_proxy': weekly_passengers,
            'gimpo_weekly_flight_proxy': weekly_flights,
            'gimpo_annualized_passenger_proxy': annualized_passengers,
            'airport_backing_passenger_equivalent': annualized_passengers * weight,
        })
    return pd.DataFrame(rows)


def build_business(candidates: List[str]) -> pd.DataFrame:
    path = IN / 'gangseo_business_report_2023_based_20250731.xlsx'
    df = pd.read_excel(path, sheet_name='2.산업세세분류별 동별 현황', header=None)
    header_row = 1
    total_row_candidates = df.index[df[1].astype(str).str.strip().eq('전 산업')].tolist()
    if not total_row_candidates:
        total_row_candidates = df.index[df[2].astype(str).str.strip().eq('Total')].tolist()
    total_row = total_row_candidates[0]
    rows = []
    for dong in candidates:
        cols = [c for c in df.columns if str(df.iloc[header_row, c]).strip() == dong]
        if not cols:
            rows.append({'admin_dong_norm': dong, 'business_establishments_2023': np.nan, 'business_workers_2023': np.nan})
            continue
        est_col = cols[0]
        worker_col = est_col + 1
        rows.append({
            'admin_dong_norm': dong,
            'business_establishments_2023': float(to_num(pd.Series([df.iloc[total_row, est_col]])).iloc[0]),
            'business_workers_2023': float(to_num(pd.Series([df.iloc[total_row, worker_col]])).iloc[0]),
        })
    business_ref = []
    for dong in candidates:
        cols = [c for c in df.columns if str(df.iloc[header_row, c]).strip() == dong]
        if cols:
            est_col = cols[0]
            worker_col = est_col + 1
            for idx in range(total_row, min(total_row + 25, len(df))):
                business_ref.append({
                    'admin_dong_norm': dong,
                    'industry_code': df.iloc[idx, 0],
                    'industry_name_ko': df.iloc[idx, 1],
                    'industry_name_en': df.iloc[idx, 2],
                    'establishments': to_num(pd.Series([df.iloc[idx, est_col]])).iloc[0],
                    'workers': to_num(pd.Series([df.iloc[idx, worker_col]])).iloc[0],
                })
    pd.DataFrame(business_ref).to_csv(OUT / 'business_industry_reference_major_rows.csv', index=False, encoding='utf-8-sig')
    return pd.DataFrame(rows)


def build_score_components(prelim: pd.DataFrame, expanded: pd.DataFrame) -> pd.DataFrame:
    df = prelim.merge(expanded, on='admin_dong_norm', how='left')
    # 하위 원천 지표 정규화
    df['store_growth_norm'] = minmax(df['total_store_change_pct'])
    df['population_change_norm'] = minmax(df['population_change_pct'])
    df['young_adult_share_norm'] = minmax(df['share_20_39_last'])
    df['senior_share_risk_reversed_norm'] = minmax(df['share_60_plus_last'], reverse=True)
    df['convenience_density_reversed_norm'] = minmax(df['convenience_per_1000_last'], reverse=True)
    df['convenience_growth_reversed_norm'] = minmax(df['convenience_change_pct'], reverse=True)
    df['inbound_movement_norm'] = minmax(df['avg_daily_inbound_movement_20260328_31'])
    df['subway_total_norm'] = minmax(df['subway_monthly_total_riders'])
    df['hospital_access_norm'] = minmax(df['hospital_clinic_count_gangseo_1km'])
    df['emergency_access_norm'] = minmax(df['nearest_emergency_room_km'], reverse=True)
    df['business_worker_norm'] = minmax(df['business_workers_2023'])
    df['magok_backing_norm'] = minmax(df['magok_backing_company_equivalent'])
    df['airport_backing_norm'] = minmax(df['airport_backing_passenger_equivalent'])

    # 5개 발표용 구성 점수
    df['상권성장'] = weighted_average(df, ['store_growth_norm', 'population_change_norm'], [0.75, 0.25])
    df['편의점경쟁'] = weighted_average(df, ['convenience_density_reversed_norm', 'convenience_growth_reversed_norm'], [0.70, 0.30])
    df['유동인구'] = weighted_average(df, ['inbound_movement_norm', 'subway_total_norm'], [0.60, 0.40])
    df['인구구조'] = weighted_average(df, ['young_adult_share_norm', 'senior_share_risk_reversed_norm', 'population_change_norm'], [0.50, 0.30, 0.20])
    df['배후시설'] = weighted_average(df, ['hospital_access_norm', 'emergency_access_norm', 'business_worker_norm', 'magok_backing_norm', 'airport_backing_norm'], [0.20, 0.10, 0.30, 0.25, 0.15])

    for scenario, weights in SCENARIOS.items():
        df[f'score_{scenario}'] = sum(df[k] * v for k, v in weights.items())
        df[f'rank_{scenario}'] = df[f'score_{scenario}'].rank(method='min', ascending=False).astype(int)

    df['final_score'] = df['score_base_balanced']
    df['final_rank'] = df['rank_base_balanced']
    df.sort_values(['final_rank', 'final_score'], ascending=[True, False], inplace=True)
    return df


def build_visualizations(score_df: pd.DataFrame, store_year: pd.DataFrame) -> None:
    palette = sns.color_palette('viridis', n_colors=len(score_df))
    rank_df = score_df.sort_values('final_score', ascending=True)

    plt.figure(figsize=(10, 6))
    bars = plt.barh(rank_df['admin_dong_norm'], rank_df['final_score'], color=palette)
    plt.xlabel('종합 점수(0~100)')
    plt.title('강서구 편의점 후보지 최종 종합 점수')
    for bar, val in zip(bars, rank_df['final_score']):
        plt.text(val + 1, bar.get_y() + bar.get_height()/2, f'{val:.1f}', va='center', fontsize=9)
    plt.xlim(0, max(100, rank_df['final_score'].max() + 10))
    plt.tight_layout()
    plt.savefig(FIG / 'final_ranking_bar_chart.png', bbox_inches='tight')
    plt.close()

    component_cols = ['상권성장', '편의점경쟁', '유동인구', '인구구조', '배후시설']
    heat = score_df.sort_values('final_score', ascending=False).set_index('admin_dong_norm')[component_cols]
    plt.figure(figsize=(9, 5.5))
    sns.heatmap(heat, annot=True, fmt='.1f', cmap='YlGnBu', linewidths=.5, cbar_kws={'label': '정규화 점수'})
    plt.title('후보지별 5대 평가축 히트맵')
    plt.xlabel('평가축')
    plt.ylabel('후보 행정동')
    plt.tight_layout()
    plt.savefig(FIG / 'score_component_heatmap.png', bbox_inches='tight')
    plt.close()

    plt.figure(figsize=(8.5, 6))
    scatter = plt.scatter(score_df['convenience_per_1000_last'], score_df['avg_daily_inbound_movement_20260328_31'],
                          s=score_df['subway_monthly_total_riders'] / max(score_df['subway_monthly_total_riders'].max(), 1) * 900 + 120,
                          c=score_df['final_score'], cmap='viridis', alpha=.82, edgecolor='black', linewidth=.6)
    for _, r in score_df.iterrows():
        plt.annotate(r['admin_dong_norm'], (r['convenience_per_1000_last'], r['avg_daily_inbound_movement_20260328_31']),
                     xytext=(5, 5), textcoords='offset points', fontsize=9)
    plt.colorbar(scatter, label='종합 점수')
    plt.xlabel('인구 1천 명당 편의점 수(낮을수록 경쟁 부담 완화)')
    plt.ylabel('평균 일 유입 생활이동 인구')
    plt.title('편의점 경쟁 밀도와 유입 수요의 균형')
    plt.gca().yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f'{int(x):,}'))
    plt.tight_layout()
    plt.savefig(FIG / 'convenience_density_vs_inbound_scatter.png', bbox_inches='tight')
    plt.close()

    store_pivot = store_year.groupby(['source_year', 'admin_dong_norm'], as_index=False)['avg_store_count'].sum()
    top_candidates = score_df.sort_values('final_score', ascending=False)['admin_dong_norm'].tolist()
    plt.figure(figsize=(10, 6))
    for dong in top_candidates:
        sub = store_pivot[store_pivot['admin_dong_norm'] == dong].sort_values('source_year')
        plt.plot(sub['source_year'], sub['avg_store_count'], marker='o', linewidth=2, label=dong)
    plt.xlabel('연도')
    plt.ylabel('전체 상가 평균 점포 수')
    plt.title('후보지별 상권 규모 변화 추이(2019~2025)')
    plt.legend(ncol=3, fontsize=8)
    plt.tight_layout()
    plt.savefig(FIG / 'store_growth_trend_2019_2025.png', bbox_inches='tight')
    plt.close()

    # 레이더 차트는 최종 상위 5개 후보를 표시한다.
    radar_df = score_df.sort_values('final_score', ascending=False).head(5)
    labels = component_cols
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    angles += angles[:1]
    fig = plt.figure(figsize=(8.2, 8.2))
    ax = plt.subplot(111, polar=True)
    for _, row in radar_df.iterrows():
        values = [row[c] for c in labels]
        values += values[:1]
        ax.plot(angles, values, linewidth=2, label=row['admin_dong_norm'])
        ax.fill(angles, values, alpha=0.08)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_title('상위 후보지 5대 평가축 레이더 차트', y=1.08)
    ax.legend(loc='upper right', bbox_to_anchor=(1.25, 1.08), fontsize=9)
    plt.tight_layout()
    plt.savefig(FIG / 'top_candidate_radar_chart.png', bbox_inches='tight')
    plt.close()


def write_methodology(score_df: pd.DataFrame) -> None:
    top = score_df.sort_values('final_score', ascending=False).iloc[0]
    md = f'''# 확장 다중지표 분석 방법론 메모

본 산출물은 강서구 내 편의점 신규 입지 후보 행정동을 비교하기 위해 기존 상권·인구·생활이동 지표에 병의원 접근성, 지하철 승하차 수요, 마곡 업무 배후수요, 김포공항 배후수요, 강서구 사업체·종사자 규모를 결합한 확장 분석 결과이다.

## 평가축과 가중치

| 평가축 | 기본 가중치 | 주요 원천 지표 | 해석 방향 |
|---|---:|---|---|
| 상권성장 | 25% | 전체 점포 변화율, 인구 변화율 | 높을수록 성장성이 크다. |
| 편의점경쟁 | 20% | 인구 1천 명당 편의점 수, 편의점 증가율 | 낮은 경쟁 밀도와 낮은 경쟁 증가율을 높게 평가한다. |
| 유동인구 | 20% | 생활이동 유입, 인근 지하철 월 승하차 | 높을수록 잠재 구매 접점이 많다. |
| 인구구조 | 15% | 20~39세 비중, 60세 이상 비중, 인구 변화율 | 젊은 소비층과 인구 안정성을 높게 평가한다. |
| 배후시설 | 20% | 병의원 접근성, 응급실 접근성, 사업체 종사자, 마곡 입주기업, 공항 여객 프록시 | 업무·의료·교통 배후수요가 클수록 높다. |

## 최종 결과 요약

기본 균형 가중치 기준 최종 1순위는 **{top['admin_dong_norm']}**이며, 종합 점수는 **{top['final_score']:.1f}점**이다. 민감도 분석은 성장·유동 수요 중시, 경쟁 리스크 중시, 배후시설 중시의 세 가지 대안 가중치로 수행했다. 시나리오별 순위 변동은 `sensitivity_analysis.csv`에 정리되어 있다.

## 해석상 주의사항

마곡은 별도 행정동으로 관리되지 않는 자료가 있어, 본 분석에서는 마곡 업무지구의 배후수요를 **가양1동과 발산1동 중심의 권역 가중치**로 반영했다. 병원 접근성은 후보 행정동 대표 중심점에서 반경 1km 및 2km 내 시설 수를 계산한 근사치이며, 지하철 접근성은 후보지 인근 역명을 사전에 매핑하여 월 승하차 합계를 산출했다. 김포공항 통계는 원자료의 최신 연도·요일별 여객 자료를 주간 프록시로 합산하고 52주 환산값으로 후보지별 공항 배후수요 지표를 만들었다.
'''
    (OUT / 'expanded_analysis_methodology_notes.md').write_text(md, encoding='utf-8')


def main() -> None:
    prelim = read_csv_smart(IN / 'candidate_preliminary_ranking_summary.csv')
    candidates = prelim['admin_dong_norm'].tolist()
    missing_centroids = [c for c in candidates if c not in CANDIDATE_CENTROIDS]
    if missing_centroids:
        raise ValueError(f'대표 좌표가 정의되지 않은 후보지가 있습니다: {missing_centroids}')

    hospital = build_hospital_access(candidates)
    subway = build_subway(candidates)
    magok = build_magok(candidates)
    airport = build_airport(candidates)
    business = build_business(candidates)

    expanded = hospital.merge(subway, on='admin_dong_norm', how='left') \
        .merge(magok, on='admin_dong_norm', how='left') \
        .merge(airport, on='admin_dong_norm', how='left') \
        .merge(business, on='admin_dong_norm', how='left')
    expanded.to_csv(OUT / 'candidate_expanded_indicators.csv', index=False, encoding='utf-8-sig')

    score_df = build_score_components(prelim, expanded)
    component_cols = ['admin_dong_norm', '상권성장', '편의점경쟁', '유동인구', '인구구조', '배후시설', 'final_score', 'final_rank']
    score_df[component_cols].sort_values('final_rank').to_csv(OUT / 'candidate_score_components.csv', index=False, encoding='utf-8-sig')
    final_cols = ['final_rank', 'admin_dong_norm', 'final_score', 'total_store_change_pct', 'convenience_per_1000_last',
                  'avg_daily_inbound_movement_20260328_31', 'subway_monthly_total_riders', 'business_workers_2023',
                  'hospital_clinic_count_gangseo_1km', 'magok_backing_company_equivalent', 'airport_backing_passenger_equivalent']
    score_df[final_cols].sort_values('final_rank').to_csv(OUT / 'candidate_final_ranking.csv', index=False, encoding='utf-8-sig')

    sens_cols = ['admin_dong_norm']
    for scenario in SCENARIOS:
        sens_cols += [f'score_{scenario}', f'rank_{scenario}']
    score_df[sens_cols].sort_values('rank_base_balanced').to_csv(OUT / 'sensitivity_analysis.csv', index=False, encoding='utf-8-sig')

    store_year = read_csv_smart(IN / 'candidate_store_industry_by_year.csv')
    store_year['source_year'] = pd.to_numeric(store_year['source_year'], errors='coerce').astype('Int64')
    store_year['avg_store_count'] = pd.to_numeric(store_year['avg_store_count'], errors='coerce')
    build_visualizations(score_df, store_year)
    write_methodology(score_df)

    with pd.ExcelWriter(OUT / 'expanded_multi_indicator_analysis_tables.xlsx', engine='openpyxl') as writer:
        expanded.to_excel(writer, sheet_name='expanded_indicators', index=False)
        score_df.sort_values('final_rank').to_excel(writer, sheet_name='scoring_full', index=False)
        score_df[component_cols].sort_values('final_rank').to_excel(writer, sheet_name='score_components', index=False)
        score_df[sens_cols].sort_values('rank_base_balanced').to_excel(writer, sheet_name='sensitivity', index=False)

    summary = {
        'output_dir': str(OUT),
        'candidate_count': len(candidates),
        'top_candidate': score_df.sort_values('final_score', ascending=False).iloc[0]['admin_dong_norm'],
        'top_score': float(score_df.sort_values('final_score', ascending=False).iloc[0]['final_score']),
        'figure_count': len(list(FIG.glob('*.png'))),
    }
    pd.Series(summary).to_json(OUT / 'expanded_analysis_run_summary.json', force_ascii=False, indent=2)
    print(summary)


if __name__ == '__main__':
    main()
