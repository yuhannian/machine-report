import streamlit as st
import pandas as pd
from io import BytesIO, StringIO
from datetime import datetime

DAILY_PRODUCTION_MIN = 50

st.set_page_config(page_title="分切机台损耗报表", layout="centered")
st.title("📊 分切机台日损耗报表生成器")

uploaded_file = st.file_uploader(
    "📂 请上传发货数据 CSV 或 Excel 文件（必须包含：分切机台，加工量，实际损耗）",
    type=["csv", "xlsx"]
)

def read_file_flexibly(uploaded_file):
    file_name = uploaded_file.name.lower()

    if file_name.endswith(".csv"):
        try:
            content = uploaded_file.getvalue().decode('utf-8-sig')
            return pd.read_csv(StringIO(content)), "csv（utf-8）"
        except UnicodeDecodeError:
            try:
                content = uploaded_file.getvalue().decode('gbk')
                st.info("📄 检测到 GBK 编码，已自动转换。")
                return pd.read_csv(StringIO(content)), "csv（gbk）"
            except Exception as e:
                st.error(f"❌ CSV 文件读取失败：{e}")
                st.stop()

    elif file_name.endswith(".xlsx"):
        try:
            return pd.read_excel(uploaded_file), "excel"
        except Exception as e:
            st.error(f"❌ Excel 文件读取失败：{e}")
            st.stop()

    else:
        st.error("❌ 不支持的文件格式。请上传 .csv 或 .xlsx 文件。")
        st.stop()

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
        df, source_type = read_file_flexibly(uploaded_file)
        st.success(f"✅ 文件读取成功（类型：{source_type}）")

        required_cols = {'分切机台', '加工量', '实际损耗'}
        if not required_cols.issubset(df.columns):
            st.error(f"❌ 文件缺少以下必要列：{required_cols - set(df.columns)}")
        else:
            report_df, total_volume = generate_machine_loss_report(df)

            st.success("✅ 损耗报表生成成功！")
            st.dataframe(report_df, use_container_width=True)

            if total_volume < DAILY_PRODUCTION_MIN:
                st.error(f"⚠️ 总加工量为 {total_volume:.2f} 吨，低于最低生产标准（{DAILY_PRODUCTION_MIN} 吨）！")
            else:
                st.success(f"✅ 总加工量为 {total_volume:.2f} 吨，达到生产标准。")

            today_str = datetime.now().strftime("%m%d")
            file_name = f"{today_str}_分切机台损耗报表.xlsx"

            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                report_df.to_excel(writer, index=False, sheet_name="分切机台损耗")

            st.download_button(
                label="📥 下载 Excel 报表",
                data=output.getvalue(),
                file_name=file_name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"❌ 读取或处理文件出错：{e}")
