# 3. Context and Scope

## Business Context

Users provide source videos and receive fully processed videos ready for publication, complete with thumbnail overlays and generated metadata.

```mermaid
flowchart LR
    User([User])
    VP[Video Processor]
    Output([Processed Video + Metadata])

    User -->|"video + theme + options"| VP
    VP -->|"video.mp4 + metadata.json"| Output
```

## Technical Context

```mermaid
flowchart TB
    subgraph "Video Processor"
        CLI[CLI Layer]
        Pipeline[Pipeline Orchestrator]
        Modules[Processing Modules]
    end

    subgraph "External Systems"
        FFmpeg[FFmpeg Binary]
        NeMo[NeMo Toolkit]
        Whisper[OpenAI Whisper]
        Claude[Claude API]
    end

    subgraph "File System"
        Input[input/]
        Output[output/]
        Processing[processing/]
        Thumbnails[thumbnails/]
        Config[~/.config/video-processor/]
    end

    CLI --> Pipeline
    Pipeline --> Modules

    Modules <-->|"video/audio ops"| FFmpeg
    Modules <-->|"English transcription"| NeMo
    Modules <-->|"Non-English transcription"| Whisper
    Modules <-->|"metadata generation"| Claude

    Modules <-->|"read"| Input
    Modules <-->|"read"| Thumbnails
    Modules <-->|"read/write"| Processing
    Modules <-->|"write"| Output
    Pipeline <-->|"read API key"| Config
```

## External Interfaces

### FFmpeg

- **Purpose**: Video/audio manipulation (extraction, trimming, concatenation)
- **Integration**: `ffmpeg-python` library wrapping CLI commands
- **Data Flow**: File paths in, processed files out

### NeMo Toolkit (Parakeet)

- **Purpose**: English speech-to-text transcription
- **Model**: `nvidia/parakeet-tdt-0.6b-v2`
- **Integration**: Python API, model cached globally
- **Data Flow**: Audio file path in, transcription text out

### OpenAI Whisper

- **Purpose**: Non-English speech-to-text transcription
- **Model**: Medium variant
- **Integration**: Python API, model cached globally
- **Data Flow**: Audio file path in, transcription text out

### Claude API

- **Purpose**: Generate video title and description from transcription
- **Integration**: LangChain with structured output (Pydantic model)
- **Data Flow**: Transcription text in, VideoMetadata object out
