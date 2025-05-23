import streamlit as st
import pandas as pd
from io import BytesIO, StringIO
from datetime import datetime



st.set_page_config(page_title="销售+毛利报表自动生成工具", layout="centered")
st.title("📊 销售+毛利自动生成工具")

uploaded_file = st.file_uploader("📂 请上传 CSV 或 Excel 格式的发货数据", type=["csv", "xlsx"])

def gross_profit_report(df):
    pivot = pd.pivot_table(
        df,
        index=['商品级次', '商品', '末级分类'],
        columns='业务员',
        values=['销售金额', '净毛利'],
        aggfunc='sum',
        fill_value=0
    )

    pivot['销售金额合计'] = pivot['销售金额'].sum(axis=1)
    pivot['净毛利合计'] = pivot['净毛利'].sum(axis=1)
    total_row = pivot.sum(axis=0)
    total_row.name = ('合计', '', '')
    final = pd.concat([pivot, pd.DataFrame([total_row])])
    final = final.reset_index()
    final.columns.values[0:3] = ['二级分类', '一级分类', '末级分类']

    return final


def read_file_flexibly(uploaded_file):
    file_name = uploaded_file.name.lower()

    if file_name.endswith(".csv"):
        try:
            content = uploaded_file.getvalue().decode('utf-8-sig')
            return pd.read_csv(StringIO(content)), "csv（utf-8）"
        except UnicodeDecodeError:
            try:
                content = uploaded_file.getvalue().decode('gbk')
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
        st.error("❌ 不支持的文件格式，请上传 .csv 或 .xlsx 文件。")
        st.stop()

if uploaded_file:
    try:
        df, file_type = read_file_flexibly(uploaded_file)

        if '商品描述' in df.columns:
            df['末级分类'] = df['商品描述'].str.split('-').str[0]
        else:
            st.error("❌ 缺少商品描述列，无法提取末级分类。")
            st.stop()

        st.success(f"✅ 文件读取成功（类型：{file_type}）")

        required_cols = {'商品', '品名', '品牌', '业务员', '数量'}
        if not required_cols.issubset(df.columns):
            st.error(f"❌ 文件缺少以下必要列：{required_cols - set(df.columns)}")
        else:
            report = sales_report(df)
            st.success("✅ 销售毛利报表生成成功！")
            st.dataframe(report, use_container_width=True)
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                report.to_excel(writer, index=False, sheet_name='销售汇总')
            today_str = datetime.now().strftime("%m%d") 
            file_name = f"{today_str}_销售毛利.xlsx"
            st.download_button(
                label="📥 下载报表为 Excel",
                data=output.getvalue(),
                file_name=file_name,
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )

    except Exception as e:
        st.error(f"❌ 报表生成失败：{e}")
