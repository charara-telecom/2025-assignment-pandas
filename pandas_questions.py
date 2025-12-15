"""Plotting referendum results in pandas.

In short, we want to make beautiful map to report results of a referendum.
In some way, we would like to depict results with something similar to the
maps that you can find here:
https://github.com/x-datascience-datacamp/datacamp-assignment-pandas/blob/main/example_map.png

To do that, you will load the data as pandas.DataFrame, merge the info and
aggregate them by regions and finally plot them on a map using `geopandas`.
"""
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt


def load_data():
    """Load data from the CSV files referundum/regions/departments."""
    referendum = pd.read_csv("./data/referendum.csv", sep=";")
    regions = pd.read_csv("./data/regions.csv")
    departments = pd.read_csv("./data/departments.csv")
    return referendum, regions, departments


def merge_regions_and_departments(regions, departments):
    """Merge regions and departments in one DataFrame.

    The columns in the final DataFrame should be:
    ['code_reg', 'name_reg', 'code_dep', 'name_dep']
    """
    reg = regions.rename(
        columns={"code": "code_reg", "name": "name_reg"}
    )[["code_reg", "name_reg"]]

    dep = departments.rename(
        columns={
            "region_code": "code_reg",
            "code": "code_dep",
            "name": "name_dep",
        }
    )[["code_reg", "code_dep", "name_dep"]]

    merged = dep.merge(reg, on="code_reg", how="left")
    merged = merged[["code_reg", "name_reg", "code_dep", "name_dep"]]
    return merged


def merge_referendum_and_areas(referendum, regions_and_departments):
    """Merge referendum and regions_and_departments in one DataFrame.

    Drop DOM-TOM-COM + abroad lines: codes containing `Z`.
    """
    ref = referendum.copy()

    ref["Department code"] = (
        ref["Department code"]
        .astype("string")
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
        .str.zfill(2)
    )

    ref = ref[~ref["Department code"].str.contains("Z", na=False)]

    merged = ref.merge(
        regions_and_departments,
        left_on="Department code",
        right_on="code_dep",
        how="left",
    )

    merged = merged.dropna()
    return merged


def compute_referendum_result_by_regions(referendum_and_areas):
    """Return a table with the absolute count for each region.

    Indexed by `code_reg` with columns:
    ['name_reg', 'Registered', 'Abstentions', 'Null', 'Choice A', 'Choice B']
    """
    df = referendum_and_areas.copy()

    cols = ["Registered", "Abstentions", "Null", "Choice A", "Choice B"]
    for col in cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    agg = (
        df.groupby(["code_reg", "name_reg"], as_index=False)[cols]
        .sum()
        .set_index("code_reg")
    )

    agg = agg[["name_reg"] + cols]
    return agg


def plot_referendum_map(referendum_result_by_regions):
    """Plot a map with the results from the referendum.

    - Load `regions.geojson`
    - Merge with results
    - Plot ratio = Choice A / (Choice A + Choice B)
    - Return the GeoDataFrame with a 'ratio' column
    """
    gdf_regions = gpd.read_file("./data/regions.geojson")

    results = referendum_result_by_regions.copy().reset_index()

    expressed = (results["Choice A"] + results["Choice B"]).replace(0, pd.NA)
    results["ratio"] = results["Choice A"] / expressed

    possi_code_cols = ["code", "code_reg", "region_code", "reg_code", "insee"]
    geo_code_col = next(
        (col for col in possi_code_cols if col in gdf_regions.columns),
        None,
    )
    if geo_code_col is None:
        raise KeyError(
            "No region code column found in geojson. Columns are: "
            f"{list(gdf_regions.columns)}"
        )

    gdf_regions[geo_code_col] = (
        gdf_regions[geo_code_col].astype("string").str.strip()
    )
    results["code_reg"] = results["code_reg"].astype("string").str.strip()

    gdf = gdf_regions.merge(
        results,
        left_on=geo_code_col,
        right_on="code_reg",
        how="left",
    )

    ax = plt.gca()
    gdf.plot(
        column="ratio",
        ax=ax,
        legend=True,
        missing_kwds={"color": "lightgrey", "label": "No data"},
        edgecolor="black",
        linewidth=0.4,
    )
    ax.set_axis_off()
    ax.set_title("Referendum results by region (Choice A / expressed)")

    return gdf


if __name__ == "__main__":
    referendum, df_reg, df_dep = load_data()
    regions_and_departments = merge_regions_and_departments(df_reg, df_dep)
    referendum_and_areas = merge_referendum_and_areas(
        referendum, regions_and_departments
    )
    referendum_results = compute_referendum_result_by_regions(
        referendum_and_areas
    )
    print(referendum_results)

    plot_referendum_map(referendum_results)
    plt.show()
