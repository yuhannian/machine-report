import streamlit as st
import pandas as pd
from io import BytesIO, StringIO

# 设置每日最低生产量标准
DAILY_PRODUCTION_MIN = 50

st.set_page_config(page_title="分切机台损耗报表", layout="centered")
st.title("📊 分切机台日损耗报表生成器")

uploaded_file = st.file_uploader("📂 请上传发货数据 CSV 文件（支持中文文件名）", type="csv")

# 检测中文字符
def contains_chinese(text):
    return any('\u4e00' <= ch <= '\u9fff' for ch in text)

# 生成报表函数
def generate_machine_loss_report(df):
    grouped = df.groupby('分切机台')[['加工量', '实际损耗']].sum().reset_index()
    grouped['损耗率'] = (grouped['实际损耗'] / grouped['加工量']).apply(lambda x: f"{x:.2%}")

    total_加工量 = grouped['加工量'].sum()
    total_实际损耗 = grouped['实际损耗'].sum()
    total_损耗率 = f"{(total_实际损耗 / total_加工量):.2%}"

    total_row = pd.DataFrame({
        '分切机台': ['合计:'],
        '加工量': [round(total_加工量, 3)],
        '实际损耗': [round(total_实际损耗, 6)],
        '损耗率': [total_损耗率]
    })

    final_result = pd.concat([grouped, total_row], ignore_index=True)
    return final_result, total_加工量

# 处理上传文件
if uploaded_file:
    try:
        original_name = uploaded_file.name

        # 替换中文文件名为 "uploaded_file.csv"（模拟）
        if contains_chinese(original_name):
            st.info(f"📄 检测到中文文件名：{original_name}，已自动替换为 uploaded_file.csv 用于处理。")
            fake_name = "uploaded_file.csv"
        else:
            fake_name = original_name

        # 读取文件内容，不依赖真实文件名
        file_content = uploaded_file.getvalue().decode("utf-8-sig")
        df = pd.read_csv(StringIO(file_content))

        # 检查所需列
        required_cols = {'分切机台', '加工量', '实际损耗'}
        if not required_cols.issubset(df.columns):
            st.error(f"❌ 缺少必要的列: {required_cols}")
        else:
            report_df, total_volume = generate_machine_loss_report(df)

            st.success("✅ 损耗报表生成成功！")
            st.dataframe(report_df, use_container_width=True)

            # 判断是否达标
            if total_volume < DAILY_PRODUCTION_MIN:
                st.error(f"⚠️ 总加工量为 {total_volume:.2f} 吨，低于最低生产标准（{DAILY_PRODUCTION_MIN} 吨）！")
            else:
                st.success(f"✅ 总加工量为 {total_volume:.2f} 吨，达到生产标准。")

            # 下载报表
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                report_df.to_excel(writer, index=False, sheet_name="分切机台损耗")
            st.download_button(
                label="📥 下载 Excel 报表",
                data=output.getvalue(),
                file_name="分切机台损耗报表.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"❌ 文件处理出错：{e}")
