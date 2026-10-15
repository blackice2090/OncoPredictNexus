import unittest,sys
from pathlib import Path
HERE=Path(__file__).parent;sys.path.insert(0,str(HERE))
from compare import partition_indices,searches
import numpy as np

class Contract(unittest.TestCase):
    def test_partition_must_have_all_five_folds(self):
        with self.assertRaises(ValueError):partition_indices(np.array([1,2,3]),1)
        train,test=partition_indices(np.tile([1,2,3,4,5],3),2)
        self.assertEqual(len(test),3);self.assertFalse(set(train)&set(test))
    def test_search_is_small_and_cpu_only(self):
        from sklearn.model_selection import ParameterGrid
        candidates=searches(4,43)
        self.assertEqual(len(ParameterGrid(candidates['xgboost'].param_grid)),8)
        model=candidates['xgboost'].estimator.named_steps['model'].estimator
        self.assertEqual(model.n_jobs,1);self.assertEqual(model.tree_method,'hist')
        self.assertFalse(hasattr(model,'callbacks') and model.callbacks)
if __name__=='__main__':unittest.main()
