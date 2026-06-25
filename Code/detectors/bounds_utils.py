def normalize_bounds(bounds):
    x_min = min(bounds[0][0], bounds[1][0])
    y_min = min(bounds[0][1], bounds[1][1])
    x_max = max(bounds[0][0], bounds[1][0])
    y_max = max(bounds[0][1], bounds[1][1])
    return [x_min, y_min, x_max, y_max]
