#!/bin/bash

declare -A MODELS=(
    ["qwen2.5:7b"]="General-purpose coding and logical reasoning assistant"
    ["qwen2.5:14b"]="Heavyweight multi-step programming and logic analysis model"
    ["llama3.1:latest"]="Robust general knowledge, drafting, and conversational agent"
    ["gpt-oss:120b-cloud"]="Large-scale synthetic reasoning and architecture consultant"
    ["gemma4:cloud"]="Advanced agile assistant for general queries and processing"
    ["laguna-xs-2.1:latest"]="Lightweight edge-optimized utility and scripting assistant"
    ["qwen3.6:27b"]="High-capacity deep context analysis and architecture engine"
    ["qwen3.8b"]="Fast compact utility parser and syntax checker"
    ["llama3.2:latest"]="Efficient everyday task execution and summarization agent"
    ["gemma4:12b"]="Mid-scale general assistant and creative assistant"
)

echo "=================================================="
echo "🚀 Starting Ollama Model Provisioning & Build Script"
echo "=================================================="

for model in "${!MODELS[@]}"; do
    desc="${MODELS[$model]}"
    echo ""
    echo "--------------------------------------------------"
    echo "Processing target: [$model]"
    echo "Role description : $desc"
    echo "--------------------------------------------------"

    if ! ollama list | grep -q "$model"; then
        echo "📥 Pulling base model $model..."
        ollama pull "$model"
    else
        echo "✅ Base model $model already present locally."
    fi

    TEMP_FILE="Modelfile_temp"
    cat <<INNEREOF > "$TEMP_FILE"
FROM $model
SYSTEM "You are $model, optimized for: $desc. Always deliver precise, direct, and production-ready outputs."
PARAMETER temperature 0.3
INNEREOF

    echo "🔨 Building custom tag: $model"
    ollama create "$model" -file "$TEMP_FILE"
    
    rm -f "$TEMP_FILE"
    echo "✨ Finished configuring $model"
done

echo ""
echo "=================================================="
echo "🎉 All models built successfully and synced to Ollama!"
echo "=================================================="
