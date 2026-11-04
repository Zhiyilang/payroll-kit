#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from calc import compute_row, calc_personal_tax, run, summarize

RULE = {"late_fee": 50.0, "leave_fee": 100.0, "social_rate": 0.105, "threshold": 5000.0}


class TestPayroll(unittest.TestCase):
    def test_full_attendance_no_deduct(self):
        r = compute_row({"姓名": "张三", "部门": "研发", "应出勤": "22", "实际出勤": "22",
                         "迟到次数": "0", "请假天数": "0", "基本工资": "12000"}, RULE)
        self.assertEqual(r["扣款合计"], 0)
        self.assertEqual(r["应发工资"], 12000)
        social = round(12000 * 0.105, 2)
        self.assertEqual(r["社保个人"], social)
        taxable = round(12000 - social - 5000, 2)
        self.assertEqual(r["应纳税所得额"], taxable)
        self.assertEqual(r["个税"], calc_personal_tax(taxable))
        self.assertEqual(r["实发工资"], round(12000 - social - r["个税"], 2))

    def test_late_and_absent(self):
        r = compute_row({"姓名": "李四", "部门": "研发", "应出勤": "22", "实际出勤": "20",
                         "迟到次数": "3", "请假天数": "0", "基本工资": "12000"}, RULE)
        # 缺勤 2 天：日薪=12000/22≈545.45 → 缺勤扣 1090.91
        self.assertAlmostEqual(r["缺勤扣款"], round(2 * (12000 / 22), 2), places=1)
        self.assertEqual(r["迟到扣款"], 150.0)  # 3*50
        self.assertEqual(r["扣款合计"], round(r["缺勤扣款"] + 150.0, 2))

    def test_leave_deduct(self):
        r = compute_row({"姓名": "王五", "部门": "销售", "应出勤": "22", "实际出勤": "22",
                         "迟到次数": "0", "请假天数": "2", "基本工资": "8000"}, RULE)
        self.assertEqual(r["请假扣款"], 200.0)  # 2*100

    def test_tax_brackets(self):
        # 应纳税所得额恰好 3000 → 3%
        self.assertEqual(calc_personal_tax(3000), 90.0)
        # 12000 → 10% - 210 = 990
        self.assertEqual(calc_personal_tax(12000), 990.0)
        # 负数免税
        self.assertEqual(calc_personal_tax(-100), 0.0)

    def test_run_end_to_end(self):
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        att = os.path.join(here, "考勤示例.csv")
        out = os.path.join(here, "_test_out.csv")
        res = run(att, RULE, out)
        self.assertEqual(len(res), 5)
        self.assertTrue(os.path.exists(out))
        # 实发 = 应发 - 社保 - 税
        for r in res:
            self.assertEqual(r["实发工资"], round(r["应发工资"] - r["社保个人"] - r["个税"], 2))
        os.remove(out)


if __name__ == "__main__":
    unittest.main()
