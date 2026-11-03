import unittest
from dataclasses import replace
from schemapact.contracts import *
from schemapact.fixtures import contract_v1,good_rows
class ContractTests(unittest.TestCase):
    def setUp(self): self.c=contract_v1()
    def test_good_passes(self): self.assertEqual(check_batch(self.c,good_rows(),1).decision,"PASS")
    def test_stale_blocks(self): self.assertEqual(check_batch(self.c,good_rows(),25).decision,"BLOCK")
    def test_negative_amount_blocks(self):
        rows=good_rows(); rows[0]["amount"]=-1; self.assertEqual(check_batch(self.c,rows,1).decision,"BLOCK")
    def test_optional_warning(self):
        rows=good_rows(); rows[0]["status"]="bad"; self.assertEqual(check_batch(self.c,rows,1).decision,"WARN")
    def test_missing_critical_blocks(self):
        rows=good_rows(); del rows[0]["order_id"]; self.assertEqual(check_batch(self.c,rows,1).decision,"BLOCK")
    def test_wrong_type(self):
        rows=good_rows(); rows[0]["amount"]="42"; self.assertTrue(any(b.code=="TYPE" for b in check_batch(self.c,rows,1).breaches))
    def test_null(self):
        rows=good_rows(); rows[0]["customer_id"]=None; self.assertTrue(any(b.code=="NULL" for b in check_batch(self.c,rows,1).breaches))
    def test_duplicate_field_rejected(self):
        with self.assertRaises(ValueError): replace(self.c,fields=(self.c.fields[0],self.c.fields[0]))
    def test_bad_type_rejected(self):
        with self.assertRaises(ValueError): FieldRule("x","blob")
    def test_bad_range_rejected(self):
        with self.assertRaises(ValueError): FieldRule("x","number",minimum=2,maximum=1)
    def test_notice_names_impacted_consumer(self):
        rows=good_rows(); rows[0]["amount"]=-1; self.assertIn("revenue-dashboard",check_batch(self.c,rows,1).notice(self.c))
    def test_rename_finds_two_consumers(self):
        new=replace(self.c,fields=tuple(FieldRule("total","number") if f.name=="amount" else f for f in self.c.fields))
        p=preview_migration(self.c,new,{"amount":"total"}); impact=next(i for i in p.impacts if i.field=="amount")
        self.assertEqual(set(impact.consumers),{"revenue-dashboard","risk-model"})
    def test_rename_is_breaking(self):
        new=replace(self.c,fields=tuple(FieldRule("total","number") if f.name=="amount" else f for f in self.c.fields))
        self.assertFalse(preview_migration(self.c,new,{"amount":"total"}).safe)
    def test_removal_detected(self):
        new=replace(self.c,fields=tuple(f for f in self.c.fields if f.name!="status"))
        self.assertEqual(next(i.change for i in preview_migration(self.c,new).impacts if i.field=="status"),"removed")
    def test_type_change_detected(self):
        new=replace(self.c,fields=tuple(replace(f,type="string") if f.name=="amount" else f for f in self.c.fields))
        self.assertIn("type_changed",[i.change for i in preview_migration(self.c,new).impacts])
    def test_tightening_detected(self):
        new=replace(self.c,fields=tuple(replace(f,minimum=10) if f.name=="amount" else f for f in self.c.fields))
        self.assertIn("tightened",[i.change for i in preview_migration(self.c,new).impacts])
    def test_added_field_nonbreaking(self):
        new=replace(self.c,fields=self.c.fields+(FieldRule("note","string",required=False,nullable=True),))
        self.assertTrue(preview_migration(self.c,new).safe)
    def test_lineage_coverage(self): self.assertEqual(preview_migration(self.c,self.c,known_consumer_count=4).lineage_coverage,.75)
    def test_undeclared_count(self): self.assertEqual(preview_migration(self.c,self.c,known_consumer_count=5).undeclared_consumers,2)
    def test_rows_recorded(self):
        rows=good_rows(); rows[1]["amount"]=-1; b=next(b for b in check_batch(self.c,rows,1).breaches if b.code=="MIN"); self.assertEqual(b.rows,(1,))
    def test_sql_lineage_detects_undeclared_field_use(self):
        report=corroborate_sql_lineage(self.c,[QueryUsage("risk-model","SELECT customer_id, amount, status FROM orders")])
        self.assertEqual(("status",),report.findings[0].undeclared_fields)
        self.assertFalse(report.complete)
    def test_sql_lineage_reports_exact_coverage(self):
        report=corroborate_sql_lineage(self.c,[
          QueryUsage("revenue-dashboard","SELECT order_id, amount, status FROM orders"),
          QueryUsage("fulfillment","SELECT order_id, customer_id, status FROM orders"),
          QueryUsage("risk-model","SELECT customer_id, amount, status FROM orders")])
        self.assertEqual(8,report.declared_matches); self.assertEqual(9,report.field_references)
        self.assertAlmostEqual(8/9,report.coverage)
    def test_sql_comments_and_literals_do_not_create_lineage(self):
        report=corroborate_sql_lineage(self.c,[QueryUsage("risk-model","SELECT amount FROM orders WHERE note='status' -- customer_id")])
        self.assertEqual(("amount",),report.findings[0].observed_fields)
    def test_select_star_expands_contract_fields(self):
        report=corroborate_sql_lineage(self.c,[QueryUsage("revenue-dashboard","SELECT o.* FROM orders o")])
        self.assertEqual(set(self.c.field_map),set(report.findings[0].observed_fields))
    def test_unknown_consumer_is_reported(self):
        report=corroborate_sql_lineage(self.c,[QueryUsage("shadow-job","SELECT amount FROM orders")])
        self.assertEqual(1,report.unknown_consumers); self.assertEqual(1,report.undeclared_references)
    def test_sql_lineage_requires_queries_and_sql(self):
        with self.assertRaises(ValueError): corroborate_sql_lineage(self.c,[])
        with self.assertRaises(ValueError): corroborate_sql_lineage(self.c,[QueryUsage("risk-model"," ")])
    def test_declared_usage_is_complete(self):
        report=corroborate_sql_lineage(self.c,[QueryUsage("risk-model","SELECT customer_id, amount FROM orders")])
        self.assertTrue(report.complete); self.assertEqual(1,report.coverage)
    def test_duplicate_consumers_rejected(self):
        with self.assertRaises(ValueError): replace(self.c,consumers=(self.c.consumers[0],self.c.consumers[0]))
if __name__=="__main__": unittest.main()

