import streamlit as st
import pandas as pd
import os
from datetime import datetime

# ==========================================
# 1. 基础配置
# ==========================================
st.set_page_config(page_title="2025年ICNOC年终述职评分系统", layout="centered")
DATA_FILE = "scoring_results.csv"  # 结果保存的文件名

# ==========================================
# 2. 核心功能：权限名单 (已根据打分表内置)
# ==========================================
# 这里的逻辑是：左边是“谁来打分”，右边是“他能给谁打分”
# 只要改这里，就能控制权限，不需要额外的 Excel/CSV 文件

# 定义两组候选人，方便后面组合
GROUP_1 = ["曲博", "陈绮霞"]
GROUP_2 = ["张远", "任思聪", "楚红涛", "王锡仕", "张赟", "林武隽", "韩慧", "贾育"]

VOTER_PERMISSIONS = {
    # --- 领导层 ---
    "段冰": GROUP_1 + GROUP_2,  # 打所有人
    "刘颖": GROUP_1,            # 只打第一组
    "邓子悟": GROUP_1,          # 只打第一组
    "张学兵": GROUP_2,          # 只打第二组
    "孙维涛": GROUP_2,          # 只打第二组

    # --- 互相打分 (互斥逻辑) ---
    "曲博": ["陈绮霞"],
    "陈绮霞": ["曲博"],
    
    # --- 中心主任互评 (打除了自己以外的 GROUP_2 成员) ---
    "张远":   [p for p in GROUP_2 if p != "张远"],
    "任思聪": [p for p in GROUP_2 if p != "任思聪"],
    "楚红涛": [p for p in GROUP_2 if p != "楚红涛"],
    "张赟":   [p for p in GROUP_2 if p != "张赟"],
    "林武隽": [p for p in GROUP_2 if p != "林武隽"],
    "韩慧":   [p for p in GROUP_2 if p != "韩慧"],
    "贾育":   [p for p in GROUP_2 if p != "贾育"],
}

# ==========================================
# 3. 评分标准定义
# ==========================================
CRITERIA = [
    {"category": "工作业绩", "item": "目标达成 (30分)", "desc": "工作目标明确，计划性强，成果达到预期。", "max_score": 30, "guide": "27-30: 优秀 | 23-26: 良好 | 19-22: 基础 | 0-18: 待改进"},
    {"category": "工作能力", "item": "创新能力 (15分)", "desc": "勇于开拓创新，提出新思路、新方法，解决问题。", "max_score": 15, "guide": "14-15: 优秀 | 12-13: 良好 | 10-11: 基础 | 0-9: 待改进"},
    {"category": "工作能力", "item": "执行能力 (15分)", "desc": "执行力强，抗压能力强，勇于攻坚克难。", "max_score": 15, "guide": "14-15: 优秀 | 12-13: 良好 | 10-11: 基础 | 0-9: 待改进"},
    {"category": "工作能力", "item": "协作配合 (10分)", "desc": "具有大局观，善于倾听，协调各方推动工作。", "max_score": 10, "guide": "9-10: 优秀 | 7-8: 良好 | 5-6: 基础 | 0-4: 待改进"},
    {"category": "管理及业务能力", "item": "团队领导能力 (20分)", "desc": "调动员工积极性，提升团队凝聚力，重视梯队建设。", "max_score": 20, "guide": "18-20: 优秀 | 15-17: 良好 | 13-14: 基础 | 0-12: 待改进"},
    {"category": "管理及业务能力", "item": "岗位技术/业务能力 (10分)", "desc": "具备专业知识，能想明白、说明白、干明白。", "max_score": 10, "guide": "9-10: 优秀 | 7-8: 良好 | 5-6: 基础 | 0-4: 待改进"}
]

# ==========================================
# 4. 页面主体逻辑
# ==========================================
st.title("📊 2025年ICNOC年终述职评分")
st.markdown("---")

# --- 第一步：身份验证 ---
st.subheader("1. 身份验证")
col1, col2 = st.columns(2)
with col1:
    # strip() 去除前后空格，防止输入习惯差异
    input_name = st.text_input("请输入您的姓名", placeholder="与述职安排表一致").strip()
with col2:
    input_phone = st.text_input("请输入您的电话", placeholder="用于身份核实")

# 检查是否有权限
current_voter_candidates = []
if input_name:
    if input_name in VOTER_PERMISSIONS:
        current_voter_candidates = VOTER_PERMISSIONS[input_name]
        st.success(f"✅ 欢迎您，{input_name}。您需要为 {len(current_voter_candidates)} 位述职人员评分。")
    else:
        st.error("❌ 系统未找到您的评分权限，请核对姓名（不需要输入部门职务）。")

# --- 第二步：选择与评分 ---
if current_voter_candidates and input_phone:
    st.markdown("---")
    st.subheader("2. 评分操作")
    
    # 读取已完成记录，避免重复
    finished_candidates = []
    if os.path.exists(DATA_FILE):
        try:
            df_exist = pd.read_csv(DATA_FILE)
            if "评分人姓名" in df_exist.columns and "被考评人" in df_exist.columns:
                finished_candidates = df_exist[
                    (df_exist["评分人姓名"] == input_name) & 
                    (df_exist["评分人电话"] == input_phone)
                ]["被考评人"].tolist()
        except:
            pass 

    # 生成下拉选项
    options_display = []
    for c in current_voter_candidates:
        if c in finished_candidates:
            options_display.append(f"{c} (✅已完成)")
        else:
            options_display.append(c)

    selected_option = st.selectbox("请选择被考评人", options_display)
    
    # 提取真实名字
    candidate = selected_option.split(" (")[0]
    
    if "✅已完成" in selected_option:
        st.warning(f"⚠️ 您已经为 {candidate} 打过分了，再次提交将作为新记录保存。")
    else:
        st.info(f"当前正在为 **{candidate}** 进行打分。")

    # 评分表单
    with st.form("scoring_form"):
        scores = {}
        total_score = 0
        
        for criterion in CRITERIA:
            st.markdown(f"#### {criterion['category']} - {criterion['item']}")
            st.caption(f"📝 标准：{criterion['desc']}")
            st.caption(f"ℹ️ 参考：{criterion['guide']}")
            
            score = st.slider(
                f"评分",
                min_value=0,
                max_value=criterion['max_score'],
                value=int(criterion['max_score'] * 0.9),
                key=f"{candidate}_{criterion['item']}" # 使用唯一key防止切换人时滑块不重置
            )
            scores[criterion['item']] = score
            total_score += score
            st.markdown("---")
        
        remarks = st.text_area("备注/评语", placeholder="可选填...")
        
        submitted = st.form_submit_button("提交评分", type="primary")
        
        if submitted:
            record = {
                "提交时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "评分人姓名": input_name,
                "评分人电话": input_phone,
                "被考评人": candidate,
                **scores,
                "总分": total_score,
                "备注": remarks
            }
            
            df_new = pd.DataFrame([record])
            
            # 保存逻辑
            if not os.path.exists(DATA_FILE):
                df_new.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
            else:
                df_new.to_csv(DATA_FILE, mode='a', header=False, index=False, encoding='utf-8-sig')
            
            st.success(f"🎉 提交成功！{candidate} 的得分为 {total_score} 分。")
            st.info("请在上方下拉框选择下一位人员继续评分。")

elif input_name and input_name in VOTER_PERMISSIONS and not input_phone:
    st.warning("👉 请输入电话号码以继续。")

# ==========================================
# 5. 管理员后台 (简易版)
# ==========================================
st.markdown("---")
with st.expander("🔐 管理员后台"):
    password = st.text_input("管理员密码", type="password")
    if password == "123456": # 修改此处的 123456 为你想要的密码
        if os.path.exists(DATA_FILE):
            df_result = pd.read_csv(DATA_FILE)
            st.write(f"共收集到 {len(df_result)} 条数据")
            st.dataframe(df_result)
            
            csv = df_result.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                "📥 下载评分结果",
                csv,
                f'ICNOC_评分结果_{datetime.now().strftime("%Y%m%d")}.csv',
                'text/csv'
            )
        else:
            st.write("暂无数据")
