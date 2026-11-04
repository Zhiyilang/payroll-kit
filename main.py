#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""payroll-kit 演示入口：用内置考勤示例生成工资表并打印摘要。"""
import os
from calc import run, summarize

RULE = {"late_fee": 50.0, "leave_fee": 100.0, "social_rate": 0.105, "threshold": 5000.0}

if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    att = os.path.join(here, "考勤示例.csv")
    out = os.path.join(here, "工资表.csv")
    res = run(att, RULE, out)
    print(summarize(res))
    print(f"\n→ 已生成 {out}")
