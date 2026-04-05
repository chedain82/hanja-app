import json
from pathlib import Path
import pandas as pd

EXCEL_FILE = "hanja DB_01.xlsm"
OUT_FILE = "assets/hanja_data.json"

EXPECTED_COLS = ["번호", "한자", "뜻", "독음", "급수", "단계", "타입"]


def safe_text(v):
    if pd.isna(v):
        return ""
    return str(v).strip()


def normalize_step_value(v: str) -> str:
    s = str(v).strip().upper().replace(" ", "")
    if not s:
        return ""
    if "-" in s:
        a, b = s.split("-", 1)
        if a and b:
            return f"{a}-{b}"
    return s


def compact_step_value(v: str) -> str:
    return str(v).replace("-", "").strip().upper()


# 📌 엑셀 읽기
df1 = pd.read_excel(EXCEL_FILE, sheet_name="DB-1")
df2 = pd.read_excel(EXCEL_FILE, sheet_name="DB-2")

# 📌 컬럼 정리
for df, default_type in [(df1, "선정"), (df2, "교과서")]:
    df.columns = [str(c).strip() for c in df.columns]

    for col in EXPECTED_COLS:
        if col not in df.columns:
            df[col] = ""

    df["타입"] = df["타입"].fillna("").astype(str).str.strip()
    df.loc[df["타입"] == "", "타입"] = default_type

# 📌 합치기
all_df = pd.concat([df1[EXPECTED_COLS], df2[EXPECTED_COLS]], ignore_index=True)

# 📌 전처리
for col in EXPECTED_COLS:
    all_df[col] = all_df[col].apply(safe_text)

all_df["단계"] = all_df["단계"].apply(normalize_step_value)
all_df["표시단계"] = all_df["단계"].apply(compact_step_value)

# 📌 저장 폴더 생성
Path("assets").mkdir(exist_ok=True)

# 📌 JSON 저장
with open(OUT_FILE, "w", encoding="utf-8") as f:
    json.dump(all_df.to_dict(orient="records"), f, ensure_ascii=False, indent=2)

print("✅ JSON 생성 완료:", OUT_FILE)