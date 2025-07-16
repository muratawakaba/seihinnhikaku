import os
import re
import streamlit as st
import pandas as pd
import google.generativeai as genai

# APIキー設定（環境変数 GEMINI_API_KEY から）
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

st.title("家電性能比較アプリ（Gemini API利用）")

# Step1: 家電の種類選択
appliance_types = st.multiselect(
    "比較したい家電の種類を選択してください",
    options=["エアコン", "冷蔵庫", "洗濯機"],
    default=["エアコン"]
)

if not appliance_types:
    st.warning("家電の種類を一つ以上選択してください。")
    st.stop()

# Step2: 各家電種ごとに製品名を複数行入力
product_inputs = {}
for appliance in appliance_types:
    text = st.text_area(
        f"{appliance}の製品名を1行ずつ入力してください",
        height=100,
        key=appliance
    )
    product_inputs[appliance] = [line.strip() for line in text.strip().split("\n") if line.strip()]

# 利用したいモデル名に変更してください
model = genai.GenerativeModel("gemini-2.0-flash")

all_data = []

if st.button("性能を取得して比較"):

    for appliance, products in product_inputs.items():
        if not products:
            st.warning(f"{appliance}の製品名が入力されていません。")
            continue

        for product in products:
            prompt = (
                f"家電の種類は「{appliance}」、製品名は「{product}」です。性能を教えてください。\n"
                "できること：３つ以上、懸念点：２つ以上を箇条書きで答えてください。\n"
                "消費電力（W）と年間電気代（円）を以下の形式で答えてください。\n"
                "消費電力: 数値\n"
                "年間電気代: 数値\n"
                "例:\n消費電力: 1200\n年間電気代: 18000\n"
            )

            try:
                response = model.generate_content(prompt)
                text = response.text

                st.markdown(f"#### {appliance} - {product} の性能情報（Gemini回答）")
                st.text(text)

                # 正規表現で消費電力と年間電気代を抽出
                # 太字マークダウン（**）やカンマ、全角半角コロンに対応
                power_match = re.search(r"消費電力[:：]?\s*\**\s*([\d,]+)", text)
                cost_match = re.search(r"年間電気代[:：]?\s*\**\s*([\d,]+)", text)

                if power_match and cost_match:
                    power_val = int(power_match.group(1).replace(",", ""))
                    cost_val = int(cost_match.group(1).replace(",", ""))

                    all_data.append({
                        "種類": appliance,
                        "製品名": product,
                        "消費電力（W）": power_val,
                        "年間電気代（円）": cost_val
                    })
                else:
                    st.warning(f"{appliance} - {product} の性能情報を正しく解析できませんでした。")
                    st.text("=== APIの返答全文 ===")
                    st.text(text)
            except Exception as e:
                st.error(f"{appliance} - {product} の情報取得中にエラーが発生しました: {e}")

    st.write(f"## 解析できた製品数: {len(all_data)}")

    if all_data:
        df = pd.DataFrame(all_data)

        st.subheader("製品性能比較表")
        st.dataframe(df)

        st.subheader("年間電気代の比較")
        st.bar_chart(df.set_index("製品名")["年間電気代（円）"])

        st.subheader("消費電力の比較")
        st.bar_chart(df.set_index("製品名")["消費電力（W）"])
    else:
        st.warning("性能情報が取得できませんでした。")
