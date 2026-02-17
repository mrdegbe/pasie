def merge_zones(bos_zones, base_zones):

    supply = []
    demand = []

    for z in bos_zones + base_zones:

        if z["type"] == "supply":
            supply.append(z)

        else:
            demand.append(z)

    return supply, demand
