#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
payroll_kit · 工资条/考勤自动核算（零依赖，纯标准库）

输入：考勤 CSV（姓名,部门,应出勤,实际出勤,迟到次数,请假天数,基本工资）
      + 规则（迟到扣款/次, 请假扣款/天, 社保个人比例, 个税起征点）
输出：工资表 CSV（应发, 扣款合计, 社保, 个税, 实发）

个税采用 2019 年起月度累进税率表（参考计算，非报税依据）。
"""
import csv
import io

# 月度个税税率表：(上限, 税率, 速算扣除数)
_TAX_BRACKETS = [
    (3000, 0.03, 0),
    (12000, 0.10, 210),
    (25000, 0.20, 1410),
    (35000, 0.25, 2660),
    (55000, 0.30, 4410),
    (80000, 0.35, 7160),
    (float("inf"), 0.45, 15160),
]


def calc_personal_tax(taxable: float) -> float:
    """根据应纳税所得额计算月度个税（速算扣除法）。taxable<=0 则免税。"""
    if taxable <= 0:
        return 0.0
    for upper, rate, quick in _TAX_BRACKETS:
        if taxable <= upper:
            return round(taxable * rate - quick, 2)
    return 0.0  # 不应到达


def compute_row(row: dict, rule: dict) -> dict:
    """核算单行工资。row 字段为字符串（从 CSV 读入），此处解析。"""
    name = row.get("姓名", "").strip()
    dept = row.get("部门", "").strip()
    should = float(row.get("应出勤", "0") or 0)
    actual = float(row.get("实际出勤", "0") or 0)
    late = int(float(row.get("迟到次数", "0") or 0))
    leave = float(row.get("请假天数", "0") or 0)
    base = float(row.get("基本工资", "0") or 0)

    late_fee = rule["late_fee"]          # 每次迟到扣款
    leave_fee = rule["leave_fee"]        # 每天请假扣款
    social_rate = rule["social_rate"]    # 社保个人比例
    threshold = rule["threshold"]        # 个税起征点

    # 缺勤扣款：应出勤 - 实际出勤 天，按日薪扣（日薪 = 基本工资/应出勤）
    absent_days = max(0.0, should - actual)
    daily = (base / should) if should > 0 else 0.0
    absent_fee = round(absent_days * daily, 2)

    late_total = round(late * late_fee, 2)
    leave_total = round(leave * leave_fee, 2)
    deduct = round(absent_fee + late_total + leave_total, 2)

    pay_before = round(base - deduct, 2)                       # 应发
    social = round(pay_before * social_rate, 2)                # 社保个人部分
    taxable = round(pay_before - social - threshold, 2)        # 应纳税所得额
    tax = calc_personal_tax(taxable)                           # 个税
    net = round(pay_before - social - tax, 2)                  # 实发

    return {
        "姓名": name,
        "部门": dept,
        "基本工资": base,
        "缺勤天数": round(absent_days, 1),
        "迟到次数": late,
        "请假天数": leave,
        "缺勤扣款": absent_fee,
        "迟到扣款": late_total,
        "请假扣款": leave_total,
        "扣款合计": deduct,
        "应发工资": pay_before,
        "社保个人": social,
        "应纳税所得额": taxable,
        "个税": tax,
        "实发工资": net,
    }


def run(attendance_csv: str, rule: dict, out_csv: str = "工资表.csv") -> list:
    """读考勤 CSV → 核算 → 写工资表 CSV，返回结果行列表。"""
    with open(attendance_csv, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    results = [compute_row(r, rule) for r in rows]
    fields = list(results[0].keys()) if results else []
    with open(out_csv, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(results)
    return results


def summarize(results: list) -> str:
    total_net = sum(r["实发工资"] for r in results)
    total_tax = sum(r["个税"] for r in results)
    buf = io.StringIO()
    buf.write(f"核算 {len(results)} 人 | 实发合计 ¥{round(total_net,2):,.2f} | 个税合计 ¥{round(total_tax,2):,.2f}\n")
    for r in results:
        buf.write(f"  {r['姓名']}({r['部门']}): 应发¥{r['应发工资']:,.2f} - 社保¥{r['社保个人']:,.2f} - 税¥{r['个税']:,.2f} = 实发¥{r['实发工资']:,.2f}\n")
    return buf.getvalue()


if __name__ == "__main__":
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    rule = {"late_fee": 50.0, "leave_fee": 100.0, "social_rate": 0.105, "threshold": 5000.0}
    att = os.path.join(here, "考勤示例.csv")
    out = os.path.join(here, "工资表.csv")
    res = run(att, rule, out)
    print(summarize(res))
    print(f"\n→ 已生成 {out}")
