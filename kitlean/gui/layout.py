def arrange(elements):
    """Zwraca pozycje elementów; rozmiary naturalne odczytuje po aktualizacji Tk."""
    y = 20
    positions = {}
    for item in elements:
        if not item.properties["visible"]:
            continue
        w = item.widget
        size = item.properties["size"]
        height = size[1] if size else w.winfo_reqheight()
        position = item.properties["position"]
        if position is None:
            position = (20, y)
            y += height + 12
        else:
            y = max(y, position[1] + height + 12)
        positions[item.name] = position
    return positions
