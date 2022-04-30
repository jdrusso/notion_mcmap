import requests
import json
import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial import Voronoi, voronoi_plot_2d
from matplotlib.patches import Patch
import requests, json
from adjustText import adjust_text

token = open('api_key', 'r').read()

# Just a biome marker, no region of interest
ignored = ['-']

skipped = ['Source']

def generate_maps():

    _json_defs = json.load(open('definitions.json', 'r'))
    biome_colors = _json_defs['biome_colors']
    custom_markers = _json_defs['custom_markers']

    database_id = '8950d22ace384c5a8f0f4001c1244d88'

    url = f"https://api.notion.com/v1/databases/{database_id}/query"

    payload = {"page_size": 100}

    headers = {
        "Authorization": "Bearer " + token,

        "Accept": "application/json",

        "Notion-Version": "2022-02-22",

        "Content-Type": "application/json"

    }

    response = requests.post(url, json=payload, headers=headers)

    response_json = json.loads(response.text)

    rows = response_json['results']

    locations = []

    for location_row in rows:

        x, y, z = (location_row['properties'][_loc]['number'] for _loc in 'XYZ')

        name = location_row['properties']['Name']['title'][0]['plain_text']
        tags = location_row['properties']['Biome']

        if None in [x, z] or name in skipped:
            continue

        locations.append(
            [name, x, y, z, tags]
        )

    locations.append(['dummy', 1e6, 0, 0, None])
    locations.append(['dummy', -1e6, 0, 0, None])
    locations.append(['dummy', 0, 0, 1e6, None])
    locations.append(['dummy', 0, 0, -1e6, None])
    locations_array = np.array(locations)

    # Get biomes for all points, if provided

    # Using locations as centers, make voronoi clusters of biomes..

    biome_data_list = []
    for idx, row in enumerate(locations_array):

        if row[4] is not None:
            _biome_data = [(int(idx), item['name'], item['color']) for item in row[4]['multi_select']]

        else:
            _biome_data = [[idx, 'dummy', 'white']]

        biome_data_list.extend(_biome_data)

    biome_data = np.array(biome_data_list)
    biome_idxs = [int(x[0]) for x in biome_data]

    assert len(biome_data) == locations_array[biome_idxs].shape[0]

    x_y = np.array([locations_array[biome_idxs, 1], locations_array[biome_idxs, 3]]).T
    vor = Voronoi(x_y)

    fig, ax = plt.subplots(figsize=(8, 8), dpi=200)

    voronoi_plot_2d(vor, ax=ax, show_points=False, show_vertices=False, line_alpha=0.2)
    for r in range(len(vor.point_region)):
        region = vor.regions[vor.point_region[r]]

        biome_name, biome_color = biome_data[r, 1], biome_data[r, 2]
        color = biome_colors.get(biome_name, 'white')

        if not -1 in region:
            polygon = [vor.vertices[i] for i in region]
            plt.fill(*zip(*polygon), color=color)

    # Make a legend for the colors
    legend_elements = [Patch(facecolor=color, label=label) for (label, color) in biome_colors.items()]
    ax.legend(handles=legend_elements, loc='lower left', fontsize=12)

    scaling = 200
    x_range = np.array([min(locations_array[:-4, 1]) - scaling, scaling + max(locations_array[:-4, 1])])
    z_range = np.array([min(locations_array[:-4, 3]) - scaling, scaling + max(locations_array[:-4, 3])])
    ax.set_xlim(x_range)
    ax.set_ylim(z_range)
    plt.xlabel('X', fontsize=14)
    plt.ylabel('Z', fontsize=14)  # heh

    # ax.scatter(locations_array[:-4, 1], locations_array[:-4, 3], s=100, color='k', marker='o')
    texts = []
    offsets = np.random.randint(20, 50, size=(len(locations_array), 2))
    offsets = offsets * np.random.choice([-1, 1], size=offsets.shape)
    for i, row in enumerate(locations_array[:-4]):

        name = row[0]
        # Don't show a marker for some
        if name in ignored: continue

        _x = row[1]
        _y = row[3]

        marker = custom_markers.get(name, 'o')
        ax.scatter(_x, _y, s=100, color='k', marker=marker, zorder=4)

        texts.append(
            ax.text(_x, _y, name,
                    fontsize=12,
                    fontweight='bold',
                    bbox={'boxstyle': 'round', 'fc': 'white', 'ec': 'white', 'alpha': 0.3})
        )

    adjust_text(texts,
                x=locations_array[:, 1],
                y=locations_array[:, 3],
                # expand_text=(1.3,1.7),
                expand_points=(1.5, 1.7),
                # only_move={'text':'y'}
                arrowprops=dict(arrowstyle='-', color='black', linewidth=1)
                )

    fig.patch.set_facecolor('white')
    ax.patch.set_facecolor('white')
    plt.tight_layout()
    plt.savefig('map.png')

    return fig, ax

# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    generate_maps()

    plt.show()

