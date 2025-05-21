import streamlit as st
import pandas as pd

def sales_report(df):
    pivot = pd.pivot_table(
        df,
        index=['商品', '品名', '品牌'],
        columns='业务员',
        values='数量',
        aggfunc='sum',
        fill_value=0
    )
    pivot['合计'] = pivot.sum(axis=1)
    total_row = pivot.sum(axis=0)
    total_row.name = ('合计', '', '')
    final = pd.concat([pivot, pd.DataFrame([total_row])])
    return final.reset_index()

st.title("📊 销售报表自动生成工具")

uploaded_file = st.file_uploader("请上传CSV格式的发货数据", type="csv")

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)

        # Check required columns
        required_cols = {'商品', '品名', '品牌', '业务员', '数量'}
        if not required_cols.issubset(df.columns):
            st.error(f"文件缺少必要的列: {required_cols}")
        else:
            report = sales_report(df)
            st.success("✅ 销售报表生成成功！")
            st.dataframe(report, use_container_width=True)

            # Download as Excel
            from io import BytesIO
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                report.to_excel(writer, index=False, sheet_name='销售汇总')
            st.download_button("📥 下载报表为 Excel", data=output.getvalue(), file_name="销售汇总.xlsx", mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        st.error(f"❌ 出错了: {e}")
