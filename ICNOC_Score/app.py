import streamlit as st
import pandas as pd
import os
from datetime import datetime

# ==========================================
# 1. 基础配置
# ==========================================
st.set_page_config(page_title="2025年年终述职评分系统", layout="centered")
DATA_FILE = "scoring_results.csv"  # 结果保存的文件名

# ==========================================
# 2. 数据定义 (完全基于图片矩阵关系)
# ==========================================

# --- A. 述职候选人名单 (行：被打分的人) ---
# 第1组 (1-2号)
CANDIDATES_GROUP_1 = ["曲博", "陈绮霞"]

# 第2组 (3-15号，补全了图片底部的人员)
CANDIDATES_GROUP_2 = [
    "张远", "任思聪", "楚红涛", "王锡仕", "张赟", 
    "林武隽", "韩慧", "贾育", "时晓鹏", "张妍", 
    "谭雪洁", "李雨翔", "张萌"
]

# 所有候选人汇总
ALL_CANDIDATES = CANDIDATES_GROUP_1 + CANDIDATES_GROUP_2

# --- B. 部门列表 (保持不变或按需修改) ---
DEPARTMENTS = [
    "云网综合运营管理部", "属地服务与支撑发展部", "资源调度优化中心", 
    "移动业务保障中心", "云网指挥调度中心", "绿色节能运营中心", 
    "核心网和平台保障中心", "安全运营中心", "云网数字化开发式运营中心", 
    "基础业务保障中心", "其他部门"
]

# --- C. 领导/专家权限字典 (列：打分人员 -> 可打分范围) ---
# 逻辑说明：Key=打分人姓名, Value=他需要打分的人员列表
LEADER_PERMISSIONS = {}

# 1. 通用规则：段冰 (打所有人)
LEADER_PERMISSIONS["段冰"] = ALL_CANDIDATES

# 2. 第1组评审：刘颖, 邓子悟 (只打第1组)
for name in ["刘颖", "邓子悟"]:
    LEADER_PERMISSIONS[name] = CANDIDATES_GROUP_1

# 3. 第1组互评：曲博 <-> 陈绮霞 (打第1组，排除自己)
LEADER_PERMISSIONS["曲博"] = ["陈绮霞"]
LEADER_PERMISSIONS["陈绮霞"] = ["曲博"]

# 4. 第2组评审团 (根据图片列头定义)
# 这些人负责给 CANDIDATES_GROUP_2 打分
# 名单来源：图片右侧列头
GROUP_2_SCORERS = [
    "张学兵", "孙维涛", "张远", "任思聪", "楚红涛", 
    "张赟", "林武隽", "韩慧", "贾育"
]

for scorer in GROUP_2_SCORERS:
    # 逻辑：打分范围是 Group 2 全员，但必须排除自己
    target_list = [p for p in CANDIDATES_GROUP_2 if p != scorer]
    LEADER_PERMISSIONS[scorer] = target_list

# ==========================================
# 3. 评分标准
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
# 4. 页面逻辑
# ==========================================
st.title("📊 2025年年终述职评分")
st.markdown("---")

# --- 第一步：角色选择 (已修改标题) ---
role = st.radio("请选择您的身份：", ("部门经理/总监", "普通员工"), horizontal=True)

# 初始化变量
valid_user = False
available_candidates = []
user_dept = ""

# --- 第二步：信息录入 (根据角色变化) ---
st.subheader("1. 身份信息录入")
col1, col2 = st.columns(2)

with col1:
    input_name = st.text_input("您的姓名", placeholder="请输入真实姓名").strip()

with col2:
    input_phone = st.text_input("联系电话", placeholder="请输入手机号")

# 逻辑分支
if role == "部门经理/总监": # 这里对应修改
    if input_name:
        if input_name in LEADER_PERMISSIONS:
            valid_user = True
            available_candidates = LEADER_PERMISSIONS[input_name]
            user_dept = "部门经理/总监" # 默认部门
            st.success(f"✅ 身份验证通过：{input_name}。您需要为 {len(available_candidates)} 位人员评分。")
        else:
            # 提示修改
            st.error("❌ 未在评分名单中找到您的名字。如果您不是列表中的指定评委（段冰、刘颖、邓子悟、曲博、陈绮霞、张学兵等），请切换为“普通员工”身份。")
            
else: # 普通员工
    # 普通员工需要选择部门
    user_dept = st.selectbox("请选择您所在的部门", DEPARTMENTS)
    if input_name:
        valid_user = True
        available_candidates = ALL_CANDIDATES # 员工可以给所有人打分
        st.info(f"👋 欢迎您，{input_name}。您可以对述职人员进行打分。")

# --- 第三步：打分操作 ---
if valid_user and input_phone:
    st.markdown("---")
    st.subheader("2. 评分操作")
    
    # 1. 先进行查重和名单逻辑
    finished_candidates = []
    if os.path.exists(DATA_FILE):
        try:
            df_exist = pd.read_csv(DATA_FILE)
            if "评分人姓名" in df_exist.columns and "评分人电话" in df_exist.columns:
                finished_candidates = df_exist[
                    (df_exist["评分人姓名"] == input_name) & 
                    (df_exist["评分人电话"] == input_phone)
                ]["被考评人"].tolist()
        except:
            pass 

    # 2. 渲染下拉框
    options_display = []
    if not available_candidates:
        st.warning("当前没有分配给您的评分任务。")
    else:
        for c in available_candidates:
            if c in finished_candidates:
                options_display.append(f"{c} (✅已完成)")
            else:
                options_display.append(c)

        selected_option = st.selectbox("请选择被考评人", options_display)
        
        if selected_option:
            candidate = selected_option.split(" (")[0]
            
            if "✅已完成" in selected_option:
                st.warning(f"⚠️ 您已提交过对 {candidate} 的评分，再次提交将覆盖或新增记录。")
            
            # 3. 渲染表单
            with st.form("scoring_form"):
                st.markdown(f"**正在为【{candidate}】打分**")
                scores = {}
                total_score = 0
                
                for criterion in CRITERIA:
                    st.markdown(f"**{criterion['item']}**")
                    st.caption(f"标准：{criterion['desc']} | 参考：{criterion['guide']}")
                    score = st.slider(
                        "得分", 0, criterion['max_score'], int(criterion['max_score'] * 0.9),
                        key=f"{candidate}_{criterion['item']}_{role}" 
                    )
                    scores[criterion['item']] = score
                    total_score += score
                    st.divider()
                
                remarks = st.text_area("备注/建议", placeholder="请输入您的评价...")
                
                # 按钮位于表单最下方
                submitted = st.form_submit_button("提交评分", type="primary", use_container_width=True)
                
                if submitted:
                    record = {
                        "提交时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "身份类型": role,
                        "评分人部门": user_dept,
                        "评分人姓名": input_name,
                        "评分人电话": input_phone,
                        "被考评人": candidate,
                        **scores,
                        "总分": total_score,
                        "备注": remarks
                    }
                    
                    df_new = pd.DataFrame([record])
                    
                    if not os.path.exists(DATA_FILE):
                        df_new.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
                    else:
                        df_new.to_csv(DATA_FILE, mode='a', header=False, index=False, encoding='utf-8-sig')
                    
                    # 将消息存入 session state
                    st.session_state['success_msg'] = f"🎉 提交成功！【{candidate}】总分：{total_score}。请继续为下一位评分。"
                    
                    # 刷新页面
                    st.rerun()

            # 4. 【关键修改】在表单(with st.form)结束后，检查并显示消息
            # 这样消息就会出现在提交按钮的视觉下方
            if 'success_msg' in st.session_state and st.session_state['success_msg']:
                st.success(st.session_state['success_msg'])
                st.session_state['success_msg'] = None # 显示一次后清除

elif valid_user and not input_phone:
    st.warning("👉 请输入电话号码以开启评分区域。")
    
# 5. 管理员后台
# ==========================================
st.markdown("---")
with st.expander("🔐 管理员后台"):
    password = st.text_input("管理员密码", type="password")
    if password == "123456": 
        if os.path.exists(DATA_FILE):
            df_result = pd.read_csv(DATA_FILE)
            st.write(f"📊 数据预览 (共 {len(df_result)} 条)")
            st.dataframe(df_result)
            
            csv = df_result.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                "📥 下载完整数据表",
                csv,
                f'述职评分结果_{datetime.now().strftime("%Y%m%d")}.csv',
                'text/csv'
            )
        else:
            st.info("暂无数据")
