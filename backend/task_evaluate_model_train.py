import datetime as dt
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib


stats_df              = pd.read_csv("stats_check.csv")
stats_df["timestamp"] = pd.to_datetime(stats_df["Timestamp"], errors="coerce")
stats_df              = stats_df.drop(["Timestamp"], axis=1)
stats_df              = stats_df.sort_values("timestamp")

tasks_df              = pd.read_csv("schedule.csv")
tasks_df["timestamp"] = pd.to_datetime(tasks_df["Timestamp"], errors="coerce")
tasks_df              = tasks_df.drop(["Timestamp"], axis=1)
tasks_df              = tasks_df.sort_values("timestamp")

names = stats_df["Name"].unique()
for name in names: 
    sub_stats_df = stats_df[stats_df["Name"]==name]
    sub_stats_df["timestamp_time"] = sub_stats_df["timestamp"].dt.time

    sub_tasks_df = tasks_df[tasks_df["User name"]==name]

    stats_idx = 0
    for i in range(sub_tasks_df.shape[0]): 
        task       = sub_tasks_df.iloc[i]

        start_time = pd.Timestamp(task["Start time"]).time()
        end_time   = pd.Timestamp(task["End time"]).time()

        in_range = sub_stats_df["timestamp_time"].between(start_time, end_time, inclusive='left')
        true_indices = in_range[in_range].index.to_numpy()
        if len(true_indices) > 0:
            splits = np.where(np.diff(true_indices) > 1)[0]
            start_idx = true_indices[0]
            end_idx = true_indices[splits[0]] if len(splits) > 0 else true_indices[-1]
            # print(start_idx, end_idx)
        
        start_energy   = (sub_stats_df.loc[start_idx, "energy"] - sub_stats_df.loc[start_idx - 1, "energy"]) * (start_time - sub_stats_df.loc[start_idx - 1, "timestamp_time"]) / (sub_stats_df.loc[start_idx, "timestamp_time"] - sub_stats_df.loc[start_idx - 1, "timestamp_time"])
        end_energy     = (sub_stats_df.loc[end_idx + 1, "energy"] - sub_stats_df.loc[end_idx, "energy"]) * (start_time - sub_stats_df.loc[end_idx, "timestamp_time"]) / (sub_stats_df.loc[end_idx + 1, "timestamp_time"] - sub_stats_df.loc[end_idx, "timestamp_time"])
        start_pressure = (sub_stats_df.loc[start_idx, "pressure"] - sub_stats_df.loc[start_idx - 1, "pressure"]) * (start_time - sub_stats_df.loc[start_idx - 1, "timestamp_time"]) / (sub_stats_df.loc[start_idx, "timestamp_time"] - sub_stats_df.loc[start_idx - 1, "timestamp_time"])
        end_pressure   = (sub_stats_df.loc[end_idx + 1, "pressure"] - sub_stats_df.loc[end_idx, "pressure"]) * (start_time - sub_stats_df.loc[end_idx, "timestamp_time"]) / (sub_stats_df.loc[end_idx + 1, "timestamp_time"] - sub_stats_df.loc[end_idx, "timestamp_time"])

        task["energy"]   = end_energy - start_energy
        task["pressure"] = end_pressure - start_pressure

def time_to_sec(t):
    return int(t.hour) * 3600 + int(t.minute) * 60 + int(t.second)

# 列名自适应（你原代码里用过 energy/pressure 小写，这里兼容）
energy_col   = "Energy"   if "Energy"   in stats_df.columns else "energy"
pressure_col = "Pressure" if "Pressure" in stats_df.columns else "pressure"

names = stats_df["Name"].unique()
for name in names:
    # 充分拷贝并重建 RangeIndex，避免 SettingWithCopy + 非连续索引问题
    sub_stats_df = (
        stats_df[stats_df["Name"] == name]
        .sort_values("timestamp")
        .reset_index(drop=True)
        .copy()
    )
    # 转为“秒（从午夜起）”，以后都用秒做比较/插值
    sub_stats_df["tsec"] = (
        sub_stats_df["timestamp"].dt.hour * 3600
        + sub_stats_df["timestamp"].dt.minute * 60
        + sub_stats_df["timestamp"].dt.second
    )

    sub_tasks_df = tasks_df[tasks_df["User name"] == name]

    for i in range(sub_tasks_df.shape[0]):
        task = sub_tasks_df.iloc[i]
        task_row_idx = task.name  # 用于写回 tasks_df 的索引

        # 起止时间 → 秒
        start_time = pd.Timestamp(task["Start time"]).time()
        end_time   = pd.Timestamp(task["End time"]).time()
        ssec = time_to_sec(start_time)
        esec = time_to_sec(end_time)

        # 区间筛选（左闭右开）
        in_range_mask = (sub_stats_df["tsec"] >= ssec) & (sub_stats_df["tsec"] < esec)

        true_pos = np.flatnonzero(in_range_mask.to_numpy())
        if true_pos.size == 0:
            # 没有任何采样点落在该时间段，跳过或可选用外插策略
            continue

        # 仅取第一段 True 连续块
        gaps = np.where(np.diff(true_pos) > 1)[0]
        seg_start_pos = true_pos[0]
        seg_end_pos   = true_pos[gaps[0]] if gaps.size > 0 else true_pos[-1]

        # 为了在段首/段尾做线性插值，需要邻接点（防越界取有效范围）
        prev_pos = max(seg_start_pos - 1, 0)
        next_pos = min(seg_end_pos + 1, len(sub_stats_df) - 1)

        # 线性插值函数：给定列名、目标时刻（秒）与两端样本位置，返回该时刻的插值
        def lerp_at(col, t_query, p0, p1):
            t0 = float(sub_stats_df.loc[p0, "tsec"]); v0 = float(sub_stats_df.loc[p0, col])
            t1 = float(sub_stats_df.loc[p1, "tsec"]); v1 = float(sub_stats_df.loc[p1, col])
            if t1 == t0:  # 退化：两个时间点重合
                return v0
            return v0 + (v1 - v0) * (t_query - t0) / (t1 - t0)

        # 段首（start）与段尾（end）各做一次插值
        start_energy   = lerp_at(energy_col,   ssec, prev_pos, seg_start_pos)
        end_energy     = lerp_at(energy_col,   esec, seg_end_pos, next_pos)    # 注意这里用 esec
        start_pressure = lerp_at(pressure_col, ssec, prev_pos, seg_start_pos)
        end_pressure   = lerp_at(pressure_col, esec, seg_end_pos, next_pos)    # 注意这里用 esec

        # 写回该任务行：区间增量
        tasks_df.loc[task_row_idx, energy_col]   = end_energy - start_energy
        tasks_df.loc[task_row_idx, pressure_col] = end_pressure - start_pressure

# merged_df = pd.merge_asof(
#     task_df.sort_values("timestamp"),
#     stats_df.sort_values("timestamp"),
#     on="timestamp",
#     direction="nearest"
# )
# print(merged_df[merged_df["User name"]=="zyx"].head(20))

# le = LabelEncoder()
# merged_df["type_encoded"] = le.fit_transform(merged_df["Task type"].astype(str))
# merged_df["difficulty"] = merged_df["Difficulty"].astype(float)
# merged_df["duration"] = merged_df["duration"].astype(float)

# X = merged_df[["type_encoded", "difficulty", "duration"]].fillna(0)
# y = merged_df[["energy_loss", "pressure_increase"]].fillna(0)

# X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# model_energy = RandomForestRegressor(random_state=42)
# model_pressure = RandomForestRegressor(random_state=42)
# model_energy.fit(X_train, y_train["energy_loss"])
# model_pressure.fit(X_train, y_train["pressure_increase"])

# y_pred_energy = model_energy.predict(X_test)
# y_pred_pressure = model_pressure.predict(X_test)

# print("\n=== Energy Loss Prediction ===")
# print("MAE:", mean_absolute_error(y_test["energy_loss"], y_pred_energy))
# print("MSE:", mean_squared_error(y_test["energy_loss"], y_pred_energy))
# print("R²:", r2_score(y_test["energy_loss"], y_pred_energy))

# print("\n=== Pressure Increase Prediction ===")
# print("MAE:", mean_absolute_error(y_test["pressure_increase"], y_pred_pressure))
# print("MSE:", mean_squared_error(y_test["pressure_increase"], y_pred_pressure))
# print("R²:", r2_score(y_test["pressure_increase"], y_pred_pressure))

# joblib.dump(model_energy, "energy_loss_model.pkl")
# joblib.dump(model_pressure, "pressure_increase_model.pkl")

# def predict_task(task_type, difficulty, duration):
#     type_encoded = le.transform([task_type])[0]
#     X_new = pd.DataFrame([[type_encoded, difficulty, duration]],
#                          columns=["type_encoded", "difficulty", "duration"])
#     energy_pred = model_energy.predict(X_new)[0]
#     pressure_pred = model_pressure.predict(X_new)[0]
#     return {
#         "Predicted Energy Loss": round(energy_pred, 2),
#         "Predicted Pressure Increase": round(pressure_pred, 2)
#     }

# example = predict_task(task_type="Work", difficulty=3, duration=90)
# print("\nExample prediction:", example)