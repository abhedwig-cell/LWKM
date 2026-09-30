from tools.p12_rds_selection import *

def test_exposes_inside_loop_fallback_defect():
    members=[
      {"bfe":2,"lgn":7,"rds":10}, # lgn-only arrives first
      {"bfe":1,"lgn":7,"rds":20}, # preferred
      {"bfe":1,"lgn":7,"rds":20}, # preferred
    ]
    assert legacy_rds_candidates(members,1,7)==[10,20,20]
    assert corrected_rds_candidates(members,1,7)==[20,20]

def test_true_fallback_when_no_preferred():
    members=[{"bfe":2,"lgn":7,"rds":10},{"bfe":3,"lgn":7,"rds":12}]
    assert corrected_rds_candidates(members,1,7)==[10,12]
