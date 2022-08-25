# SPDX-License-Identifier: LGPL-2.1-or-later
from __future__ import absolute_import, division, print_function

import os
import unittest

from pyEcoHAB import Loader, Timeline, data_path
from pyEcoHAB import single_antenna_registrations as sar
from pyEcoHAB import utility_functions as uf


class TestExecution(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sample_data = os.path.join(data_path, "weird_short")
        cls.data = Loader(sample_data)
        cls.config = Timeline(sample_data)

    def test1(self):
        sar.get_single_antenna_stats(self.data, self.config, 3600, "1")

    def test2(self):
        sar.get_single_antenna_stats(self.data, self.config, 3600)

    def test3(self):
        self.assertRaises(
            Exception,
            sar.get_single_antenna_stats,
            self.data,
            self.config,
            3600,
            "gugu",
        )

    def test4(self):
        sar.get_single_antenna_stats(self.data, self.config, 900, "1")

    def test5(self):
        sar.get_single_antenna_stats(self.data, self.config, 900)

    def test6(self):
        sar.get_single_antenna_stats(self.data, self.config, 1800, "1")

    def test7(self):
        sar.get_single_antenna_stats(self.data, self.config, 1800)


if __name__ == "__main__":
    unittest.main()
