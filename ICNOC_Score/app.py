import streamlit as st
import pandas as pd
import os
from datetime import datetime

# ==========================================
# 1. 基础配置
# ==========================================
st.set_page_config(page_title="2025年终述职评分", layout="centered")
DATA_FILE = "scoring_results.csv"

# ==========================================
# 2. 数据定义
# ==========================================

# --- A. 排序主名单 ---
MASTER_ORDER = [
    "刘颖", "邓子悟", "曲博", "陈绮霞", "张学兵", 
    "孙维涛", "张妍", "张远", "任思聪", "楚红涛", 
    "王锡仕", "张赟", "林武隽", "韩慧", "贾育", 
    "时晓鹏", "谭雪洁", "李雨翔", "张萌"
]

# --- B. 述职候选人分组 ---
CANDIDATES_GROUP_1 = ["曲博", "陈绮霞"]
CANDIDATES_GROUP_2 = [
    "张远", "任思聪", "楚红涛", "王锡仕", "张赟", 
    "林武隽", "韩慧", "贾育", "时晓鹏", "张妍", 
    "谭雪洁", "李雨翔", "张萌"
]
ALL_CANDIDATES = list(set(CANDIDATES_GROUP_1 + CANDIDATES_GROUP_2 + MASTER_ORDER))

# --- C. 部门列表 (作为下拉选项) ---
DEPARTMENTS = [
    "云网综合运营管理部", 
    "属地服务与支撑发展部", 
    "资源调度优化中心", 
    "移动业务保障中心", 
    "云网指挥调度中心", 
    "绿色节能运营中心", 
    "核心网和平台保障中心", 
    "安全运营中心", 
    "云网数字化开发式运营中心", 
    "基础业务保障中心", 
    "ICNOC/云网运营部", 
    "其他部门" # 只有选择这个才可以看到所有人
]

# --- D. 部门-人员映射表 (新增功能核心) ---
# 根据图片内容整理，用于限制普通员工的打分范围
DEPT_LEADER_MAPPING = {
    "云网综合运营管理部": ["曲博"],
    "属地服务与支撑发展部": ["陈绮霞"],
    "资源调度优化中心": ["张远", "谭雪洁"],
    "移动业务保障中心": ["任思聪", "李雨翔", "张萌"],
    "云网指挥调度中心": ["楚红涛"],
    "绿色节能运营中心": ["王锡仕", "林武隽"],
    "核心网和平台保障中心": ["张赟"],
    "安全运营中心": ["韩慧"],
    "云网数字化开发式运营中心": ["贾育"],
    "基础业务保障中心": ["孙维涛", "时晓鹏", "张妍"], # 图片中孙维涛兼任该中心总监
    "ICNOC/云网运营部": ["刘颖", "邓子悟", "张学兵"] # 图片中未明确归属具体中心的领导
}

# --- E. 领导/专家权限字典 ---
LEADER_PERMISSIONS = {}
LEADER_PERMISSIONS["段冰"] = ALL_CANDIDATES
for name in ["刘颖", "邓子悟"]:
    LEADER_PERMISSIONS[name] = CANDIDATES_GROUP_1
LEADER_PERMISSIONS["曲博"] = ["陈绮霞"]
LEADER_PERMISSIONS["陈绮霞"] = ["曲博"]

GROUP_2_SCORERS = [
    "张学兵", "孙维涛", "张远", "任思聪", "楚红涛", 
    "张赟", "林武隽", "韩慧", "贾育"
]
for scorer in GROUP_2_SCORERS:
    target_list = [p for p in CANDIDATES_GROUP_2 if p != scorer]
    LEADER_PERMISSIONS[scorer] = target_list

# ==========================================
# 3. 评分标准
# ==========================================
CRITERIA = [
    {
        "category": "工作业绩", "item": "目标达成 (40分)", 
        "desc": "工作目标明确，具有良好的计划性与前瞻性，全年工作有序推进，工作成果达到年度预期。", 
        "max_score": 40, "guide": "34-40: 优秀 | 27-33: 良好 | 21-26: 基础水平 | 0-20: 待改进"
    },
    {
        "category": "工作能力", "item": "创新能力 (10分)", 
        "desc": "勇于开拓创新，在工作中能够提出新的思路、方法，利用新的工具提升管理水平，以创造性、突破性的方式解决工作中的问题。", 
        "max_score": 10, "guide": "9-10: 优秀 | 7-8: 良好 | 5-6: 基础水平 | 0-4: 待改进"
    },
    {
        "category": "工作能力", "item": "执行能力 (10分)", 
        "desc": "工作执行力强，有较强的承压能力。勇于攻坚克难，能克服各种困难，积极灵活寻求解决办法，坚持不懈达成目标。", 
        "max_score": 10, "guide": "9-10: 优秀 | 7-8: 良好 | 5-6: 基础水平 | 0-4: 待改进"
    },
    {
        "category": "工作能力", "item": "协作配合 (10分)", 
        "desc": "具有大局观，善于倾听和换位思考，能够建立融洽的上下级关系和内外部工作联系；能够克服障碍因素、有效协条各方，推动工作高效开展。", 
        "max_score": 10, "guide": "9-10: 优秀 | 7-8: 良好 | 5-6: 基础水平 | 0-4: 待改进"
    },
    {
        "category": "管理及业务能力", "item": "团队领导能力 (20分)", 
        "desc": "有较强的基础管理能力，能够发挥部门员工长处，充分调动员工积极性，营造良好工作氛围，持续提升团队凝聚力。高度重视人员梯队建设。", 
        "max_score": 20, "guide": "18-20: 优秀 | 15-17: 良好 | 13-14: 基础水平 | 0-12: 待改进"
    },
    {
        "category": "管理及业务能力", "item": "岗位技术/业务能力 (10分)", 
        "desc": "具备符合工作要求所应具备的专业知识、岗位技能，具有较强的学习能力。开展工作能够“想明白、说明白、干明白”。", 
        "max_score": 10, "guide": "9-10: 优秀 | 7-8: 良好 | 5-6: 基础水平 | 0-4: 待改进"
    }
]

# ==========================================
# 4. 页面逻辑
# ==========================================
st.title("📊 2025年ICNOC年终述职评分")
st.markdown("---")

# --- 第一步：角色选择 ---
role = st.radio("请选择您的身份：", ("部门经理/总监", "普通员工"), horizontal=True)

valid_user = False
available_candidates = []
user_dept = ""

# --- 第二步：信息录入 ---
st.subheader("1. 身份信息录入")
col1, col2 = st.columns(2)

with col1:
    input_name = st.text_input("您的姓名", placeholder="请输入真实姓名").strip()
with col2:
    input_phone = st.text_input("联系电话", placeholder="请输入手机号")

# 逻辑分支
if role == "部门经理/总监":
    if input_name:
        if input_name in LEADER_PERMISSIONS:
            valid_user = True
            available_candidates = LEADER_PERMISSIONS[input_name]
            user_dept = "部门经理/总监"
            st.success(f"✅ 身份验证通过：{input_name}")
        else:
            st.error("❌ 未在专家名单中找到您的名字，请核对或切换为“普通员工”身份。")

else: # 普通员工
    user_dept = st.selectbox("请选择您所在的部门", DEPARTMENTS)
    
    # === 新增逻辑：根据部门筛选人员 ===
    if input_name:
        valid_user = True
        
        if user_dept == "其他部门":
            # 如果是“其他部门”，则可以给所有人打分（或按照您的需求显示全部）
            available_candidates = [p for p in MASTER_ORDER if p in ALL_CANDIDATES]
            st.info(f"👋 欢迎您，{input_name}。您可以对 所有人员 进行打分。")
        else:
            # 如果选择了具体部门，只显示该部门的领导
            # 使用 .get() 防止字典里没有该部门时报错
            dept_leaders = DEPT_LEADER_MAPPING.get(user_dept, [])
            
            # 过滤：确保这些人在总名单里（防止拼写错误）
            available_candidates = [p for p in dept_leaders if p in ALL_CANDIDATES]
            
            if available_candidates:
                st.info(f"👋 欢迎您，{input_name}。您只能对本部门 ({user_dept}) 的领导进行打分。")
            else:
                st.warning(f"⚠️ {user_dept} 暂无需要述职的考评对象。如需给其他领导打分，请选择“其他部门”。")

# --- 第三步：打分操作 ---
if valid_user and input_phone:
    st.markdown("---")
    st.subheader("2. 评分操作")
    
    # 1. 查重
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

    # 2. 排序
    def sort_key(name):
        try:
            return MASTER_ORDER.index(name)
        except ValueError:
            return 999
    available_candidates.sort(key=sort_key)

    # 3. 渲染
    options_display = []
    if not available_candidates:
        st.warning("当前列表为空，请确认部门选择是否正确。")
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
            
            with st.form("scoring_form"):
                st.markdown(f"**正在为【{candidate}】打分**")
                scores = {}
                total_score = 0
                
                for criterion in CRITERIA:
                    st.markdown(f"**{criterion['item']}**")
                    st.caption(f"{criterion['desc']}") 
                    st.caption(f"💡 参考标准：{criterion['guide']}") 
                    score = st.slider(
                        "得分", 0, criterion['max_score'], int(criterion['max_score'] * 0.9),
                        key=f"{candidate}_{criterion['item']}_{role}" 
                    )
                    scores[criterion['item']] = score
                    total_score += score
                    st.divider()
                
                remarks = st.text_area("备注/建议", placeholder="请输入您的评价...")
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
                    
                    st.session_state['success_msg'] = f"🎉 提交成功！【{candidate}】总分：{total_score}。请继续为下一位评分。"
                    st.rerun()

            if 'success_msg' in st.session_state and st.session_state['success_msg']:
                st.success(st.session_state['success_msg'])
                st.session_state['success_msg'] = None

elif valid_user and not input_phone:
    st.warning("👉 请输入电话号码以开启评分区域。")
