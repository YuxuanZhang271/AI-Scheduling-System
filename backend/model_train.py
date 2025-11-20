import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import datetime as dt

# --------- 1) 加载数据 ----------
stats_df = pd.read_csv("stats_check.csv")
tasks_df = pd.read_csv("schedule.csv")
new_tasks_df = pd.read_csv("new_tasks_df.csv")

# 统一时间列为 datetime（如果有 Timestamp 列）
if "Timestamp" in stats_df.columns:
    stats_df["timestamp"] = pd.to_datetime(stats_df["Timestamp"], errors="coerce")
    stats_df = stats_df.drop(columns=["Timestamp"]).sort_values("timestamp")
else:
    # 假如 stats_df 已经有 timestamp 列
    stats_df["timestamp"] = pd.to_datetime(stats_df["timestamp"], errors="coerce")
    stats_df = stats_df.sort_values("timestamp")

if "Timestamp" in tasks_df.columns:
    tasks_df["timestamp"] = pd.to_datetime(tasks_df["Timestamp"], errors="coerce")
    tasks_df = tasks_df.drop(columns=["Timestamp"]).sort_values("timestamp")
else:
    tasks_df["timestamp"] = pd.to_datetime(tasks_df.get("timestamp", None), errors="coerce")
    tasks_df = tasks_df.sort_values("timestamp")

# 方便：确定 stats 中能量/压力列名
energy_col = "Energy" if "Energy" in stats_df.columns else ("energy" if "energy" in stats_df.columns else None)
pressure_col = "Pressure" if "Pressure" in stats_df.columns else ("pressure" if "pressure" in stats_df.columns else None)
if energy_col is None or pressure_col is None:
    raise ValueError("在 stats_check.csv 中找不到 Energy/Pressure 列，请确认列名。")

# --------- 辅助函数 ----------
def parse_time_to_seconds(tval):
    """输入可能是 'HH:MM:SS' 或 pandas.Timestamp.time() 或 str，返回从午夜起的秒数"""
    if pd.isna(tval):
        return None
    if isinstance(tval, str):
        # 允许 "HH:MM" / "HH:MM:SS"
        try:
            tt = dt.datetime.strptime(tval, "%H:%M:%S").time()
        except Exception:
            try:
                tt = dt.datetime.strptime(tval, "%H:%M").time()
            except Exception:
                # 可能是包含日期的 timestamp 字符串
                tt = pd.to_datetime(tval, errors="coerce").time()
        return tt.hour*3600 + tt.minute*60 + tt.second
    if isinstance(tval, (dt.time, pd._libs.tslibs.timestamps.Timestamp)):
        if isinstance(tval, pd._libs.tslibs.timestamps.Timestamp):
            tval = tval.time()
        return tval.hour*3600 + tval.minute*60 + tval.second
    return None

# --------- 2) 在 tasks_df 上计算 duration（分钟）以便训练使用 ----------
def compute_duration_minutes(row):
    s = parse_time_to_seconds(row.get("Start time"))
    e = parse_time_to_seconds(row.get("End time"))
    if s is None or e is None:
        return np.nan
    # 若跨午夜（end < start），处理为跨天
    if e < s:
        e += 24*3600
    return (e - s) / 60.0

tasks_df["duration"] = tasks_df.apply(compute_duration_minutes, axis=1)
# 把 Difficulty 列转成数值列（容错）
tasks_df["difficulty"] = pd.to_numeric(tasks_df["Difficulty"], errors="coerce").fillna(0.0)

# --------- 3) 用 stats_check.csv 为每个 task 计算 energy_loss 和 pressure_increase ----------
# 遍历每个用户，按你之前的做法做线性插值
names = stats_df["Name"].unique()
for name in names:
    sub_stats_df = stats_df[stats_df["Name"] == name].sort_values("timestamp").reset_index(drop=True).copy()
    if sub_stats_df.empty:
        continue
    # 秒级时间
    sub_stats_df["tsec"] = sub_stats_df["timestamp"].dt.hour*3600 + sub_stats_df["timestamp"].dt.minute*60 + sub_stats_df["timestamp"].dt.second

    sub_tasks_idx = tasks_df[tasks_df["User name"] == name].index.to_numpy()
    for idx in sub_tasks_idx:
        task = tasks_df.loc[idx]
        ssec = parse_time_to_seconds(task.get("Start time"))
        esec = parse_time_to_seconds(task.get("End time"))
        if ssec is None or esec is None:
            continue
        # 处理跨午夜
        if esec < ssec:
            esec += 24*3600

        in_range = (sub_stats_df["tsec"] >= ssec) & (sub_stats_df["tsec"] < esec)
        true_pos = np.flatnonzero(in_range.to_numpy())
        if true_pos.size == 0:
            # 没样本点位于该区间，跳过（也可以选择外插）
            continue
        gaps = np.where(np.diff(true_pos) > 1)[0]
        seg_start_pos = true_pos[0]
        seg_end_pos = true_pos[gaps[0]] if gaps.size > 0 else true_pos[-1]
        prev_pos = max(seg_start_pos - 1, 0)
        next_pos = min(seg_end_pos + 1, len(sub_stats_df) - 1)

        def lerp_at(col, t_query, p0, p1):
            t0 = float(sub_stats_df.loc[p0, "tsec"]); v0 = float(sub_stats_df.loc[p0, col])
            t1 = float(sub_stats_df.loc[p1, "tsec"]); v1 = float(sub_stats_df.loc[p1, col])
            if t1 == t0:
                return v0
            return v0 + (v1 - v0) * (t_query - t0) / (t1 - t0)

        start_energy = lerp_at(energy_col, ssec, prev_pos, seg_start_pos)
        end_energy   = lerp_at(energy_col, esec, seg_end_pos, next_pos)
        start_pressure = lerp_at(pressure_col, ssec, prev_pos, seg_start_pos)
        end_pressure   = lerp_at(pressure_col, esec, seg_end_pos, next_pos)

        tasks_df.loc[idx, "energy_loss"] = end_energy - start_energy
        tasks_df.loc[idx, "pressure_increase"] = end_pressure - start_pressure

# 丢弃没有标签的样本（没有计算到 energy/pressure 的任务）
train_df = tasks_df.dropna(subset=["energy_loss", "pressure_increase"]).copy()
if train_df.empty:
    raise ValueError("未找到任何带有 energy_loss / pressure_increase 的训练样本，请检查 stats_check.csv 与 schedule.csv 的时间对齐。")

# --------- 4) 特征编码与训练 ---------
# Task type 编码器（训练时 fit）
le = LabelEncoder()
train_types = train_df["Task type"].astype(str).fillna("UNKNOWN")
le.fit(train_types)
train_df["type_encoded"] = le.transform(train_types)

# 准备 X,y
train_df["duration"] = pd.to_numeric(train_df["duration"], errors="coerce").fillna(0.0)
X = train_df[["type_encoded", "difficulty", "duration"]].fillna(0.0)
y_energy = train_df["energy_loss"].astype(float)
y_pressure = train_df["pressure_increase"].astype(float)

X_train, X_test, y_train_e, y_test_e = train_test_split(X, y_energy, test_size=0.2, random_state=42)
_, _, y_train_p, y_test_p = train_test_split(X, y_pressure, test_size=0.2, random_state=42)

model_energy = RandomForestRegressor(n_estimators=100, random_state=42)
model_pressure = RandomForestRegressor(n_estimators=100, random_state=42)
model_energy.fit(X_train, y_train_e)
model_pressure.fit(X_train, y_train_p)

# 评估
y_pred_energy = model_energy.predict(X_test)
y_pred_pressure = model_pressure.predict(X_test)

print("\n=== Energy Loss Prediction ===")
print("MAE:", mean_absolute_error(y_test_e, y_pred_energy))
print("MSE:", mean_squared_error(y_test_e, y_pred_energy))
print("R²:", r2_score(y_test_e, y_pred_energy))

print("\n=== Pressure Increase Prediction ===")
print("MAE:", mean_absolute_error(y_test_p, y_pred_pressure))
print("MSE:", mean_squared_error(y_test_p, y_pred_pressure))
print("R²:", r2_score(y_test_p, y_pred_pressure))

# 保存模型与编码器
joblib.dump(model_energy, "energy_loss_model.pkl")
joblib.dump(model_pressure, "pressure_increase_model.pkl")
joblib.dump(le, "task_label_encoder.pkl")
print("Saved models and label encoder.")

# --------- 5) 对 new_tasks_df 进行预处理并预测 ----------
# 计算新任务 duration & difficulty 字段
new_tasks_df["duration"] = new_tasks_df.apply(compute_duration_minutes, axis=1)
new_tasks_df["difficulty"] = pd.to_numeric(new_tasks_df["Difficulty"], errors="coerce").fillna(0.0)

# 编码 Task type：对训练集中未见类型，映射为 len(le.classes_)
type_map = {v:i for i,v in enumerate(le.classes_)}
unknown_code = len(type_map)
def encode_type_for_new(t):
    tstr = str(t) if not pd.isna(t) else "UNKNOWN"
    return type_map.get(tstr, unknown_code)

new_tasks_df["type_encoded"] = new_tasks_df["Task type"].apply(encode_type_for_new)

# 如果出现 unknown_code（说明有未见类型），模型仍能接收数值输入，虽不保证预测优异
X_new = new_tasks_df[["type_encoded", "difficulty", "duration"]].fillna(0.0)

# 载入模型并预测（也可以直接使用内存中的 model_*）
energy_model = joblib.load("energy_loss_model.pkl")
pressure_model = joblib.load("pressure_increase_model.pkl")

new_tasks_df["Predicted_Energy_Loss"] = energy_model.predict(X_new)
new_tasks_df["Predicted_Pressure_Increase"] = pressure_model.predict(X_new)

# 输出并保存
out_cols = ["Timestamp", "User name", "Task type", "Start time", "End time", "Difficulty", "duration",
            "Predicted_Energy_Loss", "Predicted_Pressure_Increase"]
new_tasks_df.to_csv("predicted_new_tasks.csv", index=False)
print("Saved predictions to predicted_new_tasks.csv")
print(new_tasks_df[out_cols].head(10))