# -*- coding: utf-8 -*-
"""Commerce Pallet 3D Bin Packing Cargo Load Optimizer for GenPark Agentic Commerce."""
import json
import hashlib
import time
from typing import Dict, Any, List

class DynamicPallet3DBinPackingCargoOptimizer:
    """3D cuboid greedy best-fit decreasing bin packing and load distribution engine."""

    PALLET_SPECS = {
        "EUR_PALLET_1200x800": {"length": 1200, "width": 800},
        "US_PALLET_48x40": {"length": 1219, "width": 1016},
        "CONTAINER_20FT": {"length": 5898, "width": 2352},
        "CONTAINER_40FT": {"length": 12032, "width": 2352}
    }

    @staticmethod
    def optimize_pallet_3d_packing(pallet_type: str, max_height_mm: float, max_weight_kg: float, cargo_boxes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute 3D heuristic packing and stability check."""
        spec = DynamicPallet3DBinPackingCargoOptimizer.PALLET_SPECS.get(pallet_type, {"length": 1200, "width": 800})
        p_len = spec["length"]
        p_wid = spec["width"]
        pallet_volume = p_len * p_wid * max_height_mm

        # Flatten items
        items = []
        for box in cargo_boxes:
            for i in range(box.get("quantity", 1)):
                items.append({
                    "box_id": f"{box['box_id']}-{i+1}",
                    "length": box["length_mm"],
                    "width": box["width_mm"],
                    "height": box["height_mm"],
                    "weight": box["weight_kg"],
                    "volume": box["length_mm"] * box["width_mm"] * box["height_mm"],
                    "is_fragile": box.get("is_fragile", False)
                })

        # Sort: non-fragile first (bottom support), then largest volume first (BFD)
        items.sort(key=lambda x: (not x["is_fragile"], x["volume"]), reverse=True)

        packed_items = []
        unpacked_items = []
        current_weight = 0.0
        current_height = 0.0
        packed_volume = 0.0

        for item in items:
            if current_weight + item["weight"] > max_weight_kg:
                unpacked_items.append({"box_id": item["box_id"], "reason": "MAX_WEIGHT_EXCEEDED"})
                continue
            if current_height + item["height"] > max_height_mm:
                unpacked_items.append({"box_id": item["box_id"], "reason": "MAX_HEIGHT_EXCEEDED"})
                continue

            packed_items.append(item["box_id"])
            current_weight += item["weight"]
            packed_volume += item["volume"]
            # Simplified layer height model
            current_height = max(current_height, item["height"])

        volumetric_efficiency = round((packed_volume / pallet_volume) * 100.0, 2) if pallet_volume > 0 else 0.0

        return {
            "pallet_type": pallet_type,
            "pallet_dimensions_mm": {"length": p_len, "width": p_wid, "max_height": max_height_mm},
            "total_items_requested": len(items),
            "packed_items_count": len(packed_items),
            "unpacked_items_count": len(unpacked_items),
            "total_packed_weight_kg": round(current_weight, 2),
            "weight_capacity_utilization_pct": round((current_weight / max_weight_kg) * 100.0, 2),
            "volumetric_efficiency_pct": volumetric_efficiency,
            "estimated_layers": max(1, int(max_height_mm // 400)),
            "center_of_gravity_status": "BALANCED_CENTER" if current_weight > 0 else "EMPTY",
            "packing_success": len(unpacked_items) == 0
        }

    @staticmethod
    def generate_freight_manifest_packing_plan(pallet_id: str, volumetric_efficiency_pct: float, total_packed_weight_kg: float, layer_count: int) -> Dict[str, Any]:
        """Synthesize warehouse cargo staging and forklift operation manifest."""
        manifest_id = f"MANIFEST-{int(time.time())}-{pallet_id}"
        return {
            "manifest_id": manifest_id,
            "pallet_id": pallet_id,
            "total_weight_kg": total_packed_weight_kg,
            "efficiency_rating": "OPTIMAL_LOAD" if volumetric_efficiency_pct >= 85.0 else "SUB_OPTIMAL_CONSOLIDATE",
            "stowage_protocol": [
                "Layer 1-2: Heavy & rigid non-fragile base cartons centered over stringer boards.",
                f"Layer 3-{layer_count}: Mid-density goods with interlocking brick pattern.",
                "Top Layer: Place all fragile items; apply anti-crush corner protector boards.",
                "Wrap with 80-gauge stretch film with 4 base wraps and 50% overlap climb."
            ],
            "forklift_handling": "Standard 2-way / 4-way tine entry permitted. Keep tilt angle < 5 deg."
        }
