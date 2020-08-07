from efsassembler.DataManager import DataManager as dm
import rpy2.robjects as robjects
import importlib
import os.path
import sys

class FSelector:

    # ranking_name: the name of the csv ranking output produced by the algorithm;
    def __init__(self, ranking_name, script_name):

        self.ranking_name = ranking_name
        self.script_name = script_name
        self.user_script = False
        self._check_for_script_file()

    
    @classmethod
    def generate_fselectors_object(self, methods):
        
        fs_methods = []
        for script, language, ranking_name in methods:
            if language == "python":
                fs_methods.append(
                    PySelector(ranking_name, script)
                )
            elif language == "r":
                fs_methods.append(
                    RSelector(ranking_name, script)
                )
        return fs_methods


    def _check_for_script_file(self):
        pkgdir = sys.modules['efsassembler'].__path__[0] + "/"
        user_alg_path = pkgdir + "fs_algorithms/user_algorithms/"
        user_r_script = os.path.isfile(user_alg_path + self.script_name + ".r")
        user_py_script = os.path.isfile(user_alg_path + self.script_name + ".py")

        if user_py_script or user_r_script:
            self.user_script = True
        else:
            self.user_script = False
        return


class RSelector(FSelector):

    def select(self, dataframe, output_path=None, save_ranking=True):
        dataframe = dm.pandas_to_r(dataframe)

        this_file_path = os.path.dirname(__file__)
        if self.user_script:
            call = this_file_path + "/fs_algorithms/user_algorithms/" + self.script_name + ".r"
        else:
            call = this_file_path + "/fs_algorithms/" + self.script_name + ".r"
        robjects.r.source(call)

        ranking = robjects.r["select"](dataframe)
        ranking = dm.r_to_pandas(ranking)
        
        if save_ranking:
            dm.save_encoded_ranking(ranking, output_path+self.ranking_name)

        robjects.r['rm']('select')
        return ranking


class PySelector(FSelector):

    def __init__(self, ranking_name, script_name):
        FSelector.__init__(self, ranking_name, script_name)
        if self.user_script:
            self.py_selection = importlib.import_module("efsassembler.fs_algorithms.user_algorithms." + \
                                                        script_name).select
        else:
            self.py_selection = importlib.import_module("efsassembler.fs_algorithms."+script_name).select

    def select(self, dataframe, output_path=None, save_ranking=True):
        ranking = self.py_selection(dataframe)
        if save_ranking:
            dm.save_encoded_ranking(ranking, output_path+self.ranking_name)
        return ranking