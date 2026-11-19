import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
import server
class CoreTests(unittest.TestCase):
 def test_profile(self):
  p=server.profile_rows([{'a':'1','b':'x'},{'a':'','b':'y'},{'a':'3','b':'y'}])
  self.assertEqual(p['row_count'],3); self.assertEqual(p['columns'][0]['null_count'],1); self.assertEqual(p['columns'][0]['type'],'numérico')
 def test_classification(self):
  rows=[{'x':i,'z':i%4,'label':'A' if i%10<5 else 'B'} for i in range(80)]
  r=server.run_model({'feature_columns':'["x", "z"]','target_column':'label','approach':'supervised','problem_type':'classification'},rows)
  self.assertEqual(r['engine_type'],'ML_REAL'); self.assertTrue(any(m['name']=='Accuracy' for m in r['metrics']))
 def test_regression(self):
  rows=[{'x':i,'z':i%5,'y':3*i+2*(i%5)+7} for i in range(80)]
  r=server.run_model({'feature_columns':'["x", "z"]','target_column':'y','approach':'supervised','problem_type':'regression'},rows)
  self.assertTrue(any(m['name']=='RMSE' for m in r['metrics']))
 def test_kmeans(self):
  rows=[{'x':i,'z':i%3} for i in range(50)]
  r=server.run_model({'feature_columns':'["x", "z"]','target_column':None,'approach':'unsupervised','problem_type':'clustering'},rows)
  self.assertEqual(r['algorithm'],'K-Means'); self.assertEqual(len(r['clusters']),3)
if __name__=='__main__':unittest.main(verbosity=2)
