# general imports
import os
import shutil
import unittest
import numpy as np

from tests.setup_test_data import setup_gt_test_data
from tests.setup_test_data import dirpath_test

from geopathfinder.naming_conventions.sgrt_naming import create_sgrt_filename

# import yeoda
from yeoda.datacube import EODataCube


class EODataCubeTester(unittest.TestCase):
    """ Responsible for testing all the data cube operations and functionalities of a data cube. """

    @classmethod
    def setUpClass(cls):
        """ Creates GeoTIFF test data. """

        setup_gt_test_data()

    @classmethod
    def tearDownClass(cls):
        """ Removes all test data. """

        shutil.rmtree(os.path.join(dirpath_test(), 'data'))

    def setUp(self):
        """ Retrieves test data filepaths and auxiliary data. """

        self.gt_filepaths, self.timestamps = setup_gt_test_data()

    def test_unknown_filename(self):
        """ Checks data cube structure if filename translation fails. """

        # function which is not able to interpret the filename
        def smart_filename_creator(x):
            raise Exception('')

        dc = EODataCube(filepaths=self.gt_filepaths, smart_filename_creator=smart_filename_creator,
                        dimensions=['time', 'var_name', 'pol'])
        assert len(dc.dimensions) == 1
        assert len(dc) == len(self.gt_filepaths)

    def test_rename_dimension(self):
        """ Tests renaming a dimension of a data cube. """

        dc = EODataCube(filepaths=self.gt_filepaths, smart_filename_creator=create_sgrt_filename,
                        dimensions=['time', 'var_name', 'pol'])
        dc.rename_dimensions({'pol': 'band'}, in_place=True)
        assert 'band' in dc.inventory.columns
        assert 'pol' not in dc.inventory.columns
        assert len(set(dc['band'])) == 2

    def test_add_dimension(self):
        """ Tests adding a dimension to a data cube. """

        dc = EODataCube(filepaths=self.gt_filepaths, smart_filename_creator=create_sgrt_filename,
                        dimensions=['time', 'var_name', 'pol'])
        dim_values = np.random.rand(len(dc))
        dc.add_dimension("value", dim_values, in_place=True)
        assert "value" in dc.inventory.columns
        assert list(dc['value']) == dim_values.tolist()

    def test_sort_by_dimension(self):
        """ Tests sorting a dimension of the data cube. """

        dc = EODataCube(filepaths=self.gt_filepaths, smart_filename_creator=create_sgrt_filename,
                        dimensions=['time', 'var_name', 'pol'])
        timestamps = list(dc['time'])
        dim_values = np.random.rand(len(dc))
        timestamps_sorted = np.array(timestamps)[np.argsort(dim_values)].tolist()

        dc.add_dimension("value", dim_values, in_place=True)
        dc.sort_by_dimension("value", in_place=True)
        assert list(dc['time']) == timestamps_sorted

    def test_split_time(self):
        """ Tests splitting of the data cube in time to create multiple data cubes. """

        dc = EODataCube(filepaths=self.gt_filepaths, smart_filename_creator=create_sgrt_filename,
                        dimensions=['time', 'var_name', 'pol'])
        first_time_interval = (self.timestamps[0], self.timestamps[1])
        second_time_interval = (self.timestamps[2], self.timestamps[-1])
        expression = (">=", "<=")
        dcs = dc.split_by_dimension([first_time_interval, second_time_interval], expressions=[expression, expression])
        assert len(dcs) == 2
        assert sorted(list(set(dcs[0]['time']))) == self.timestamps[:2]
        assert sorted(list(set(dcs[1]['time']))) == self.timestamps[2:]

    def test_split_yearly(self):
        """ Test splitting of the data cube in yearly intervals to create yearly data cubes. """

        dc = EODataCube(filepaths=self.gt_filepaths, smart_filename_creator=create_sgrt_filename,
                        dimensions=['time', 'var_name', 'pol'])
        yearly_dcs = dc.split_yearly(name='time')
        assert len(yearly_dcs) == 2
        dcs_2016 = dc.split_yearly(name='time', years=2016)
        assert len(dcs_2016) == 1
        dc_2016 = dcs_2016[0]
        years = [timestamp.year for timestamp in dc_2016['time']]
        assert (np.array(years) == 2016).all()

    def test_split_monthly(self):
        """ Test splitting of the data cube in monthly intervals to create monthly data cubes. """

        dc = EODataCube(filepaths=self.gt_filepaths, smart_filename_creator=create_sgrt_filename,
                        dimensions=['time', 'var_name', 'pol'])
        monthly_dcs = dc.split_monthly(name='time')
        assert len(monthly_dcs) == 4
        dcs_feb = dc.split_monthly(name='time', months=2)
        assert len(dcs_feb) == 2
        months = [timestamp.month for dc_feb in dcs_feb for timestamp in dc_feb['time']]
        assert (np.array(months) == 2).all()

    def test_unite(self):
        """
        Tests data cube union, i.e. if all data from a second datacube is added to the original data cube
        (rows and columns).
        """

        n = len(self.gt_filepaths)
        dc_1 = EODataCube(filepaths=self.gt_filepaths[:int(n/2)], smart_filename_creator=create_sgrt_filename,
                          dimensions=['time', 'pol'])
        dc_2 = EODataCube(filepaths=self.gt_filepaths[int(n/2):], smart_filename_creator=create_sgrt_filename,
                          dimensions=['time', 'orbit_direction'])

        dc_united = dc_1.unite(dc_2)
        assert 'pol' in dc_united.dimensions
        assert 'orbit_direction' in dc_united.dimensions

    def test_intersect_empty(self):
        """
        Tests data cube intersection on the temporal dimension, i.e. if all data from a second datacube is properly
        intersected with the data of to the original data cube according to matching timestamps. The result should be
        empty due to non-overlapping timestamps.
        """

        # empty data cube when an intersection is applied
        dc_1 = EODataCube(filepaths=self.gt_filepaths, smart_filename_creator=create_sgrt_filename,
                          dimensions=['time', 'pol'])
        dc_2 = EODataCube(filepaths=self.gt_filepaths, smart_filename_creator=create_sgrt_filename,
                          dimensions=['time', 'orbit_direction'])
        dc_1.inventory = dc_1.inventory[dc_1['time'] == self.timestamps[0]]
        dc_2.inventory = dc_2.inventory[dc_2['time'] == self.timestamps[1]]
        dc_intersected = dc_1.intersect(dc_2, on_dimension='time')
        assert len(dc_intersected) == 0

    def test_intersect_dimensions(self):
        """
        Tests simple data cube intersection, i.e. if all data from a second datacube is properly
        intersected with the data of to the original data cube.
        """

        dc_1 = EODataCube(filepaths=self.gt_filepaths, smart_filename_creator=create_sgrt_filename,
                          dimensions=['time', 'pol'])
        dc_2 = EODataCube(filepaths=self.gt_filepaths, smart_filename_creator=create_sgrt_filename,
                          dimensions=['time', 'orbit_direction'])

        dc_intersected = dc_1.intersect(dc_2)
        assert len(dc_intersected) == len(self.gt_filepaths)
        assert 'pol' not in dc_intersected.dimensions
        assert 'orbit_direction' not in dc_intersected.dimensions
        assert 'time' in dc_intersected.dimensions

    def test_intersect_align_dimension_shrink(self):
        """
        Tests matching of entries with two different methods, which should yield the same result: data cube
        intersection and data cube alignment on the temporal dimension.
        """

        dc_1 = EODataCube(filepaths=self.gt_filepaths, smart_filename_creator=create_sgrt_filename,
                          dimensions=['time'])
        dc_2 = dc_1.clone()
        dc_2.inventory = dc_2.inventory[dc_2['time'] != self.timestamps[0]]
        dc_2.inventory = dc_2.inventory[dc_2['time'] != self.timestamps[2]]

        dc_aligned = dc_1.align_dimension(dc_2, name='time', in_place=False)
        dc_intersected = dc_1.intersect(dc_2, on_dimension='time', in_place=False)

        assert sorted(list(dc_aligned['time'])) == sorted(list(dc_intersected['time']))

    def test_align_dimension_shrink(self):
        """
        Tests alignment of a data cube with another data cube along the temporal dimension. Since the second
        data cube contains less data, the original data cube will also contain less data, i.e. the same timestamps as
        in the other data cube.
        """

        dc_1 = EODataCube(filepaths=self.gt_filepaths, smart_filename_creator=create_sgrt_filename,
                          dimensions=['time'])
        dc_2 = dc_1.clone()
        dc_2.inventory = dc_2.inventory[dc_2['time'] != self.timestamps[0]]
        dc_2.inventory = dc_2.inventory[dc_2['time'] != self.timestamps[2]]

        dc_1.align_dimension(dc_2, name='time', in_place=True)
        assert sorted(list(set(dc_1['time']))) == [self.timestamps[1], self.timestamps[3]]

    def test_align_dimension_grow(self):
        """
        Tests alignment of a data cube with another data cube along the temporal dimension. Since the second
        data cube contains more data, the original data cube will also contain more data, i.e. the same timestamps as
        in the other data cube by duplicating the entries.
        """

        dc_1 = EODataCube(filepaths=self.gt_filepaths, smart_filename_creator=create_sgrt_filename,
                          dimensions=['time'])
        dc_2 = dc_1.clone()
        timestamps = list(dc_1['time'])
        subset_idxs = [timestamps.index(self.timestamps[0]),
                       timestamps.index(self.timestamps[1]),
                       timestamps.index(self.timestamps[2]),
                       timestamps.index(self.timestamps[3])]
        dc_1.inventory = dc_1.inventory.iloc[subset_idxs]

        dc_1.align_dimension(dc_2, name='time', in_place=True)
        assert (dc_1['time'] == dc_2['time']).all()

if __name__ == '__main__':
    unittest.main()

