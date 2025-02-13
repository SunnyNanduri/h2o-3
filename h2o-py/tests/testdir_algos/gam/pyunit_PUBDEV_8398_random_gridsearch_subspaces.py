from __future__ import division
from __future__ import print_function
import sys
sys.path.insert(1, "../../../")
import h2o
from tests import pyunit_utils
from h2o.estimators.gam import H2OGeneralizedAdditiveEstimator
from h2o.grid.grid_search import H2OGridSearch

# In this test, we check to make sure that a random grid search on a GAM works with hyperparameters containing subspaces.
# The test compares the results of the grid search models with the models we created
# by manually searching over the hyperspace.
# If the coefficients do not match or an incorrect number of models is generated, the test throws an assertion error.
class test_random_gam_gridsearch_specific:

    h2o_data = []
    myX = []
    myY = []
    h2o_model = []
    search_criteria = {'strategy': 'RandomDiscrete', "max_models": 40, "seed": 1}
    hyper_parameters = {'lambda': [0, 0.01],
                        'subspaces': [{'scale': [[1, 1, 1], [2, 2, 2]],
                                         'num_knots': [[5, 5, 5], [5, 6, 7]],
                                         'gam_columns': [["C16", "C17", "C18"]],
                                       'bs':[[2,2,2],[0,0,0],[2,0,2]]},
                                        {'scale': [[1, 1], [2, 2]],
                                         'num_knots': [[5, 5], [6, 6]],
                                         'gam_columns': [["C16", "C17"], ["C17", "C18"]],
                                         'bs': [[2,2],[0,2]]},
                                        {'scale': [[1, 1], [2, 2]],
                                         'num_knots': [[5, 5], [6, 6]],
                                         'gam_columns': [["C16", "C17"], ["C17", "C18"]],
                                         'bs': [[2,2],[0,0]]}]}
    manual_gam_models = []
    num_grid_models = 0
    expected_grid_models = 40

    def __init__(self):
        self.setup_data()

    def setup_data(self):
        """
        This function performs all initializations necessary:
        load the data sets and set the training set indices and response column index
        """
        self.h2o_data = h2o.import_file(
            path = pyunit_utils.locate("smalldata/glm_test/gaussian_20cols_10000Rows.csv"))
        self.h2o_data["C1"] = self.h2o_data["C1"].asfactor()
        self.h2o_data["C2"] = self.h2o_data["C2"].asfactor()
        self.myX = ["C1", "C2"]
        self.myY = "C21"
        for lambda_ in self.hyper_parameters["lambda"]:
            for subspace in self.hyper_parameters["subspaces"]:
                for scale in subspace['scale']:
                    for gam_columns in subspace['gam_columns']:
                        for num_knots in subspace['num_knots']:
                            for bs in subspace['bs']:
                                self.manual_gam_models.append(H2OGeneralizedAdditiveEstimator(family="gaussian",
                                                                                          gam_columns=gam_columns,
                                                                                          keep_gam_cols=True,
                                                                                          scale=scale,
                                                                                          num_knots=num_knots,
                                                                                          lambda_=lambda_,
                                                                                          bs=bs
                                                                                          ))

    def train_models(self):
        self.h2o_model = H2OGridSearch(H2OGeneralizedAdditiveEstimator(family="gaussian", keep_gam_cols=True), 
                                       hyper_params=self.hyper_parameters, search_criteria=self.search_criteria)
        self.h2o_model.train(x = self.myX, y = self.myY, training_frame = self.h2o_data)
        for model in self.manual_gam_models:
            model.train(x = self.myX, y = self.myY, training_frame = self.h2o_data)

    def match_models(self):
        for model in self.manual_gam_models:
            scale = model.actual_params['scale']
            gam_columns = model.actual_params['gam_columns']
            num_knots = model.actual_params['num_knots']
            lambda_ = model.actual_params['lambda']
            bs = model.actual_params['bs']
            for grid_search_model in self.h2o_model.models:
                if grid_search_model.actual_params['gam_columns'] == gam_columns \
                    and grid_search_model.actual_params['scale'] == scale \
                    and grid_search_model.actual_params['bs']==bs \
                    and grid_search_model.actual_params['num_knots'] == num_knots \
                    and grid_search_model.actual_params['lambda'] == lambda_:
                    assert grid_search_model.coef() == model.coef(), "coefficients should be equal"
                    break

        assert len(self.h2o_model.models) == self.expected_grid_models, "Expected model number: {0}, actual model number: " \
                                                            "{1}".format(self.expected_grid_models, len(self.h2o_model.models))

def test_gridsearch():
    test_gam_grid = test_random_gam_gridsearch_specific()
    test_gam_grid.train_models()
    test_gam_grid.match_models()

if __name__ == "__main__":
    pyunit_utils.standalone_test(test_gridsearch)
else:
    test_gridsearch()
