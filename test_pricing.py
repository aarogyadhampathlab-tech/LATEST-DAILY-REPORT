import unittest

import pandas as pd

from pricing import PriceListError, build_financial_summary, format_inr, read_price_list


class PricingTests(unittest.TestCase):
    def test_formats_amounts_with_indian_grouping_and_no_decimal_places(self):
        self.assertEqual(format_inr(262420), "₹2,62,420")
        self.assertEqual(format_inr(113640.25), "₹1,13,640")
        self.assertEqual(format_inr(300), "₹300")

    def test_reads_excel_html_price_list_and_estimates_by_booking_mode(self):
        price_list = read_price_list(
            b"""<html><body><table>
            <tr><th>Test Id</th><th>Test Name</th><th>OPD Charge</th><th>IPD Charge</th></tr>
            <tr><td>12</td><td>Complete Blood Count</td><td>300.00</td><td>350.00</td></tr>
            <tr><td>13</td><td>Urine Analysis</td><td>100.00</td><td>120.00</td></tr>
            </table></body></html>""",
            "price list.xls",
        )
        reports = [
            pd.DataFrame({
                "testid": ["12", "12", "12", "13", "99"],
                "TestName": ["CBC", "CBC", "CBC", "Urine", "Unlisted"],
                "BookingMode": ["IPD", "OPD Indent", "IPD", "OPD Indent", "IPD"],
            })
        ]

        table, totals = build_financial_summary(reports, price_list)

        self.assertEqual(table.iloc[0]["Test"], "CBC")
        self.assertEqual(table.iloc[0]["Total tests"], 3)
        self.assertEqual(table.iloc[0]["Estimated charges"], 1000)
        unlisted_test = table[table["Test"] == "Unlisted"].iloc[0]
        self.assertFalse(unlisted_test["Price available"])
        self.assertEqual(totals["estimated_charges"], 1100)
        self.assertEqual(totals["tests_with_prices"], 4)
        self.assertEqual(totals["tests_without_prices"], 1)

    def test_rejects_price_list_with_conflicting_test_ids(self):
        contents = b"""<html><body><table>
        <tr><th>Test Id</th><th>Test Name</th><th>OPD Charge</th><th>IPD Charge</th></tr>
        <tr><td>12</td><td>Test A</td><td>100</td><td>100</td></tr>
        <tr><td>12</td><td>Test A</td><td>200</td><td>200</td></tr>
        </table></body></html>"""

        with self.assertRaisesRegex(PriceListError, "conflicting prices"):
            read_price_list(contents, "prices.xls")


if __name__ == "__main__":
    unittest.main()
