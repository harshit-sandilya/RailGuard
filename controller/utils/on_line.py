def on_line(point, line_start, line_end):
    """Check if a point is on a line segment defined by two endpoints"""
    x, y = point
    x1, y1 = line_start
    x2, y2 = line_end

    if not (min(x1, x2) <= x <= max(x1, x2) and min(y1, y2) <= y <= max(y1, y2)):
        return False
    cross_product = (y - y1) * (x2 - x1) - (x - x1) * (y2 - y1)
    return abs(cross_product) < 1e-9
