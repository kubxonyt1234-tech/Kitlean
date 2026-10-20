"""Disk-backed segment snapshots. Only the active segment has live entities."""

import copy
import json
import sqlite3

from .errors import KitleanError


class Segments:
    def __init__(self, world, menu):
        self.world = world
        self.menu = menu
        self.coord = (0, 0)
        self.identifier = menu
        self.previous = None
        self.restored = False
        self.generation = 0
        self.connection = None
        path = world.runtime.storage.path.parent / ("world_" + menu + ".sqlite3")
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            self.connection = sqlite3.connect(path)
            self.connection.execute("PRAGMA cache_size=-512")
            self.connection.execute(
                "CREATE TABLE IF NOT EXISTS segments (id INTEGER PRIMARY KEY AUTOINCREMENT, x INTEGER, y INTEGER, data TEXT NOT NULL, UNIQUE(x,y))"
            )
            self.connection.execute(
                "INSERT OR IGNORE INTO segments(id,x,y,data) VALUES(0,0,0,'{}')"
            )
            self.connection.commit()
        except (OSError, sqlite3.Error) as error:
            if self.connection:
                self.connection.close()
            raise KitleanError(
                "Cannot initialize segment storage: " + str(error), world.runtime.line
            ) from None

    def snapshot(self, traveler):
        rt = self.world.runtime
        entities = []
        for entity in rt.objects.values():
            if (
                entity.kind == "item.sprite"
                and entity.parent == self.menu
                and entity.name != traveler
                and not getattr(entity, "template", False)
            ):
                entities.append(
                    {
                        "name": entity.name,
                        "properties": copy.deepcopy(entity.properties),
                        "velocity": getattr(entity, "velocity", 0.0),
                        "state": {
                            field: copy.deepcopy(getattr(entity, field))
                            for field in (
                                "grounded",
                                "animation_state",
                                "visual_animation",
                                "visual_phase",
                            )
                            if hasattr(entity, field)
                        },
                    }
                )
        return {
            "entities": entities,
            "background": rt.get(self.menu).properties["background"],
        }

    def transition(self, traveler, direction):
        rt = self.world.runtime
        actor = rt.get(traveler)
        dx, dy = direction
        target = (self.coord[0] + dx, self.coord[1] + dy)
        try:
            row = self.connection.execute(
                "SELECT id,data FROM segments WHERE x=? AND y=?", target
            ).fetchone()
            payload = json.loads(row[1]) if row else {}
            if not isinstance(payload, dict) or not isinstance(
                payload.get("entities", []), list
            ):
                raise ValueError("Invalid segment record")
            outgoing = {
                e.name for e in self.world.sprites(self.menu) if e.name != traveler
            }
            names = set()
            for saved in payload.get("entities", []):
                name = saved["name"]
                props = saved["properties"]
                if (
                    not isinstance(name, str)
                    or not name.isidentifier()
                    or name in names
                    or name in rt.objects
                    and name not in outgoing
                ):
                    raise ValueError("Segment alias conflict: " + str(name))
                if name == traveler:
                    raise ValueError("Segment snapshot contains the traveler")
                self.world.source(props["file"])
                self.world.coordinates(props["position"])
                names.add(name)
                if not rt.asset_path(props["file"]).is_file():
                    raise ValueError("Missing sprite asset: " + props["file"])
            current = json.dumps(self.snapshot(traveler), allow_nan=False)
            with self.connection:
                self.connection.execute(
                    "UPDATE segments SET data=? WHERE x=? AND y=?",
                    (current, *self.coord),
                )
                if row is None:
                    cursor = self.connection.execute(
                        "INSERT INTO segments(x,y,data) VALUES(?,?,'{}')", target
                    )
                    target_id = cursor.lastrowid
                else:
                    target_id = row[0]
                identifier = self.menu if target_id == 0 else self.menu + str(target_id)
                if identifier in rt.objects and identifier != self.menu:
                    raise ValueError(
                        "Segment identifier conflicts with object alias: " + identifier
                    )
        except (sqlite3.Error, ValueError, KeyError, TypeError, OSError) as error:
            raise KitleanError(
                "Segment transition failed: " + str(error), rt.line
            ) from None
        previous = self.identifier
        for name in outgoing:
            rt.remove(name, suspend=True)
        for saved in payload.get("entities", []):
            entity = rt.create("item.sprite", saved["name"])
            entity.properties = copy.deepcopy(saved["properties"])
            entity.parent = self.menu
            entity.velocity = saved.get("velocity", 0.0)
            for field in (
                "grounded",
                "animation_state",
                "visual_animation",
                "visual_phase",
            ):
                if field in saved.get("state", {}):
                    setattr(entity, field, copy.deepcopy(saved["state"][field]))
        if "background" in payload:
            rt.get(self.menu).properties["background"] = payload["background"]
        self.previous = previous
        self.coord = target
        self.identifier = self.menu if target_id == 0 else self.menu + str(target_id)
        self.restored = row is not None
        self.generation += 1
        width, height = rt.get(self.menu).properties["size"]
        w, h = self.world.dimensions(actor)
        x, y = actor.properties["position"]
        if dx:
            x = 1.0 if dx > 0 else max(0.0, width - w - 1)
        if dy:
            y = 1.0 if dy > 0 else max(0.0, height - h - 1)
        actor.properties["position"] = (
            min(max(x, 0), max(0, width - w)),
            min(max(y, 0), max(0, height - h)),
        )
        actor.grounded = False
        self.world.contacts.clear()
        self.world.outside.clear()
        if rt.windows.root is not None:
            rt.windows.refresh()
        return True

    def release_previous(self):
        if self.previous is None:
            raise KitleanError(
                "No successfully saved previous segment", self.world.runtime.line
            )
        # Previous live entities are already released atomically after the disk save.
        return True

    def close(self):
        if self.connection is not None:
            self.connection.close()
            self.connection = None
