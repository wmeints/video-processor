# 6. Runtime View

## Pipeline Execution

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant Pipeline
    participant AudioExtractor
    participant Transcriber
    participant ContentGenerator
    participant VideoEditor
    participant ThumbnailProcessor
    participant FileSystem

    User->>CLI: process video.mp4 --theme dark
    CLI->>CLI: Validate inputs
    CLI->>FileSystem: Create processing/<timestamp>/
    CLI->>Pipeline: run_pipeline(context)

    Note over Pipeline: Step 1: Audio Extraction
    Pipeline->>AudioExtractor: extract_audio(video_path, audio_path)
    AudioExtractor->>FileSystem: Write audio.wav
    AudioExtractor-->>Pipeline: audio_path

    Note over Pipeline: Step 2: Transcription
    Pipeline->>Transcriber: transcribe_audio(audio_path, language)
    Transcriber->>Transcriber: Load/cache model
    Transcriber->>FileSystem: Write transcription.txt
    Transcriber-->>Pipeline: transcription_text

    Note over Pipeline: Step 3: Metadata Generation
    Pipeline->>ContentGenerator: generate_content_metadata(transcription, language)
    ContentGenerator->>ContentGenerator: Call Claude API
    ContentGenerator->>FileSystem: Write metadata.json
    ContentGenerator-->>Pipeline: VideoMetadata

    Note over Pipeline: Step 4: Video Trimming
    Pipeline->>VideoEditor: trim_video(video_path, trimmed_path, start, end)
    VideoEditor->>FileSystem: Write trimmed_video.mp4
    VideoEditor-->>Pipeline: trimmed_path

    Note over Pipeline: Step 5: Thumbnail Addition
    Pipeline->>ThumbnailProcessor: create_thumbnail_with_text(...)
    ThumbnailProcessor->>FileSystem: Write thumbnail_with_text.png
    Pipeline->>ThumbnailProcessor: add_thumbnail_to_video(...)
    ThumbnailProcessor->>FileSystem: Write video_with_thumbnail.mp4
    ThumbnailProcessor-->>Pipeline: final_video_path

    Note over Pipeline: Output Stage
    Pipeline->>FileSystem: Copy to output/<timestamp>_<title>.mp4
    Pipeline->>FileSystem: Write output/<timestamp>_<title>_metadata.json
    Pipeline-->>CLI: Complete
    CLI-->>User: Display output path
```

## Device Detection Flow

The transcriber automatically selects the best available compute device:

```mermaid
flowchart TD
    Start[Start Transcription] --> CheckCUDA{CUDA Available?}
    CheckCUDA -->|Yes| UseCUDA[Use NVIDIA GPU]
    CheckCUDA -->|No| CheckMPS{MPS Available?}
    CheckMPS -->|Yes| UseMPS[Use Apple Silicon GPU]
    CheckMPS -->|No| UseCPU[Use CPU]

    UseCUDA --> LoadModel[Load Model]
    UseMPS --> LoadModel
    UseCPU --> LoadModel
    LoadModel --> Transcribe[Run Transcription]
```

## ProcessingContext Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Created: CLI creates context
    Created --> AudioExtraction: run_pipeline()
    AudioExtraction --> Transcription: audio.wav created
    Transcription --> MetadataGeneration: transcription.txt created
    MetadataGeneration --> VideoTrimming: metadata.json created
    VideoTrimming --> ThumbnailAddition: trimmed_video.mp4 created
    ThumbnailAddition --> OutputStage: video_with_thumbnail.mp4 created
    OutputStage --> [*]: Final output copied
```

## Intermediate Files

Each pipeline run creates a timestamped directory with all intermediate artifacts:

```
processing/20240115_143022/
├── audio.wav                    # Extracted audio (16kHz mono)
├── transcription.txt            # Raw transcription text
├── metadata.json                # Generated title/description
├── trimmed_video.mp4            # Video after trimming
├── thumbnail_with_text.png      # Thumbnail image with overlay
└── video_with_thumbnail.mp4     # Final video before copy
```

This enables debugging by inspecting any stage of the pipeline.
