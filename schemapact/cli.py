import argparse,json
from dataclasses import asdict,replace
from pathlib import Path
from .contracts import check_batch,preview_migration,FieldRule
from .fixtures import contract_v1,good_rows
def main():
    p=argparse.ArgumentParser(); p.add_argument("--output",type=Path,default=Path("report.json")); a=p.parse_args()
    old=contract_v1(); bad=[dict(r) for r in good_rows()]; bad[1]["amount"]=-4
    check=check_batch(old,bad,age_hours=30)
    fields=tuple(FieldRule("total_amount","number",critical=True,minimum=10) if f.name=="amount" else f for f in old.fields)
    new=replace(old,version="2.0.0",fields=fields)
    preview=preview_migration(old,new,{"amount":"total_amount"},known_consumer_count=4)
    report={"check":asdict(check),"notice":check.notice(old),"migration":asdict(preview),"migration_safe":preview.safe}
    a.output.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"decision":check.decision,"breaches":len(check.breaches),"affected_consumers":sorted({c for i in preview.impacts for c in i.consumers}),"lineage_coverage":preview.lineage_coverage},indent=2))
if __name__=="__main__": main()
