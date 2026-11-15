import unittest
import numpy as np
import pandas as pd
import xarray as xr
from vrishin_transport_tools import build_transition_matrix, bootstrap_exit_probability
from vrishin_drifter_exit_and_timestep_analysis import process_pairs, km_summary

class TransportTests(unittest.TestCase):
    def test_matrix_and_unknown_rows(self):
        df = pd.DataFrame({'origin_cell':[0,0,0,1], 'dest':[0,234,235,237], 'traj':[1,2,3,4]})
        p,c,n = build_transition_matrix(df)
        self.assertAlmostEqual(p[0,234], 1/3)
        self.assertTrue(np.isnan(p[2]).all())
        self.assertEqual(p[234,234], 1)
        ps,_,_=build_transition_matrix(df,unsupported='self_loop')
        self.assertTrue(np.allclose(ps.sum(axis=1),1))
        self.assertEqual(ps[2,2],1)

    def test_cluster_bootstrap(self):
        df=pd.DataFrame({'origin_cell':[0,0,0,0], 'dest':[234,234,0,0], 'traj':[1,1,2,2]})
        point,ci,n=bootstrap_exit_probability(df,0,234,B=100,seed=42)
        self.assertAlmostEqual(point,.5)
        self.assertEqual(n,100)
        self.assertLessEqual(ci[0],point)
        self.assertGreaterEqual(ci[1],point)

    def test_rule_reentry_and_cell_exit(self):
        time=np.arange(9*24+1)*np.timedelta64(1,'h')+np.datetime64('2000-01-01')
        lon=np.full(len(time),11.0); lat=np.full(len(time),-44.0)
        lon[24:]=13.0 # leaves cell 0 at day 1
        lon[48:72]=46.0 # exits R on day 2 and returns at day 3
        lon[72:]=13.0
        ds=xr.Dataset({'lon': ('obs',lon),'lat': ('obs',lat),'time': ('obs',time),'rowsize':('traj',[len(time)])})
        pairs=pd.DataFrame([{'traj':0,'obs_row':0,'time':'2000-01-01','origin_cell':0,'dest':235}])
        res=process_pairs(ds,pairs).iloc[0]
        self.assertEqual(res.first3,235)
        self.assertEqual(res.first7,235)
        self.assertEqual(res.endpoint7,1)
        self.assertEqual(res.cell_exit_days,1)
        self.assertTrue(res.cell_exit_observed)

    def test_km_right_censor(self):
        n,e,med,p3,p7=km_summary([1,2,5],[True,False,True])
        self.assertEqual((n,e),(3,2))
        self.assertAlmostEqual(p3,1/3)
        self.assertAlmostEqual(p7,1.0)

if __name__=='__main__': unittest.main()
