from .contracts import *
def contract_v1():
    return Contract("orders","1.0.0","data-platform",24,(
      FieldRule("order_id","string",critical=True),
      FieldRule("customer_id","string",critical=True),
      FieldRule("amount","number",critical=True,minimum=0),
      FieldRule("status","string",allowed=("paid","refunded","pending")),
    ),(
      Consumer("revenue-dashboard",frozenset({"order_id","amount","status"}),"finance"),
      Consumer("fulfillment",frozenset({"order_id","customer_id","status"}),"operations"),
      Consumer("risk-model",frozenset({"customer_id","amount"}),"risk"),
    ))
def good_rows(): return [{"order_id":"o1","customer_id":"c1","amount":42.5,"status":"paid"},{"order_id":"o2","customer_id":"c2","amount":19.0,"status":"pending"}]
