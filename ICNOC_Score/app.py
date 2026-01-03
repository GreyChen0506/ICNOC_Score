import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- 页面配置 ---
st.set_page_config(page_title="2025年ICNOC年终述职评分系统", layout="centered")

# --- 文件路径配置 ---
DATA_FILE = "scoring_results.csv"      # 评分结果保存文件
RELATION_FILE = "relationship.csv"     # 权限关系配置文件

# --- 评分标准数据 (保持不变) ---
CRITERIA = [
    {"category": "工作业绩", "item": "目标达成 (30分)", "desc": "工作目标明确，计划性强，成果达到预期。", "max_score": 30, "guide": "27-30: 优秀 | 23-26: 良好 | 19-22: 基础 | 0-18: 待改进"},
    {"category": "工作能力", "item": "创新能力 (15分)", "desc": "勇于开拓创新，提出新思路、新方法，解决问题。", "max_score": 15, "guide": "14-15: 优秀 | 12-13: 良好 | 10-11: 基础 | 0-9: 待改进"},
    {"category": "工作能力", "item": "执行能力 (15分)", "desc": "执行力强，抗压能力强，勇于攻坚克难。", "max_score": 15, "guide": "14-15: 优秀 | 12-13: 良好 | 10-11: 基础 | 0-9: 待改进"},
    {"category": "工作能力", "item": "协作配合 (10分)", "desc": "具有大局观，善于倾听，协调各方推动工作。", "max_score": 10, "guide": "9-10: 优秀 | 7-8: 良好 | 5-6: 基础 | 0-4: 待改进"},
    {"category": "管理及业务能力", "item": "团队领导能力 (20分)", "desc": "调动员工积极性，提升团队凝聚力，重视梯队建设。", "max_score": 20, "guide": "18-20: 优秀 | 15-17: 良好 | 13-14: 基础 | 0-12: 待改进"},
    {"category": "管理及业务能力", "item": "岗位技术/业务能力 (10分)", "desc": "具备专业知识，能想明白、说明白、干明白。", "max_score": 10, "guide": "9-10: 优秀 | 7-8: 良好 | 5-6: 基础 | 0-4: 待改进"}
]

# --- 核心函数：加载权限关系 ---
@st.cache_data
def load_voter_permissions():
    """读取 CSV 文件，生成 {打分人: [可打分的候选人列表]} 的字典"""
    if not os.path.exists(RELATION_FILE):
        return None, "未找到权限配置文件 relationship.csv"
    
    try:
        # 读取CSV，假设第一行是标题
        df = pd.read_csv(RELATION_FILE)
        
        # 1. 提取所有打分人（从第4列开始是打分人名字，即索引3）
        # 列名结构：ID, 被考评人, 职务, 段冰, 刘颖...
        voter_names = df.columns[3:].tolist()
        
        # 2. 构建权限字典
        permissions = {}
        for voter in voter_names:
            # 找到该列中标记为 √ 或 1 的行
            # fillna('') 防止空值报错，astype(str) 统一转字符串比较
            valid_rows = df[df[voter].fillna('').astype(str).str.contains('√|1', na=False)]
            # 获取这些行的“被考评人”列
            candidates = valid_rows['被考评人'].tolist()
            if candidates:
                permissions[voter.strip()] = candidates
                
        return permissions, None
    except Exception as e:
        return None, f"读取配置文件出错: {str(e)}"

# --- 加载数据 ---
permissions_map, error_msg = load_voter_permissions()

# --- 界面开始 ---
st.title("📊 2025年ICNOC年终述职评分")

if error_msg:
    st.error(f"⚠️ 系统配置错误: {error_msg}")
    st.stop()

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
    if input_name in permissions_map:
        current_voter_candidates = permissions_map[input_name]
        st.success(f"✅ 欢迎您，{input_name}。您共有 {len(current_voter_candidates)} 位述职人员需要评分。")
    else:
        st.error("❌ 系统未找到您的评分权限，请核对姓名（不需要输入部门职务）。")

# --- 第二步：选择与评分 ---
# 只有名字验证通过才显示后续内容
if current_voter_candidates and input_phone:
    st.markdown("---")
    st.subheader("2. 评分操作")
    
    # 过滤掉已经打过分的人（可选优化，这里暂不做，防止想要修改分数）
    candidate = st.selectbox("请选择被考评人 (仅显示您有权评分的人员)", current_voter_candidates)
    
    st.info(f"当前正在为 **{candidate}** 进行打分。")

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
            st.info("您可以继续在上方下拉框选择下一位人员进行评分。")

elif input_name and input_name in permissions_map and not input_phone:
    st.warning("👉 请输入电话号码以继续。")

# --- 管理员后台 (代码保持不变) ---
st.markdown("---")
with st.expander("🔐 管理员后台 (点击展开)"):
    password = st.text_input("管理员密码", type="password")
    if password == "123456": 
        if os.path.exists(DATA_FILE):
            df_result = pd.read_csv(DATA_FILE)
            st.write(f"共收集到 {len(df_result)} 条数据")
            st.dataframe(df_result)
            
            csv = df_result.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                "📥 下载评分结果",
                csv,
                f'评分结果_{datetime.now().strftime("%Y%m%d")}.csv',
                'text/csv'
            )
        else:
            st.write("暂无数据")
