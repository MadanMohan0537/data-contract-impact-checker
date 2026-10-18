"""Versioned data contracts, checks, circuit breaking, and migration previews."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any

TYPES={"string":str,"integer":int,"number":(int,float),"boolean":bool}

@dataclass(frozen=True)
class FieldRule:
    name:str
    type:str
    required:bool=True
    nullable:bool=False
    critical:bool=False
    minimum:float|None=None
    maximum:float|None=None
    allowed:tuple[Any,...]=()
    def __post_init__(self):
        if self.type not in TYPES: raise ValueError(f"unsupported type: {self.type}")
        if self.minimum is not None and self.maximum is not None and self.minimum>self.maximum: raise ValueError("minimum exceeds maximum")

@dataclass(frozen=True)
class Consumer:
    name:str
    fields:frozenset[str]
    owner:str
    signed:bool=True

@dataclass(frozen=True)
class Contract:
    dataset:str
    version:str
    producer:str
    freshness_hours:int
    fields:tuple[FieldRule,...]
    consumers:tuple[Consumer,...]=()
    def __post_init__(self):
        if len({f.name for f in self.fields})!=len(self.fields): raise ValueError("duplicate field")
        if self.freshness_hours<1: raise ValueError("freshness must be positive")
    @property
    def field_map(self): return {f.name:f for f in self.fields}

@dataclass(frozen=True)
class Breach:
    code:str
    field:str|None
    severity:str
    rows:tuple[int,...]
    detail:str

@dataclass(frozen=True)
class CheckResult:
    dataset:str
    row_count:int
    breaches:tuple[Breach,...]
    decision:str
    checked_at:str
    def notice(self,contract:Contract)->str:
        if not self.breaches: return f"{contract.dataset}: batch passed its contract."
        impacted=sorted(c.name for c in contract.consumers if any(b.field in c.fields for b in self.breaches))
        owners=", ".join(impacted) or "no declared consumer"
        return (f"{contract.dataset} contract {contract.version} failed. Decision: {self.decision}. "
                f"{len(self.breaches)} rule(s) failed; affected consumers: {owners}. "
                f"Producer owner: {contract.producer}. Inspect breach codes before retrying.")

def check_batch(contract:Contract,rows:list[dict[str,Any]],age_hours:float)->CheckResult:
    breaches:list[Breach]=[]; fields=contract.field_map
    if age_hours>contract.freshness_hours:
        breaches.append(Breach("STALE",None,"critical",(),f"{age_hours:.1f}h exceeds {contract.freshness_hours}h"))
    for name,rule in fields.items():
        missing=tuple(i for i,row in enumerate(rows) if name not in row)
        if rule.required and missing: breaches.append(Breach("MISSING_FIELD",name,"critical" if rule.critical else "warning",missing,"required field absent"))
        nulls=tuple(i for i,row in enumerate(rows) if name in row and row[name] is None)
        if not rule.nullable and nulls: breaches.append(Breach("NULL",name,"critical" if rule.critical else "warning",nulls,"null not allowed"))
        valid=[(i,row[name]) for i,row in enumerate(rows) if name in row and row[name] is not None]
        wrong=tuple(i for i,v in valid if not isinstance(v,TYPES[rule.type]) or (rule.type=="integer" and isinstance(v,bool)))
        if wrong: breaches.append(Breach("TYPE",name,"critical" if rule.critical else "warning",wrong,f"expected {rule.type}"))
        numeric=[(i,v) for i,v in valid if isinstance(v,(int,float)) and not isinstance(v,bool)]
        low=tuple(i for i,v in numeric if rule.minimum is not None and v<rule.minimum)
        high=tuple(i for i,v in numeric if rule.maximum is not None and v>rule.maximum)
        if low: breaches.append(Breach("MIN",name,"critical" if rule.critical else "warning",low,f"below {rule.minimum}"))
        if high: breaches.append(Breach("MAX",name,"critical" if rule.critical else "warning",high,f"above {rule.maximum}"))
        disallowed=tuple(i for i,v in valid if rule.allowed and v not in rule.allowed)
        if disallowed: breaches.append(Breach("ALLOWED",name,"critical" if rule.critical else "warning",disallowed,"value outside allowed set"))
    decision="BLOCK" if any(b.severity=="critical" for b in breaches) else "WARN" if breaches else "PASS"
    return CheckResult(contract.dataset,len(rows),tuple(breaches),decision,datetime.now(timezone.utc).isoformat())

@dataclass(frozen=True)
class Impact:
    change:str
    field:str
    consumers:tuple[str,...]
    severity:str
    proposal:str

@dataclass(frozen=True)
class MigrationPreview:
    impacts:tuple[Impact,...]
    lineage_coverage:float
    undeclared_consumers:int
    @property
    def safe(self): return not any(i.severity=="breaking" for i in self.impacts)

def preview_migration(old:Contract,new:Contract,renames:dict[str,str]|None=None,known_consumer_count:int|None=None)->MigrationPreview:
    renames=renames or {}; oldmap,newmap=old.field_map,new.field_map; impacts=[]
    def users(field): return tuple(sorted(c.name for c in old.consumers if field in c.fields))
    for name,rule in oldmap.items():
        replacement=renames.get(name)
        if replacement and replacement in newmap:
            impacts.append(Impact("renamed",name,users(name),"breaking",f"dual-publish {name} and {replacement}, migrate consumers, then remove"))
        elif name not in newmap:
            impacts.append(Impact("removed",name,users(name),"breaking",f"retain {name} until declared consumers migrate"))
        else:
            other=newmap[name]
            if rule.type!=other.type: impacts.append(Impact("type_changed",name,users(name),"breaking","publish a compatible shadow field and backfill"))
            tightened=(rule.nullable and not other.nullable) or (other.minimum is not None and (rule.minimum is None or other.minimum>rule.minimum)) or (other.maximum is not None and (rule.maximum is None or other.maximum<rule.maximum))
            if tightened: impacts.append(Impact("tightened",name,users(name),"breaking","measure violations, remediate producers, then enforce"))
    declared=len(old.consumers); known=known_consumer_count if known_consumer_count is not None else declared
    coverage=1.0 if known==0 else min(1.0,declared/known)
    return MigrationPreview(tuple(impacts),coverage,max(0,known-declared))
