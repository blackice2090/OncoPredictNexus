import unittest
import numpy as np
from features import add_genomic_interactions,FEATURES
from notebook_checks import audit_cells,ranking_labels,bootstrap_gain

class TrainingContractTests(unittest.TestCase):
    def test_engineering_is_target_free_and_preserves_inputs(self):
        x=np.zeros((2,8));x[0,:3]=[1,1,0];x[1,:3]=[0,1,1]
        z=add_genomic_interactions(x)
        self.assertEqual(z.shape,(2,11));np.testing.assert_array_equal(z[:,:8],x)
        np.testing.assert_array_equal(z[:,8:],[[1,0,0],[0,0,1]])
        with self.assertRaises(ValueError):add_genomic_interactions(np.full((2,8),np.nan))
    def test_missing_and_duplicate_cells_fail(self):
        with self.assertRaises(ValueError):audit_cells(['A','A'],np.zeros((2,8)),np.zeros((2,3)))
        with self.assertRaises(ValueError):audit_cells(['A','B'],np.zeros((2,8)),np.full((2,3),np.nan))
    def test_ranking_labels_keep_ties_without_sensitive_thresholds(self):
        np.testing.assert_array_equal(ranking_labels(np.array([[1,2,3],[2,2,3],[3,2,1]])),[0,3,2])
    def test_bootstrap_resamples_cells_and_repeats_stay_together(self):
        y=np.zeros((8,3));base=np.ones((3,8,3));candidate=np.zeros_like(base)
        result=bootstrap_gain(y,base,candidate,100)
        self.assertAlmostEqual(result['delta_RMSE'],1)
        self.assertEqual(result['conditional_95_interval'],[1.,1.])

if __name__=='__main__':unittest.main()
