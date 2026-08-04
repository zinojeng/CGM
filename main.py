import streamlit as st
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
from matplotlib import rcParams
import matplotlib.font_manager as fm
from event_analysis import extract_event_data, analyze_meal
from glucose_analysis import calculate_metrics, create_agp, create_daily_clusters
from deep_analysis import perform_deep_analysis
from split_csv import split_csv
from insulin_input import get_insulin_info
from insulin_analysis import extract_insulin_data, analyze_insulin, plot_insulin_data, get_insulin_statistics
from gri_rag import GRIAnalyzer, ReferenceDatabase, perform_gri_rag_analysis
from gri_plotting import plot_gri
from agp_variability import agp_variability
from profile_config import PATIENT_PROFILES, DEFAULT_PROFILE_KEY

# 設置中文顯示
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

REFERENCE_DB_PATH = "reference_database"

def read_cgm_file(file_path):
    if not os.path.exists(file_path):
        st.error(f"文件不存在：{file_path}")
        return pd.DataFrame()

    st.write(f"正在處理 CGM 數據文件：{os.path.basename(file_path)}")

    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        st.error(f"讀取文件時發生錯誤：{str(e)}")
        return pd.DataFrame()

    required_columns = ['Date', 'Time', 'Sensor Glucose (mg/dL)']
    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        st.error(f"文件 {os.path.basename(file_path)} 中缺少以下必要的 {', '.join(missing_columns)}")
        return pd.DataFrame()

    df['Timestamp'] = pd.to_datetime(df['Date'].astype(str) + ' ' + df['Time'].astype(str))
    df['Sensor Glucose (mg/dL)'] = pd.to_numeric(df['Sensor Glucose (mg/dL)'], errors='coerce')
    return df.sort_values('Timestamp')


def clean_value(value):
    if isinstance(value, (float, int)):
        return float(value)
    if isinstance(value, str):
        value = value.strip()
        if '%' in value:
            return float(value.strip('%')) / 100
        if 'mg/dL' in value:
            return float(value.split()[0])
    try:
        return float(value)
    except ValueError:
        return value


def format_gri_metrics_text(gri_metrics):
    if not isinstance(gri_metrics, dict) or not gri_metrics:
        return "尚無 GRI 指標可供分析。"

    lines = []
    mean_gri = gri_metrics.get("Mean GRI")
    hypo_component = gri_metrics.get("Hypoglycemia Component")
    hyper_component = gri_metrics.get("Hyperglycemia Component")

    if mean_gri is not None and not (isinstance(mean_gri, float) and np.isnan(mean_gri)):
        lines.append(f"- Mean GRI 約 **{float(mean_gri):.2f}**，綜合評估整體風險。")

    def _format_percentage(value):
        if value is None:
            return "資料不足"
        if isinstance(value, (float, np.floating)) and np.isnan(value):
            return "資料不足"
        return f"{float(value):.2f}%"

    if hypo_component is not None or hyper_component is not None:
        hypo_text = _format_percentage(hypo_component)
        hyper_text = _format_percentage(hyper_component)
        lines.append(f"- 低血糖風險成分：{hypo_text}，高血糖風險成分：{hyper_text}。")

    return "\n".join(lines) if lines else "尚無 GRI 指標可供分析。"


st.title("CGM 數據分析")

st.sidebar.title("設定")

# 可選分析模型：key 為 API model id，value 為 UI 顯示用說明。
# GPT-5.6 系列為目前最新世代；舊的 gpt-5 / gpt-5-mini / gpt-5-nano 已於
# 2026-06-11 公告淘汰，並將於 2026-12-11 自 API 下線，故不再列為選項
# （官方對應替代品分別為 sol / terra / luna）。
MODEL_OPTIONS = {
    "gpt-5.6-sol": {
        "label": "GPT-5.6 Sol — 旗艦推理",
        "note": "分析品質最高，適合複雜或難解個案。約 $5 / $30 每 1M tokens（輸入 / 輸出）",
    },
    "gpt-5.6-terra": {
        "label": "GPT-5.6 Terra — 均衡（推薦）",
        "note": "品質與成本兼顧，適合日常報告產出。約 $2 / $12 每 1M tokens（輸入 / 輸出）",
    },
    "gpt-5.6-luna": {
        "label": "GPT-5.6 Luna — 高效省成本",
        "note": "適合大量批次分析。約 $0.20 / $1.20 每 1M tokens（輸入 / 輸出）",
    },
    "gpt-4o": {
        "label": "GPT-4o — 舊版通用",
        "note": "非推理模型，回應較快但分析深度較淺。約 $2.50 / $10 每 1M tokens（輸入 / 輸出）",
    },
    "gpt-4o-mini": {
        "label": "GPT-4o mini — 舊版最省",
        "note": "成本最低，適合快速試跑或驗證流程。約 $0.15 / $0.60 每 1M tokens（輸入 / 輸出）",
    },
}

DEFAULT_MODEL_KEY = "gpt-5.6-terra"

_model_keys = list(MODEL_OPTIONS.keys())

selected_model = st.sidebar.selectbox(
    "選擇分析模型：",
    _model_keys,
    index=_model_keys.index(DEFAULT_MODEL_KEY),
    format_func=lambda key: MODEL_OPTIONS[key]["label"],
    help=(
        "可用模型 (USD 定價以官方公告為準)：\n\n"
        + "\n".join(
            f"- {config['label']}：{config['note']}"
            for config in MODEL_OPTIONS.values()
        )
    )
)

st.sidebar.caption(MODEL_OPTIONS[selected_model]["note"])

openai_api_key = st.sidebar.text_input(
    label="請輸入您的 OpenAI API 金鑰：",
    type='password',
    placeholder="sk-...",
    help="從 https://platform.openai.com/account/api-keys 獲取"
)

profile_keys = list(PATIENT_PROFILES.keys())
default_profile_index = profile_keys.index(DEFAULT_PROFILE_KEY) if DEFAULT_PROFILE_KEY in profile_keys else 0
selected_profile_key = st.sidebar.selectbox(
    "選擇族群目標：",
    profile_keys,
    index=default_profile_index,
    format_func=lambda key: PATIENT_PROFILES[key]['display_name']
)
profile_config = PATIENT_PROFILES[selected_profile_key]

target_lower, target_upper = profile_config['target_range']
st.sidebar.markdown(
    f"**目標範圍**：{target_lower}-{target_upper} mg/dL\n\n"
    f"{profile_config['targets_summary']}"
)

uploaded_file = st.file_uploader("請上傳 CGM 數據文件（CSV 或 Excel 格式）", type=["csv", "xlsx", "xls"])

if uploaded_file:
    st.success(f"文件 {uploaded_file.name} 已成功上傳")

    st.subheader("胰島素資訊")
    insulin_info = get_insulin_info()

    if st.button("執行分析"):
        output_directory = "output_directory"
        os.makedirs(output_directory, exist_ok=True)

        event_file, sensor_glucose_file = split_csv(uploaded_file, output_directory)
        if event_file and sensor_glucose_file:
            st.success(f"文件 {uploaded_file.name} 已成功拆分")

            cgm_df = read_cgm_file(sensor_glucose_file)
            meal_data, insulin_data = extract_event_data([event_file])
            insulin_data = extract_insulin_data(event_file)

            if not cgm_df.empty:
                st.header("血糖數據分析")

                st.subheader("族群目標與建議")
                st.markdown(
                    f"**{profile_config['display_name']}**\n\n"
                    f"- 建議 Time in Range：`{target_lower}-{target_upper} mg/dL`\n"
                    f"- {profile_config['targets_summary']}\n\n"
                    f"{profile_config['recommendation']}"
                )

                cgm_metrics = calculate_metrics(cgm_df, profile_config)
                agp_plot = create_agp(cgm_df, profile_config)
                daily_clusters_plot = create_daily_clusters(cgm_df, profile_config)

                st.subheader("血糖數據指標")
                col1, col2, col3, col4 = st.columns(4)

                range_metrics = [config['metric_label'] for config in profile_config['ranges']]
                metrics_order = range_metrics + ["CV", "Mean Glucose (mg/dL)", "GMI", "GRI"]
                percentage_metrics = set(range_metrics)

                for i, metric in enumerate(metrics_order):
                    column = [col1, col2, col3, col4][i % 4]
                    with column:
                        value = cgm_metrics.get(metric, "N/A")
                        if isinstance(value, (float, np.floating)):
                            if metric == "Mean Glucose (mg/dL)":
                                st.metric(label=metric, value=f"{value:.1f}")
                            elif metric in percentage_metrics:
                                st.metric(label=metric, value=f"{value:.2%}")
                            else:
                                st.metric(label=metric, value=f"{value:.2f}")
                        else:
                            st.metric(label=metric, value=value)

            if insulin_data is not None:
                st.header("胰島素數據分析")
                analyzed_insulin_data = analyze_insulin(insulin_data, insulin_info)

                fig = plot_insulin_data(analyzed_insulin_data)
                st.pyplot(fig)

                st.subheader("胰島素注射統計")
                insulin_stats = get_insulin_statistics(analyzed_insulin_data)

                for category in ['長效胰島素', '速效胰島素', '預混胰島素', '未知']:
                    if category in insulin_stats:
                        st.write(f"**{category}**")
                        data = insulin_stats[category]
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("平均劑量", f"{data['平均劑量']} 單位")
                        with col2:
                            st.metric("注射次數", data['注射次數'])
                        st.write(f"劑量範圍: {data['最小劑量']} - {data['最大劑量']} 單位")

                        if category != '未知':
                            if data['常見注射時間']:
                                st.write("常見注射時間和平均劑量：")
                                for time, avg_dose, count in data['常見注射時間']:
                                    st.write(f"  - {time:02d}:00 附近，平均劑量 {avg_dose} 單位 (共 {count} 次)")
                        else:
                            if '劑量分組' in data:
                                st.write("未分類胰島素注射分組：")
                                for avg_time, avg_dose, count in data['劑量分組']:
                                    hour = int(avg_time)
                                    minute = int((avg_time - hour) * 60)
                                    st.write(f"  - {hour:02d}:{minute:02d} 附近，平均劑量 {avg_dose} 單位 (共 {count} 次)")

                        for insulin_name, insulin_detail in data.items():
                            if isinstance(insulin_detail, dict) and insulin_name not in ['常見注射時間', '劑量分組']:
                                st.write(
                                    f"  - {insulin_name}: 平均劑量 {insulin_detail['平均劑量']} 單位, 注射次數 {insulin_detail['注射次數']}"
                                )

                        st.write("---")

                if '未知' in insulin_stats:
                    st.warning(
                        "有未分類的胰島素注射記錄。這些記錄已根據劑量和時間進行了分組。"
                        "請檢查這些分組是否符合您的實際使用情況，並考慮更新您的胰島素輸入設置。"
                    )
            else:
                st.warning("無法提取有效的胰島素數據。")

            if not meal_data.empty:
                st.header("餐食數據分析")
                st.success(f"成功提取餐食數據！共 {len(meal_data)} 條記錄")

                st.subheader("餐食數據預覽")
                st.dataframe(meal_data.head())

                meal_metrics, meal_daily_stats = analyze_meal(meal_data)

                st.subheader("餐食分析結果")
                col1, col2 = st.columns(2)
                for i, (key, value) in enumerate(meal_metrics.items()):
                    if isinstance(value, (float, np.floating)):
                        st.metric(label=key, value=f"{value:.2f}")
                    elif isinstance(value, str):
                        cleaned = float(value.strip('%')) / 100 if '%' in value else float(value)
                        st.metric(label=key, value=f"{cleaned:.2f}")
                    else:
                        st.metric(label=key, value=value)

                st.subheader("每日餐食統計")
                st.dataframe(meal_daily_stats)
            else:
                st.warning("無法從文件中提取有效的餐食數據。")

            if not cgm_df.empty and insulin_data is not None:
                st.header("In-depth analysis and summary")
                if openai_api_key:
                    with st.spinner("正在進行深度分析，請稍候..."):
                        st.subheader("AGP analysis")
                        agp_result = agp_variability(
                            cgm_df,
                            openai_api_key,
                            model_name=selected_model
                        )

                        agp_analysis = agp_result.agp_analysis
                        hypo_hyper_analysis = agp_result.hypo_hyper_analysis
                        sd = agp_result.sd
                        cv = agp_result.cv
                        mage = agp_result.mage

                        st.pyplot(agp_plot)
                        if agp_result.notice:
                            st.caption(agp_result.notice.strip())

                        st.write("AGP 分析:", agp_analysis)
                        st.write("低血糖和高血糖分析:", hypo_hyper_analysis)
                        if agp_result.envelope_summary:
                            st.markdown(agp_result.envelope_summary)

                        st.subheader("Daily Clusters Plot")
                        st.pyplot(daily_clusters_plot)

                        st.subheader("GRI 分析")
                        try:
                            try:
                                reference_db = ReferenceDatabase(REFERENCE_DB_PATH)
                            except Exception as e:
                                st.warning(f"無法載入參考資料庫：{str(e)}。將繼續進行基本分析。")
                                reference_db = None

                            gri_analyzer = GRIAnalyzer(cgm_df, reference_db)
                            gri_analysis = gri_analyzer.analyze()

                            gri_rag_result = perform_gri_rag_analysis(
                                gri_analysis,
                                openai_api_key,
                                model_name=selected_model
                            )

                            gri_plot = plot_gri(cgm_df)
                            st.plotly_chart(gri_plot)

                            st.write("GRI 分析結果：")
                            st.markdown(format_gri_metrics_text(gri_analysis))
                            if gri_rag_result.notice:
                                st.caption(gri_rag_result.notice.strip())
                            if gri_rag_result.content:
                                st.markdown(gri_rag_result.content)

                        except Exception as e:
                            st.error(f"GRI 分析時發生錯誤：{str(e)}")

                        deep_analysis_result = perform_deep_analysis(
                            cgm_df=cgm_df,
                            insulin_data=insulin_data,
                            meal_data=meal_data,
                            cgm_metrics=cgm_metrics,
                            insulin_stats=insulin_stats,
                            agp_analysis=agp_analysis,
                            hypo_hyper_analysis=hypo_hyper_analysis,
                            gri_analysis=gri_analysis,
                            gri_gpt4_analysis=gri_rag_result.content,
                            openai_api_key=openai_api_key,
                            model_name=selected_model,
                            profile_config=profile_config,
                            agp_notice=agp_result.notice,
                            gri_notice=gri_rag_result.notice,
                            agp_envelope_summary=agp_result.envelope_summary,
                            sd=sd,
                            cv=cv,
                            mage=mage
                        )

                        st.subheader("綜合分析結果")
                        for key, value in deep_analysis_result.items():
                            st.write(f"**{key}:**")
                            st.write(value)
                            st.write("---")
                else:
                    st.warning("請輸入 OpenAI API 金鑰以進行深度分析。")
        else:
            st.error(f"文件 {uploaded_file.name} 拆分失敗")
else:
    st.info("請上傳 CGM 數據文件（CSV 或 Excel 格式）。")
