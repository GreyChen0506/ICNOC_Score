import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- 页面配置 ---
st.set_page_config(page_title="2025年ICNOC年终述职评分系统", layout="centered")

# --- 文件保存路径 ---
DATA_FILE = "scoring_results.csv"

# --- 评分标准数据 (源自Word文档) ---
CRITERIA = [
    {
        "category": "工作业绩",
        "item": "目标达成 (30分)",
        "desc": "工作目标明确，计划性强，成果达到预期。",
        "max_score": 30,
        "guide": "27-30: 优秀 | 23-26: 良好 | 19-22: 基础 | 0-18: 待改进"
    },
    {
        "category": "工作能力",
        "item": "创新能力 (15分)",
        "desc": "勇于开拓创新，提出新思路、新方法，解决问题。",
        "max_score": 15,
        "guide": "14-15: 优秀 | 12-13: 良好 | 10-11: 基础 | 0-9: 待改进"
    },
    {
        "category": "工作能力",
        "item": "执行能力 (15分)",
        "desc": "执行力强，抗压能力强，勇于攻坚克难。",
        "max_score": 15,
        "guide": "14-15: 优秀 | 12-13: 良好 | 10-11: 基础 | 0-9: 待改进"
    },
    {
        "category": "工作能力",
        "item": "协作配合 (10分)",
        "desc": "具有大局观，善于倾听，协调各方推动工作。",
        "max_score": 10,
        "guide": "9-10: 优秀 | 7-8: 良好 | 5-6: 基础 | 0-4: 待改进"
    },
    {
        "category": "管理及业务能力",
        "item": "团队领导能力 (20分)",
        "desc": "调动员工积极性，提升团队凝聚力，重视梯队建设。",
        "max_score": 20,
        "guide": "18-20: 优秀 | 15-17: 良好 | 13-14: 基础 | 0-12: 待改进"
    },
    {
        "category": "管理及业务能力",
        "item": "岗位技术/业务能力 (10分)",
        "desc": "具备专业知识，能想明白、说明白、干明白。",
        "max_score": 10,
        "guide": "9-10: 优秀 | 7-8: 良好 | 5-6: 基础 | 0-4: 待改进"
    }
]

# --- 标题 ---
st.title("📊 2025年ICNOC年终述职评分")
st.markdown("---")

# --- 第一步：实名登录信息 ---
st.subheader("1. 评分人信息登记")
col1, col2 = st.columns(2)
with col1:
    voter_name = st.text_input("您的姓名", placeholder="请输入真实姓名")
with col2:
    voter_phone = st.text_input("联系电话", placeholder="请输入手机号")

# --- 第二步：选择被考评人 ---
st.subheader("2. 选择被考评对象")
# 这里可以根据需要添加更多人名
candidate_list = ["楚红涛", "待定候选人A", "待定候选人B"] 
candidate = st.selectbox("请选择被考评人", candidate_list)

st.info(f"当前正在为 **{candidate}** 进行打分。")

# --- 第三步：开始打分 ---
if voter_name and voter_phone:
    st.markdown("---")
    st.subheader("3. 评分详情")
    
    scores = {}
    total_score = 0
    
    with st.form("scoring_form"):
        for criterion in CRITERIA:
            st.markdown(f"#### {criterion['category']} - {criterion['item']}")
            st.caption(f"📝 标准：{criterion['desc']}")
            st.caption(f"ℹ️ 参考：{criterion['guide']}")
            
            # 使用滑块打分，移动端体验好
            score = st.slider(
                f"请为【{criterion['item']}】打分",
                min_value=0,
                max_value=criterion['max_score'],
                value=int(criterion['max_score'] * 0.8), # 默认给个80%的分数
                key=criterion['item']
            )
            scores[criterion['item']] = score
            total_score += score
            st.markdown("---")
        
        # --- 备注信息 ---
        remarks = st.text_area("备注/评语 (可选)", placeholder="请输入具体的评价或建议...")
        
        # --- 提交按钮 ---
        submitted = st.form_submit_button("提交评分", type="primary")
        
        if submitted:
            # 记录数据
            record = {
                "提交时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "评分人姓名": voter_name,
                "评分人电话": voter_phone,
                "被考评人": candidate,
                **scores,
                "总分": total_score,
                "备注": remarks
            }
            
            df_new = pd.DataFrame([record])
            
            # 保存到CSV
            if not os.path.exists(DATA_FILE):
                df_new.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
            else:
                df_new.to_csv(DATA_FILE, mode='a', header=False, index=False, encoding='utf-8-sig')
            
            st.success(f"提交成功！{candidate} 的总分为：{total_score} 分。")
            st.balloons()
            
else:
    st.warning("⚠️ 请先在上方填写您的姓名和电话，即可开始打分。")

# --- (可选) 管理员查看数据区域 ---
# st.markdown("---")
# if st.checkbox("查看后台数据 (管理员)"):
#     if os.path.exists(DATA_FILE):
#         st.dataframe(pd.read_csv(DATA_FILE))
#     else:
#         st.write("暂无数据")