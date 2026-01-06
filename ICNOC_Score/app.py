import streamlit as st
import pandas as pd
import os
from datetime import datetime

# ==========================================
# 1. 基础配置
# ==========================================
st.set_page_config(page_title="2025年终述职评分", layout="centered")
DATA_FILE = "scoring_results.csv"  # 结果保存的文件名

# ==========================================
# 2. 数据定义
# ==========================================

# --- A. 排序主名单 (用于下拉菜单排序，保持不变) ---
MASTER_ORDER = [
    "刘颖", "邓子悟", "曲博", "陈绮霞", "张学兵", 
    "孙维涛", "张妍", "张远", "任思聪", "楚红涛", 
    "王锡仕", "张赟", "林武隽", "韩慧", "贾育", 
    "时晓鹏", "谭雪洁", "李雨翔", "张萌"
]

# --- B. 述职候选人 (矩阵表的行) ---
# 第1组
TARGETS_GROUP_1 = ["曲博", "陈绮霞"]
# 第2组 (3-15号)
TARGETS_GROUP_2 = [
    "张远", "任思聪", "楚红涛", "王锡仕", "张赟", 
    "林武隽", "韩慧", "贾育", "时晓鹏", "张妍", 
    "谭雪洁", "李雨翔", "张萌"
]
# 所有被考评人
ALL_TARGETS = TARGETS_GROUP_1 + TARGETS_GROUP_2

# --- C. 部门列表 (员工代表选择用) ---
# 【修改点】：删除了最后两项 "ICNOC..." 和 "其他部门"
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
    "基础业务保障中心"
]

# --- D. 部门-人员映射表 (用于员工代表筛选) ---
# 【修改点】：
# 1. 基础业务保障中心：删除了“孙维涛”
# 2. 删除了 "ICNOC/云网运营部..." 的Key
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
    "基础业务保障中心": ["时晓鹏", "张妍"] # 已删除孙维涛
}

# --- E. 领导/评委权限字典 ---
LEADER_PERMISSIONS = {}

# 1. 段冰：打所有人 (1-15号)
LEADER_PERMISSIONS["段冰"] = ALL_TARGETS

# 2. 刘颖、邓子悟：只打第1组
for name in ["刘颖", "邓子悟"]:
    LEADER_PERMISSIONS[name] = TARGETS_GROUP_1

# 3. 曲博、陈绮霞：互相打分
LEADER_PERMISSIONS["曲博"] = ["陈绮霞"]
LEADER_PERMISSIONS["陈绮霞"] = ["曲博"]

# 4. 张学兵、孙维涛：打第2组所有人
for name in ["张学兵", "孙维涛"]:
    LEADER_PERMISSIONS[name] = TARGETS_GROUP_2

# 5. 第2组互评圈
SCORERS_GROUP_2 = [
    "张远", "任思聪", "楚红涛", "张赟", "林武隽", "韩慧", "贾育"
]

for scorer in SCORERS_GROUP_2:
    can_score_list = [p for p in TARGETS_GROUP_2 if p != scorer]
    LEADER_PERMISSIONS[scorer] = can_score_list

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
role = st.radio(
    "请选择您的身份：", 
    ("二级部门班子成员/三级总监", "员工代表"), 
    horizontal=True
)

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
if role == "二级部门班子成员/三级总监":
    if input_name:
        if input_name in LEADER_PERMISSIONS:
            valid_user = True
            available_candidates = LEADER_PERMISSIONS[input_name]
            user_dept = "班子成员/总监"
            st.success(f"✅ 身份验证通过：{input_name}")
        else:
            st.error("❌ 未在评分评委名单中找到您的名字。如果您是述职人员但不在评委列，请切换为“员工代表”。")

else: # 员工代表
    user_dept = st.selectbox("请选择您所在的部门", DEPARTMENTS)
    
    if input_name:
        valid_user = True
        
        # 使用映射表过滤 (删除了“其他部门”的逻辑分支)
        dept_leaders = DEPT_LEADER_MAPPING.get(user_dept, [])
        # 确保只显示在排序名单里的人
        available_candidates = [p for p in dept_leaders if p in MASTER_ORDER]
        
        if available_candidates:
            st.info(f"👋 欢迎您，{input_name}。您只能对本部门 ({user_dept}) 的领导进行打分。")
        else:
            # 防止某个部门没有映射到人（比如映射表写错了，或者该部门领导不在述职名单里）
            st.warning(f
