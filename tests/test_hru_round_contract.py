from tools.run_hru_primary import ROUNDS

BASE=["LDGBclus","lu2","lu4","grondsoort2","grondsoort4"]
EXPECTED=[
BASE[:3]+["lu7"]+BASE[3:]+["pawn21","bodem370","Gt_LHM43","kwelklasse4","isdrain"],
BASE[:3]+["lu7"]+BASE[3:]+["pawn21","bodem370","Gt_LHM43","kwelklasse4"],
BASE+["pawn21","bodem370","Gt_LHM43","kwelklasse4"],
BASE+["pawn21","Gt_LHM43","kwelklasse4"],
BASE+["Gt_LHM43","kwelklasse4"],
BASE+["pawn21","Gt_LHM43"],
BASE+["Gt_LHM43"],
BASE+["pawn21","kwelklasse4"],
BASE+["kwelklasse4"],
BASE+["pawn21"],
BASE]
def test_historical_eleven_round_order_is_frozen():
    assert ROUNDS==EXPECTED
