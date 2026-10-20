import unittest
import pandas as pd
from tools.met_knmi_svat_adapter import aggregate

class TestKnmiSvatAdapter(unittest.TestCase):
    def example(self):
        m=pd.DataFrame({'hru_id':[1,1],'svat_id':[11,12],'area_m2':[1.,3.]})
        a=pd.DataFrame({'svat_id':[11,12],'date':['2020-01-01']*2,'rad_kj_m2_d':[100,100],'tmin_c':[1,1],'tmax_c':[3,3],'vapour_pressure_kpa':[1,1],'rain_mm_d':[0.,4.],'etref_mm_d':[2,2]})
        b=pd.DataFrame({'svat_id':[11,12],'date':['2020-01-01']*2,'wind_m_s':[2.,6.],'wet_raw_fraction':[0.5,float('nan')]})
        return m,a,b
    def test_svat_rain_policy_before_weighting(self):
        v,audit=aggregate(*self.example())
        self.assertAlmostEqual(v.wind_m_s[0],5)
        self.assertAlmostEqual(v.rain_mm_d[0],3)
        self.assertAlmostEqual(v.wet_fraction[0],0.075)
        self.assertEqual(audit.fallback_svat_count[0],1)
    def test_partial_support_rejected(self):
        m,a,b=self.example()
        with self.assertRaises(ValueError):aggregate(m,a.iloc[:1],b)
    def test_zero_raw_uses_owner_positive_rain_fallback(self):
        m,a,b=self.example();b.loc[1,'wet_raw_fraction']=0.
        v,audit=aggregate(m,a,b)
        self.assertAlmostEqual(v.wet_fraction[0],0.075)
        self.assertEqual(audit.fallback_svat_count[0],1)
