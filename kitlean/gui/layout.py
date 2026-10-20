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
        margin = item.properties["margin"]
        if position is None and not positions:
            y = margin
        if position is None:
            parent_width = w.master.winfo_width()
            width = size[0] if size else w.winfo_reqwidth()
            align = item.properties["align"]
            x = (
                max(margin, (parent_width - width) / 2)
                if align == "center"
                else max(margin, parent_width - width - margin)
                if align == "right"
                else margin
            )
            position = (x, y)
            y += height + 12
        else:
            y = max(y, position[1] + height + 12)
        positions[item.name] = position
    return positions
