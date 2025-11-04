"""JSON schema contracts shared with the Responses API."""

# RESEARCH (LLM output)
RESEARCH_SCHEMA = {
  "type": "object",
  "additionalProperties": False,
  "properties": {
    "references": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
          "url": {"type": "string"},
          "title": {"type": "string"},
          "type": {"type": "string", "enum": ["gallery","article","store","blog","community","other"]},
          "summary": {"type":"string"}
        },
        "required": ["url","title","type"]
      }
    },
    "designs": {
      "type":"array",
      "items":{
        "type":"object",
        "additionalProperties": False,
        "properties":{
          "motifs":{"type":"array","items":{"type":"string"}},
          "composition":{"type":"array","items":{"type":"string"}},
          "line":{"type":"string","enum":["ultra-thin","thin","regular","bold"]},
          "outline":{"type":"string","enum":["none","clean","heavy","rough"]},
          "typography":{"type":"array","items":{"type":"string"}},
          "palette":{
            "type":"array",
            "items":{
              "type":"object",
              "additionalProperties": False,
              "properties":{"hex":{"type":"string"},"weight":{"type":"number"}},
              "required":["hex","weight"]
            }
          },
          "mood":{"type":"array","items":{"type":"string"}},
          "hooks":{"type":"array","items":{"type":"string"}},
          "notes":{"type":"array","items":{"type":"string"}}
        },
        "required":["motifs","composition","line","outline","typography","palette","mood","hooks","notes"]
      }
    },
    "palette": {  # global palette suggestion (optional)
      "type":"array",
      "items":{"type":"object","properties":{"hex":{"type":"string"},"weight":{"type":"number"}}, "required":["hex","weight"]}
    },
    "notes":{"type":"string"},

    # NEW: distributions
    "color_distribution":{
      "type":"array",
      "items":{
        "type":"object","additionalProperties": False,
        "properties":{
          "area":{"type":"string","enum":["background","foreground","focal","accent","text","other"]},
          "hex":{"type":"string"},
          "weight":{"type":"number"}  # 0..1 across entire frame
        },
        "required":["area","hex","weight"]
      }
    },
    "light_distribution":{
      "type":"object",
      "additionalProperties": False,
      "properties":{
        "direction":{"type":"string"},                # e.g., "top-left", "rim-right", "backlit"
        "key":{"type":"number"}, "fill":{"type":"number"}, "rim":{"type":"number"}, "ambient":{"type":"number"},
        "zones":{
          "type":"array",
          "items":{"type":"object","properties":{"area":{"type":"string"}, "intensity":{"type":"number"}, "notes":{"type":"string"}}, "required":["area","intensity"]}
        },
        "notes":{"type":"string"}
      },
      "required":["direction"]
    },
    "gradient_distribution":{
      "type":"array",
      "items":{
        "type":"object","additionalProperties": False,
        "properties":{
          "allow":{"type":"boolean"},                           # true if gradients acceptable for target media
          "type":{"type":"string","enum":["linear","radial","conic"]},
          "angle":{"type":"number"},
          "center":{"type":"object","properties":{"x":{"type":"number"},"y":{"type":"number"}}},
          "stops":{
            "type":"array",
            "items":{"type":"object","properties":{"hex":{"type":"string"},"pos":{"type":"number"},"weight":{"type":"number"}}, "required":["hex","pos"]}
          },
          "areas":{"type":"array","items":{"type":"string"}},   # where to apply
          "vector_approximation_steps":{"type":"integer"}       # if allow=false, suggest 3-7 stepped bands
        },
        "required":["allow","type","stops","areas"]
      }
    }
  },
  "required": ["references","designs","color_distribution","light_distribution","gradient_distribution"]
}

# SYNTHESIS (LLM output)
SYNTHESIS_SCHEMA = {
  "type":"object","additionalProperties": False,
  "properties":{
    "prompts":{
      "type":"array",
      "items":{
        "type":"object","additionalProperties": False,
        "properties":{
          "title":{"type":"string"},
          "positive":{"type":"string"},
          "negative":{"type":"array","items":{"type":"string"}},
          "notes":{"type":"string"},

          # NEW: carry explicit distributions to the generation stage
          "palette_distribution":{"type":"array","items":{"type":"object","properties":{"hex":{"type":"string"},"weight":{"type":"number"}}, "required":["hex","weight"]}},
          "light_distribution": RESEARCH_SCHEMA["properties"]["light_distribution"],
          "gradient_distribution": RESEARCH_SCHEMA["properties"]["gradient_distribution"],

          "constraints":{
            "type":"object","additionalProperties": False,
            "properties":{
              "transparent_background":{"type":"boolean"},
              "vector_safe":{"type":"boolean"},
              "gradient_mode":{"type":"string","enum":["stepped-bands","true-gradients"]} # switch by env
            }
          }
        },
        "required":["positive","negative","palette_distribution","light_distribution","gradient_distribution"]
      }
    }
  },
  "required":["prompts"]
}
