# -*- coding: utf-8 -*-
"""MCP Server for Commerce Pallet 3D Bin Packing Cargo Load Optimizer Skill."""
import sys
import json
import logging
from typing import Dict, Any

from .core import DynamicPallet3DBinPackingCargoOptimizer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

TOOLS_SCHEMA = [
    {
        "name": "optimize_pallet_3d_packing",
        "description": "Compute optimal 3D pallet cuboid packing layout, volumetric efficiency percentage, and center-of-gravity stability coordinates.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pallet_type": {
                    "type": "string",
                    "enum": [
                        "EUR_PALLET_1200x800",
                        "US_PALLET_48x40",
                        "CONTAINER_20FT",
                        "CONTAINER_40FT"
                    ]
                },
                "max_height_mm": {
                    "type": "number"
                },
                "max_weight_kg": {
                    "type": "number"
                },
                "cargo_boxes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "box_id": {
                                "type": "string"
                            },
                            "length_mm": {
                                "type": "number"
                            },
                            "width_mm": {
                                "type": "number"
                            },
                            "height_mm": {
                                "type": "number"
                            },
                            "weight_kg": {
                                "type": "number"
                            },
                            "is_fragile": {
                                "type": "boolean"
                            },
                            "quantity": {
                                "type": "integer"
                            }
                        },
                        "required": [
                            "box_id",
                            "length_mm",
                            "width_mm",
                            "height_mm",
                            "weight_kg",
                            "quantity"
                        ]
                    }
                }
            },
            "required": [
                "pallet_type",
                "max_height_mm",
                "max_weight_kg",
                "cargo_boxes"
            ]
        }
    },
    {
        "name": "generate_freight_manifest_packing_plan",
        "description": "Generate step-by-step layer placement sequence and forklift loading safety manifest.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pallet_id": {
                    "type": "string"
                },
                "volumetric_efficiency_pct": {
                    "type": "number"
                },
                "total_packed_weight_kg": {
                    "type": "number"
                },
                "layer_count": {
                    "type": "integer"
                }
            },
            "required": [
                "pallet_id",
                "volumetric_efficiency_pct",
                "total_packed_weight_kg",
                "layer_count"
            ]
        }
    }
]

def handle_rpc(line: str) -> str:
    try:
        req = json.loads(line)
        method = req.get("method")
        msg_id = req.get("id")

        if method == "initialize":
            res = {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "genpark-agentic-commerce-dynamic-pallet-3d-bin-packing-cargo-load-skill", "version": "1.0.0"}
            }
            return json.dumps({"jsonrpc": "2.0", "id": msg_id, "result": res})

        elif method == "tools/list":
            return json.dumps({"jsonrpc": "2.0", "id": msg_id, "result": {"tools": TOOLS_SCHEMA}})

        elif method == "tools/call":
            params = req.get("params", {})
            tool_name = params.get("name")
            args = params.get("arguments", {})

            target_func = getattr(DynamicPallet3DBinPackingCargoOptimizer, tool_name, None)
            if not target_func:
                return json.dumps({"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32601, "message": f"Method not found: {tool_name}"}})

            result = target_func(**args)
            return json.dumps({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(result, indent=2)}]
                }
            })

        else:
            return json.dumps({"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32601, "message": f"Method not found: {method}"}})

    except Exception as e:
        return json.dumps({"jsonrpc": "2.0", "id": req.get("id") if "req" in locals() else None, "error": {"code": -32000, "message": str(e)}})

def run_test():
    print("[TEST] Running internal RPC self-test for genpark-agentic-commerce-dynamic-pallet-3d-bin-packing-cargo-load-skill...")
    init_req = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    init_res = json.loads(handle_rpc(init_req))
    assert init_res.get("result", {}).get("serverInfo", {}).get("name") == "genpark-agentic-commerce-dynamic-pallet-3d-bin-packing-cargo-load-skill"

    list_req = json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
    list_res = json.loads(handle_rpc(list_req))
    assert len(list_res.get("result", {}).get("tools", [])) == 2
    print(f"[TEST] SUCCESS: {len(list_res['result']['tools'])} tools verified.")
    return True

if __name__ == "__main__":
    if "--test" in sys.argv:
        if run_test():
            sys.exit(0)
        sys.exit(1)

    for line in sys.stdin:
        if not line.strip():
            continue
        out = handle_rpc(line)
        sys.stdout.write(out + "\n")
        sys.stdout.flush()
