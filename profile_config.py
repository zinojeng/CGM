PATIENT_PROFILES = {
    "T1DM": {
        "display_name": "第 1 型糖尿病 (T1DM)",
        "target_range": (70, 180),
        "ranges": [
            {
                "metric_label": "VLow (<54 mg/dL)",
                "daily_label": "Time < 54 mg/dL",
                "min": None,
                "max": 54,
                "include_lower": True,
                "include_upper": False,
                "color": "#990000"
            },
            {
                "metric_label": "Low (54-<70 mg/dL)",
                "daily_label": "TBR (54-69 mg/dL)",
                "min": 54,
                "max": 70,
                "include_lower": True,
                "include_upper": False,
                "color": "#FF0000"
            },
            {
                "metric_label": "TIR (70-180 mg/dL)",
                "daily_label": "TIR (70-180 mg/dL)",
                "min": 70,
                "max": 180,
                "include_lower": True,
                "include_upper": True,
                "color": "#228B22"
            },
            {
                "metric_label": "High (>180-250 mg/dL)",
                "daily_label": "TAR (181-250 mg/dL)",
                "min": 180,
                "max": 250,
                "include_lower": False,
                "include_upper": True,
                "color": "#FFFF00"
            },
            {
                "metric_label": "VHigh (>250 mg/dL)",
                "daily_label": "Time > 250 mg/dL",
                "min": 250,
                "max": None,
                "include_lower": False,
                "include_upper": True,
                "color": "#FF9900"
            }
        ],
        "targets_summary": "TIR 70-180 mg/dL ≥70%；<70 mg/dL <4%；<54 mg/dL <1%；>180 mg/dL <25%；>250 mg/dL <5%。",
        "recommendation": (
            "- **Time in Range**：維持 70–180 mg/dL 區間時間 ≥70%。\n"
            "- **低血糖管理**：<70 mg/dL 控制於 <4%，且 <54 mg/dL 控制於 <1%。\n"
            "- **高血糖管理**：>180 mg/dL 控制於 <25%，>250 mg/dL 控制於 <5%。\n"
            "- 建議定期檢視胰島素調整與日常作息，避免劇烈波動。"
        )
    },
    "T2DM": {
        "display_name": "第 2 型糖尿病 (T2DM)",
        "target_range": (70, 180),
        "ranges": [
            {
                "metric_label": "VLow (<54 mg/dL)",
                "daily_label": "Time < 54 mg/dL",
                "min": None,
                "max": 54,
                "include_lower": True,
                "include_upper": False,
                "color": "#990000"
            },
            {
                "metric_label": "Low (54-<70 mg/dL)",
                "daily_label": "TBR (54-69 mg/dL)",
                "min": 54,
                "max": 70,
                "include_lower": True,
                "include_upper": False,
                "color": "#FF0000"
            },
            {
                "metric_label": "TIR (70-180 mg/dL)",
                "daily_label": "TIR (70-180 mg/dL)",
                "min": 70,
                "max": 180,
                "include_lower": True,
                "include_upper": True,
                "color": "#228B22"
            },
            {
                "metric_label": "High (>180-250 mg/dL)",
                "daily_label": "TAR (181-250 mg/dL)",
                "min": 180,
                "max": 250,
                "include_lower": False,
                "include_upper": True,
                "color": "#FFFF00"
            },
            {
                "metric_label": "VHigh (>250 mg/dL)",
                "daily_label": "Time > 250 mg/dL",
                "min": 250,
                "max": None,
                "include_lower": False,
                "include_upper": True,
                "color": "#FF9900"
            }
        ],
        "targets_summary": "TIR 70-180 mg/dL ≥70%；<70 mg/dL <4%；<54 mg/dL <1%；>180 mg/dL <25%；>250 mg/dL <5%。",
        "recommendation": (
            "- **Time in Range**：建議保持 70–180 mg/dL ≥70%，以降低慢性併發症風險。\n"
            "- **低血糖風險**：<70 mg/dL 控制於 <4%，<54 mg/dL 控制於 <1%。\n"
            "- **高血糖風險**：>180 mg/dL 控制於 <25%，>250 mg/dL 控制於 <5%。\n"
            "- 與醫療團隊討論降糖藥物與生活管理，兼顧心血管與體重目標。"
        )
    },
    "GDM": {
        "display_name": "妊娠糖尿病 (GDM)",
        "target_range": (63, 140),
        "ranges": [
            {
                "metric_label": "Time <54 mg/dL",
                "daily_label": "Time < 54 mg/dL",
                "min": None,
                "max": 54,
                "include_lower": True,
                "include_upper": False,
                "color": "#990000"
            },
            {
                "metric_label": "Below Target (54-<63 mg/dL)",
                "daily_label": "TBR (54-62 mg/dL)",
                "min": 54,
                "max": 63,
                "include_lower": True,
                "include_upper": False,
                "color": "#FF0000"
            },
            {
                "metric_label": "TIR (63-140 mg/dL)",
                "daily_label": "TIR (63-140 mg/dL)",
                "min": 63,
                "max": 140,
                "include_lower": True,
                "include_upper": True,
                "color": "#228B22"
            },
            {
                "metric_label": "High (141-160 mg/dL)",
                "daily_label": "Above Target (141-160 mg/dL)",
                "min": 140,
                "max": 160,
                "include_lower": False,
                "include_upper": True,
                "color": "#FFFF00"
            },
            {
                "metric_label": "VHigh (>160 mg/dL)",
                "daily_label": "Time > 160 mg/dL",
                "min": 160,
                "max": None,
                "include_lower": False,
                "include_upper": True,
                "color": "#FF9900"
            }
        ],
        "targets_summary": "TIR 63-140 mg/dL ≥70%；<63 mg/dL <4%；<54 mg/dL <1%；>140 mg/dL <25%。",
        "recommendation": (
            "- **Time in Range**：妊娠期間建議血糖維持 63–140 mg/dL ≥70%。\n"
            "- **低血糖管理**：<63 mg/dL 控制於 <4%，<54 mg/dL 控制於 <1%，確保母胎安全。\n"
            "- **高血糖管理**：>140 mg/dL 控制於 <25%，避免巨大兒與新生兒低血糖。\n"
            "- 每日監測餐後血糖並調整飲食與胰島素，以符合產科建議。"
        )
    },
    "Pregnancy_T1D": {
        "display_name": "孕期合併第 1 型糖尿病",
        "target_range": (63, 140),
        "ranges": [
            {
                "metric_label": "Time <54 mg/dL",
                "daily_label": "Time < 54 mg/dL",
                "min": None,
                "max": 54,
                "include_lower": True,
                "include_upper": False,
                "color": "#990000"
            },
            {
                "metric_label": "Below Target (54-<63 mg/dL)",
                "daily_label": "TBR (54-62 mg/dL)",
                "min": 54,
                "max": 63,
                "include_lower": True,
                "include_upper": False,
                "color": "#FF0000"
            },
            {
                "metric_label": "TIR (63-140 mg/dL)",
                "daily_label": "TIR (63-140 mg/dL)",
                "min": 63,
                "max": 140,
                "include_lower": True,
                "include_upper": True,
                "color": "#228B22"
            },
            {
                "metric_label": "High (141-160 mg/dL)",
                "daily_label": "Above Target (141-160 mg/dL)",
                "min": 140,
                "max": 160,
                "include_lower": False,
                "include_upper": True,
                "color": "#FFFF00"
            },
            {
                "metric_label": "VHigh (>160 mg/dL)",
                "daily_label": "Time > 160 mg/dL",
                "min": 160,
                "max": None,
                "include_lower": False,
                "include_upper": True,
                "color": "#FF9900"
            }
        ],
        "targets_summary": "TIR 63-140 mg/dL ≥70%；<63 mg/dL <4%；<54 mg/dL <1%；>140 mg/dL <25%。",
        "recommendation": (
            "- **孕期目標**：維持 63–140 mg/dL ≥70%，以減少母胎併發症。\n"
            "- **低血糖保護**：特別注意夜間 <63 mg/dL，確保有適當的備援碳水化合物。\n"
            "- **高血糖控制**：>140 mg/dL 控制於 <25%，配合胰島素微調與飲食管理。\n"
            "- 與產科與糖尿病團隊密切合作，調整胰島素基礎率與餐次劑量。"
        )
    },
    "Pregnancy_T2D": {
        "display_name": "孕期合併第 2 型糖尿病",
        "target_range": (63, 140),
        "ranges": [
            {
                "metric_label": "Time <54 mg/dL",
                "daily_label": "Time < 54 mg/dL",
                "min": None,
                "max": 54,
                "include_lower": True,
                "include_upper": False,
                "color": "#990000"
            },
            {
                "metric_label": "Below Target (54-<63 mg/dL)",
                "daily_label": "TBR (54-62 mg/dL)",
                "min": 54,
                "max": 63,
                "include_lower": True,
                "include_upper": False,
                "color": "#FF0000"
            },
            {
                "metric_label": "TIR (63-140 mg/dL)",
                "daily_label": "TIR (63-140 mg/dL)",
                "min": 63,
                "max": 140,
                "include_lower": True,
                "include_upper": True,
                "color": "#228B22"
            },
            {
                "metric_label": "High (141-160 mg/dL)",
                "daily_label": "Above Target (141-160 mg/dL)",
                "min": 140,
                "max": 160,
                "include_lower": False,
                "include_upper": True,
                "color": "#FFFF00"
            },
            {
                "metric_label": "VHigh (>160 mg/dL)",
                "daily_label": "Time > 160 mg/dL",
                "min": 160,
                "max": None,
                "include_lower": False,
                "include_upper": True,
                "color": "#FF9900"
            }
        ],
        "targets_summary": "TIR 63-140 mg/dL ≥70%；<63 mg/dL <4%；<54 mg/dL <1%；>140 mg/dL <25%。",
        "recommendation": (
            "- **Time in Range**：孕期建議 63–140 mg/dL ≥70%，平衡母胎需求。\n"
            "- **低血糖風險**：<63 mg/dL 維持 <4%，<54 mg/dL <1%，需要加強自我監測。\n"
            "- **高血糖風險**：>140 mg/dL 維持 <25%，若使用胰島素或口服藥需與醫師討論調整。\n"
            "- 注意體重變化與餐次碳水配置，搭配規律活動提升血糖穩定度。"
        )
    }
}

DEFAULT_PROFILE_KEY = "T1DM"
