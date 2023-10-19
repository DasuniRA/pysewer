# SPDX-FileCopyrightText: 2023 Helmholtz Centre for Environmental Research (UFZ)
# SPDX-License-Identifier: GPL-3.0-only

import networkx as nx
import pytest
from shapely.geometry import LineString, Point

import pysewer


class TestOptimization:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.sink_coordinates = (691350, 2553250)
        dem = "./tests/test_data/dem.tif"
        buildings = "./tests/test_data/buildings_clipped.shp"
        roads = "./tests/test_data/roads_clipped.shp"
        self.model_domain = pysewer.ModelDomain(dem, roads, buildings)
        self.model_domain.add_sink(self.sink_coordinates)
        self.connection_graph = self.model_domain.generate_connection_graph()
        self.layout = pysewer.rsph_tree(self.connection_graph, [self.sink_coordinates])
        self.sewer_graph = pysewer.estimate_peakflow(
            self.layout, inhabitants_dwelling=6, daily_wastewater_person=250
        )

    def test_mannings(self):
        diameter = 0.5
        slope = -0.01
        roughness = 0.012
        assert round(pysewer.mannings_equation(diameter, roughness, slope), 3) == 0.205

    def test_diameter(self):
        G = self.sewer_graph = pysewer.calculate_hydraulic_parameters(
            self.layout,
            sinks=[self.sink_coordinates],
            pressurized_diameter=0.2,
            diameters=[0.2, 0.3, 0.4, 0.5, 1, 2],
            roughness=0.012,
        )

    def test_needs_pump_flat(self):
        profile = [(0.0, 10), (10.0, 10), (20, 10)]
        needs_p, out_td, td_profile = pysewer.needs_pump(
            profile, tmin=0.25, min_slope=-0.01
        )
        assert needs_p == False
        assert round(out_td, 2) == 0.45

    def test_needs_pump_flat_low_tmax(self):
        profile = [(0.0, 10), (10.0, 10), (100, 10)]
        needs_p, out_td, td_profile = pysewer.needs_pump(
            profile, tmin=0.25, tmax=0.5, min_slope=-0.01
        )
        assert needs_p == True
