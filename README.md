<!-- SPDX-FileCopyrightText: 2023 Helmholtz Centre for Environmental Research (UFZ)
SPDX-License-Identifier: GPL-3.0-only -->

# pysewer

- [pysewer](#pysewer)
  - [Summary](#summary)
  - [Documentation](#documentation)
  - [Installation](#installation)
    - [Step 1: Clone the repository and navigate to the root directory](#step-1-clone-the-repository-and-navigate-to-the-root-directory)
    - [Step 2: Create the conda environment](#step-2-create-the-conda-environment)
    - [Step 3: Install pysewer via pip](#step-3-install-pysewer-via-pip)
  - [Input Data and data representation](#input-data-and-data-representation)
    - [Road Network Data](#road-network-data)
    - [Building Data](#building-data)
    - [Preprocessing](#preprocessing)
    - [Graph Attributes](#graph-attributes)
  - [Routing Solver](#routing-solver)
  - [Plotting](#plotting)
  - [Export](#export)
  - [Default parameters](#default-parameters)
  - [License](#license)
- [How to contribute to pysewer?](#how-to-contribute-to-pysewer)
  - [Code of conduct](#code-of-conduct)
  - [How to cite?](#how-to-cite)

<!-- /TOC -->

## Summary

![Example of an automatically generated Sewer Network](notebooks/example_data/plots/modeldomain_pumps.png)

The aim of pysewer is to provide a framework automatically generate cost-efficient sewer network layouts on minimal data requirements.

It is build around an algorithm for generation of viable sewer-network layouts. The approximated sewer network is represented by sources (households/buildings), potential pathways, and one or multiple sinks. The algorithm approximates the directed steinertree (the steiner arborescence) between all sources and the sink by using an repeated shortest path heuristic (RSPH).


## Documentation
The documentation can be found [here](https://despot.pages.ufz.de/pysewer).  

An example of how to use pysewer for generating a sewer network layout can be found here: [example_sewer_network_generation](notebooks/example_sewer_network.ipynb).

## Installation

Currently the installation is easiest managed via Anaconda. Anaconda 3 can be downloaded [here.](https://www.anaconda.com/products/individual). The package is tested with **Python 3.10.6**. We recommend using a conda environment to manage the installation of GDAL and other dependencies given the difficulty of installing GDAL using pip. Therefore we urge to first create a new conda environment and install the required packages.  

**Please use conda to install GDAL, it is the easiest way to install GDAL**

### Step 1: Clone the repository and navigate to the root directory

```shell
git clone https://github.com/dbdespot/pysewer.git
cd pysewer
```


### Step 2: Create the conda environment
Here you create a conda environment (pysewer) and install the required packages.  We recommend directly installing GDAL, Rasterio and Fiona using conda.

Creating the conda environment:

```shell
conda create -n pysewer python=3.10.6
```

Activate the environment:

```shell
conda activate pysewer
```

Install the required packages:

```shell
conda install -c conda-forge gdal 
```

All other packages are installed via pip during the installation of pysewer.
Note that the exact versions of the packages used can be found in the [environment.yml](environment.yml) file.  

### Step 3: Install pysewer via pip

Now that you have conda environment uo and running, lets install pysewer. To do this you first need to clone pysewer repository hosted [here.](https://github.com/dbdespot/pysewer) and install it using git and pip with:

```shell
cd pysewer
pip install .

# for the development version
python -m pip install -e .

# OR just 
pip install -e .
```

> [!TIP]  
> To install without cloning the repository use:  
> ```pip install git+https://github.com/dbdespot/pysewer.git```  

Please see the [documentation](https://despot.pages.ufz.de/pysewer) for more details.

## Input Data and data representation

The following input data is required:

- A Digital Elevation Model (DEM)
- Point Data on Building locations
- Road Network Data
- Local daily water consumption (cubic meter per person)

### Road Network Data

The roads data is expected to be either LineString or MultiLineString geometries with a valid CRS. The GeoDataFrame can contain additional attributes that will be preserved during the preprocessing.

| Column Name      | Data Type                    | Description                                                                         |
| ---------------- | ---------------------------- | ----------------------------------------------------------------------------------- |
| geometry         | LineString / MultiLineString | The geometry representing the road network.                                         |
| road_id          | integer                      | Unique identifier for each road segment (required).                                 |
| other_attributes | various                      | Any additional attributes related to roads (optional, preserved during processing). |

**Example Roads Geodataframe**

| geometry                                                    | road_id | other_attributes                        |
| ----------------------------------------------------------- | ------- | --------------------------------------- |
| LineString((x1, y1), …)                                     | 1       | {'name': 'Main St.', 'type': 'highway'} |
| MultiLineString(((x2, y2), (x3, y3)), ((x4, y4), (x5, y5))) | 2       | {'name': '2nd Ave.', 'type': 'street'}  |

### Building Data

The buildings data can include Polygon, MultiPolygon, or Point geometries, where polygons will be converted to points (centroids). The GeoDataFrame should also have a valid CRS, which should match the CRS of the roads data.

| Column Name      | Data Type                      | Description                                                                             |
| ---------------- | ------------------------------ | --------------------------------------------------------------------------------------- |
| geometry         | Point / Polygon / MultiPolygon | The geometry representing the buildings (which can be converted to points).             |
| building_id      | integer                        | Unique identifier for each building.                                                    |
| other_attributes | various                        | Any additional attributes related to buildings (optional, preserved during processing). |

**Example Buildings Geodataframe**

| geometry                                                                                     | building_id | other_attributes                           |
| -------------------------------------------------------------------------------------------- | ----------- | ------------------------------------------ |
| Point(x1, y1)                                                                                | 1           | {'name': 'House A', 'type': 'residential'} |
| Polygon(((x2, y2), (x3, y3), (x4, y4), (x5, y5)))                                            | 2           | {'name': 'House B', 'type': 'residential'} |
| MultiPolygon(((x6, y6), (x7, y7), (x8, y8), (x9, y9)), ((x10, y10), (x11, y11), (x12, y12))) | 3           | {'name': 'House C', 'type': 'residential'} |

> [!NOTE]  
> The buildings data is expected to be a Point, Polygon, or MultiPolygon geometry with a valid CRS. Ideally point geometries are preferred, however we added a function convert polygons or multi-polygons to points.  
> The buildings data can include additional attributes that will be preserved during the preprocessing.  
> To avoid issues with preprocessing, we recommend to project the data into a UTM-zone that matches the area of interest.  

### Preprocessing

The main objective of sewer layout generation is to connect all buildings to a waste water treatment plant (WWTP) while keeping system cost low. The initial graph represents all potential sewer lines in our model domain.

Preprocessing comes down to:

- "connecting" buildings to the street network
- clustering of buildings surpassing a predefined threshold
- contracting the street network for more efficient graph traversal

After preprocessing, all relevant data is and stored as a MultiDiGraph to allow for asymmetric edge values (e.g. elevation profile and subsequently costs).

### Graph Attributes

```yaml
Node Attributes:
    "node_type": "building","wwtp"
    "elevation"
    "pumping_station": bool
    "lifting_station":bool
Edge Attributes:
    "geometry": detailed shapely line
    "length"
    "diameter"
    "pressurized": bool
    "profile"
    "needs_pump": bool
    "private_sewer":bool
    "weight": value representing arbitrary cost function
```

## Routing Solver

![Routing Animation](/notebooks/example_data/plots/rsph.gif)

The package comes with two solvers to find estimates for the underlying steiner tree problem (more specifically minimum steiner arboresence).

- RSPH
- RSPH Fast

---

The _RSPH solver_ iteratively connects the nearest unconnected node (in terms of distance and pump penalty) to the closest connected network node. The solver can account for multiple sinks and is therefore well suited to generate decentralized network scenarios.

The _RSPH Fast_ solver derives the network by combining all shortest paths to a single sink. Faster, but only allows for a single sink.

## Plotting

```python
info = pysewer.get_sewer_info(G)
info["Routing Solver"] = "RSPH"
info["Pump Penalty"] = test_model_domain.pump_penalty
fig,ax = pysewer.plot_model_domain(test_model_domain, plot_sewer=True,sewer_graph = G, info_table=info)
```

```python
pysewer.plot_sewer_attributes(test_model_domain,G,attribute="peak_flow",title="Peak Flow Estimation m³/s")
plt.show()
```

## Export

```python
sewer_network_gdf = pysewer.get_edge_gdf(G,detailed=True)
pysewer.export_sewer_network(sewer_network_gdf, "sewer_network.gpkg")
```

## Default parameters

The default or global parameters are stored in the [settings.yaml](pysewer/config/settings.yaml) file. This file can be overwritten by specifying a custom settings file (e.g.[example_settings.yaml](notebooks/example_settings.yaml)) and passing it to the `load_config(custom_settings.yaml)` function. The settings parameters are categorized into 3 sections, namely `preprocessing`, `optimization` and `plotting`.

The table below summaries the key default parameters and their meaning.

| Parameter                 | Description                                                                                                      | Default |
| ------------------------- | ---------------------------------------------------------------------------------------------------------------- | ------- |
| `dem_file_path`           | Path for the DEM file                                                                                            | None    |
| `roads_input_data`        | Path for the road input data                                                                                     | None    |
| `buildings_input_data`    | Path for the buildings input data                                                                                | None    |
| `pump_penalty`            | Penalty for using a pump in the cost function                                                                    | 1000    |
| `dx`                      | Sampling resolution, used for extracting elevation data from the DEM (in meters)                                 | 10      |
| `max_connection_length`   | The maximum distance between a building and the nearest street for it to be included in the cluster centers list | 30      |
| `inhabitants_dwelling`    | The number of inhabitants per dwelling.                                                                          | 3       |
| `daily_wastewater_person` | The daily wastewater generated per person in m³                                                                  | 0.2     |
| `peak_factor`             | Peak factor for wastewater                                                                                       | 2.3     |
| `min_slope`               | The minimum slope required for gravitational flow.                                                               | -0.1    |
| `tmax`                    | Maximum trench depth allowed (meters)                                                                            | 8       |
| `tmin`                    | Minimum trench depth allowed (meters)                                                                            | 0.25    |
| `min_trench_depth`        | Lowest possible trench depth                                                                                     | 0       |
| `diameters`               | List of diameters to be considered (meters)                                                                      | List [] |
| `pressurized_diameter`    | Diameter of pressure pipes to be used (meters)                                                                   | 0.2     |
| `roughness`               | The pipe roughness coefficient in meters                                                                         | 0.013   |

## License

GNU GPLv3-modified-UFZ. See [LICENSE](LICENSE) for details.

# How to contribute to pysewer?

Please check out how [Contributing](CONTRIBUTING.md) for on how to contribute to pysewer. Please note that we have created a mirror repository on [Github](https://github.com/dbdespot/pysewer) to allow for easier contribution. The original repository is hosted on [Gitlab](https://git.ufz.de/despot/pysewer).

## Code of conduct

Please check out our [Code of Conduct](CODE_OF_CONDUCT.md) for details.

## How to cite?

Currently, pysewer is under review in the Journal of Open Source Software (JOSS). Please check back later.
