import streamlit as st
import pandas as pd
from io import BytesIO

# Set daily production minimum
DAILY_PRODUCTION_MIN = 50

st.set_page_config(page_title="分切机台损耗报表", layout="centered")
st.title("📊 分切机台日损耗报表生成器")

uploaded_file = st.file_uploader("请上传发货数据 CSV 文件（必须包含：分切机台，加工量，实际损耗）", type="csv")

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

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file, encoding='utf-8-sig')

        # Validate necessary columns
        required_cols = {'分切机台', '加工量', '实际损耗'}
        if not required_cols.issubset(df.columns):
            st.error(f"❌ 缺少必要的列: {required_cols}")
        else:
            report_df, total_volume = generate_machine_loss_report(df)

            st.success("✅ 损耗报表生成成功！")
            st.dataframe(report_df, use_container_width=True)

            # Check production threshold
            if total_volume < DAILY_PRODUCTION_MIN:
                st.error(f"⚠️ 总加工量为 {total_volume:.2f} 吨，低于最低生产标准（{DAILY_PRODUCTION_MIN} 吨）！")
            else:
                st.success(f"✅ 总加工量为 {total_volume:.2f} 吨，达到生产标准。")

            # Excel export
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
        st.error(f"❌ 读取或处理文件出错: {e}")
