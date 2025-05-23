import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime

st.set_page_config(page_title="🚚 客户运费分摊工具", layout="centered")
st.title("🚛 客户运费分摊自动计算")

uploaded_file = st.file_uploader("📂 请上传包含【明细费用】的 Excel 文件", type=["xls", "xlsx"])

if uploaded_file:
    try:
        shipping_cost = pd.read_excel(uploaded_file, sheet_name='明细费用')
        shipping_cost['最大距离'] = shipping_cost['距离'].astype(str).str.extract(r'[–—-](\d+)').astype(float)
        shipping_cost['运费'] = shipping_cost.groupby('运费组')['运费'].transform('first')

        df = shipping_cost[
            shipping_cost['运费组'].notna() &
            shipping_cost['上车费B'] & 
            shipping_cost['款项类型'] & 
            shipping_cost['发货客户业务员'] &
            shipping_cost['运输路线'] & 
            shipping_cost['客户吨位'].notna() &
            shipping_cost['最大距离'].notna()
        ].copy()

        df['吨公里'] = df['客户吨位'] * df['最大距离']

        group_total = df.groupby('运费组').agg(
            总吨公里=('吨公里', 'sum'),
            总运费=('运费', 'max')
        ).reset_index()


        df = df.merge(group_total, on='运费组', how='left')

        df['客户分摊运费'] = (df['吨公里'] / df['总吨公里']) * df['总运费']
        df['客户分摊运费'] = df['客户分摊运费'].round(2)

        st.success("✅ 运费分摊计算成功！")
        st.dataframe(df[['运费组', '上车费B','款项类型', '发货客户业务员', '运输路线',
        '客户吨位', '最大距离', '吨公里', '总运费', '客户分摊运费']], use_container_width=True)

        today_str = datetime.now().strftime("%m%d")
        file_name = f"{today_str}_运费分摊结果.xlsx"


        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name="运费分摊结果")

        st.download_button(
            label="📥 下载结果 Excel",
            data=output.getvalue(),
            file_name=file_name,
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        st.error(f"❌ 文件处理出错：{e}")
