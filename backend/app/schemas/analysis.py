from typing import List, Optional, Any, Dict
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field

# --- Metadata ---
class Metadata(BaseModel):
    title: Optional[str] = Field(None, description="Descriptive title of the video content")
    duration_estimated: Optional[str] = Field(None, description="Estimated duration in seconds (MM:SS format)")
    aspect_ratio: Optional[str] = Field(None, description="e.g., 16:9, 9:16, 1:1")
    resolution_quality: Optional[str] = Field(None, description="e.g., 1080p, 4K, 720p")
    video_type: Optional[str] = Field(None, description="e.g., motion graphics, live-action, etc.")

# --- Transcript ---
class SpokenDialogue(BaseModel):
    timestamp_start: Optional[str] = None
    timestamp_end: Optional[str] = None
    speaker: Optional[str] = None
    text: Optional[str] = None
    source_type: Optional[str] = Field(None, description="Type of speech: 'lyrics', 'voice_over', or 'dialogue'")
    tone: Optional[str] = None
    emotional_quality: Optional[str] = None

class OnScreenText(BaseModel):
    timestamp_start: Optional[str] = None
    timestamp_end: Optional[str] = None
    text: Optional[str] = None
    position: Optional[str] = None
    style: Optional[str] = None
    font_style_notes: Optional[str] = None

class Transcript(BaseModel):
    has_speech: Optional[bool] = None
    spoken_dialogue: List[SpokenDialogue] = Field(default_factory=list)
    on_screen_text: List[OnScreenText] = Field(default_factory=list)

# --- Characters ---
class ScreenTime(BaseModel):
    first_appearance: Optional[str] = None
    last_appearance: Optional[str] = None
    total_appearances: Optional[str] = None

class Character(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None
    role: Optional[str] = None
    screen_time: Optional[ScreenTime] = None
    actions: List[str] = Field(default_factory=list)
    expressions_observed: List[str] = Field(default_factory=list)

# --- Props ---
class Prop(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    material: Optional[str] = None
    usage_context: Optional[str] = None
    scenes_present: List[str] = Field(default_factory=list)

# --- Environment ---
class Lighting(BaseModel):
    type: Optional[str] = None
    mood: Optional[str] = None
    direction: Optional[str] = None

class ColorPalette(BaseModel):
    dominant_colors: List[str] = Field(default_factory=list)
    accent_colors: List[str] = Field(default_factory=list)
    overall_tone: Optional[str] = None

class PrimarySetting(BaseModel):
    type: Optional[str] = None
    description: Optional[str] = None
    lighting: Optional[Lighting] = None
    color_palette: Optional[ColorPalette] = None

class BackgroundElement(BaseModel):
    element: Optional[str] = None
    type: Optional[str] = None
    depth: Optional[str] = None

class EnvironmentAndBackground(BaseModel):
    primary_setting: Optional[PrimarySetting] = None
    background_elements: List[BackgroundElement] = Field(default_factory=list)

# --- Scenes ---
class CameraMovement(BaseModel):
    movement: List[str] = Field(default_factory=list)
    direction: Optional[str] = None
    speed: Optional[str] = None

class Composition(BaseModel):
    framing: Optional[str] = None
    focus: Optional[str] = None
    angle: Optional[str] = None

class SceneAction(BaseModel):
    subject: Optional[str] = None
    action: Optional[str] = None
    object: Optional[str] = None
    purpose: Optional[str] = None

class VisualEffect(BaseModel):
    type: Optional[str] = None
    description: Optional[str] = None

class SceneAudioNotes(BaseModel):
    music: Optional[str] = None
    sound_effects: List[str] = Field(default_factory=list)
    ambient_sound: Optional[str] = None

class Transition(BaseModel):
    type: Optional[str] = None
    direction: Optional[str] = None
    duration: Optional[str] = None

class Scene(BaseModel):
    id: Optional[str] = None
    scene_number: Optional[int] = None
    timestamp_start: Optional[str] = None
    timestamp_end: Optional[str] = None
    duration_seconds: Optional[str] = None
    shot_type: Optional[str] = None
    camera_movement: Optional[CameraMovement] = None
    composition: Optional[Composition] = None
    location: Optional[str] = None
    primary_subject: Optional[str] = None
    characters_present: List[str] = Field(default_factory=list)
    props_present: List[str] = Field(default_factory=list)
    actions_occurring: List[SceneAction] = Field(default_factory=list)
    visual_effects: List[VisualEffect] = Field(default_factory=list)
    audio_notes: Optional[SceneAudioNotes] = None
    transition_to_next: Optional[Transition] = None
    narrative_function: Optional[str] = None

# --- Visual & Cinematographic ---
class CameraWork(BaseModel):
    overall_style: Optional[str] = None
    techniques_used: List[str] = Field(default_factory=list)
    quality_notes: Optional[str] = None

class LightingDesign(BaseModel):
    primary_style: Optional[str] = None
    quality_notes: Optional[str] = None
    special_effects: List[str] = Field(default_factory=list)

class ColorGrading(BaseModel):
    look: Optional[str] = None
    temperature: Optional[str] = None
    contrast: Optional[str] = None
    notable_choices: Optional[str] = None

class VisualEffectsPost(BaseModel):
    has_vfx: Optional[bool] = None
    effects_types: List[str] = Field(default_factory=list)
    quality_assessment: Optional[str] = None

class GraphicsAndText(BaseModel):
    has_graphics: Optional[bool] = None
    types: List[str] = Field(default_factory=list)
    style: Optional[str] = None
    animation_quality: Optional[str] = None

class EditingStyle(BaseModel):
    pacing: Optional[str] = None
    transition_style: Optional[str] = None
    rhythm: Optional[str] = None

class VisualAndCinematographicAnalysis(BaseModel):
    camera_work: Optional[CameraWork] = None
    lighting_design: Optional[LightingDesign] = None
    color_grading: Optional[ColorGrading] = None
    visual_effects_and_post: Optional[VisualEffectsPost] = None
    graphics_and_text: Optional[GraphicsAndText] = None
    editing_style: Optional[EditingStyle] = None

# --- Audio Analysis ---
class Music(BaseModel):
    has_music: Optional[bool] = None
    genre: Optional[str] = None
    mood: Optional[str] = None
    tempo: Optional[str] = None
    instrumentation: List[str] = Field(default_factory=list)
    prominence: Optional[str] = None

class SoundEffects(BaseModel):
    has_sfx: Optional[bool] = None
    types: List[str] = Field(default_factory=list)
    quality: Optional[str] = None

class VoiceAndDialogue(BaseModel):
    has_voiceover: Optional[bool] = None
    has_dialogue: Optional[bool] = None
    voice_characteristics: Optional[str] = None
    recording_quality: Optional[str] = None

class OverallAudioMix(BaseModel):
    balance: Optional[str] = None
    quality: Optional[str] = None

class AudioAnalysis(BaseModel):
    music: Optional[Music] = None
    sound_effects: Optional[SoundEffects] = None
    voice_and_dialogue: Optional[VoiceAndDialogue] = None
    overall_audio_mix: Optional[OverallAudioMix] = None

# --- Content and Themes ---
class Branding(BaseModel):
    has_branding: Optional[bool] = None
    brand_name: Optional[str] = None
    logo_present: Optional[bool] = None
    logo_placements: List[str] = Field(default_factory=list)
    product_mentions: List[str] = Field(default_factory=list)

class ContentAndThemes(BaseModel):
    primary_subject: Optional[str] = None
    themes: List[str] = Field(default_factory=list)
    tone: Optional[str] = None
    mood: Optional[str] = None
    genre_or_category: Optional[str] = None
    target_audience: Optional[str] = None
    purpose: Optional[str] = None
    key_messages: List[str] = Field(default_factory=list)
    branding: Optional[Branding] = None

# --- Technical Quality ---
class VideoQuality(BaseModel):
    resolution: Optional[str] = None
    sharpness: Optional[str] = None
    exposure: Optional[str] = None

class ProductionValues(BaseModel):
    overall_quality: Optional[str] = None
    equipment_level: Optional[str] = None
    post_production: Optional[str] = None

class TechnicalQuality(BaseModel):
    video_quality: Optional[VideoQuality] = None
    production_values: Optional[ProductionValues] = None

# --- Overall Assessment ---
class OverallAssessment(BaseModel):
    summary: Optional[str] = None
    visual_style: Optional[str] = None
    emotional_impact: Optional[str] = None
    memorability_score: Optional[str] = None
    strengths: List[str] = Field(default_factory=list)
    areas_for_improvement: List[str] = Field(default_factory=list)
    comparable_references: List[str] = Field(default_factory=list)

# --- Timeline Summary ---
class TimelineEvent(BaseModel):
    timestamp: Optional[str] = None
    description: Optional[str] = None

class TimelineSummary(BaseModel):
    intro: Optional[TimelineEvent] = None
    key_moments: List[TimelineEvent] = Field(default_factory=list)
    climax: Optional[TimelineEvent] = None
    conclusion: Optional[TimelineEvent] = None

# --- LITE (Root + first-level objects, strings only) ---
class MetadataLite(BaseModel):
    title: Optional[str] = None
    duration_estimated: Optional[str] = None
    aspect_ratio: Optional[str] = None
    resolution_quality: Optional[str] = None
    video_type: Optional[str] = None

class TranscriptLite(BaseModel):
    has_speech: Optional[str] = None
    spoken_dialogue: Optional[str] = None
    on_screen_text: Optional[str] = None

class EnvironmentAndBackgroundLite(BaseModel):
    primary_setting: Optional[str] = None
    background_elements: Optional[str] = None

class VisualAndCinematographicAnalysisLite(BaseModel):
    camera_work: Optional[str] = None
    lighting_design: Optional[str] = None
    color_grading: Optional[str] = None
    visual_effects_and_post: Optional[str] = None
    graphics_and_text: Optional[str] = None
    editing_style: Optional[str] = None

class AudioAnalysisLite(BaseModel):
    music: Optional[str] = None
    sound_effects: Optional[str] = None
    voice_and_dialogue: Optional[str] = None
    overall_audio_mix: Optional[str] = None

class ContentAndThemesLite(BaseModel):
    primary_subject: Optional[str] = None
    themes: Optional[str] = None
    tone: Optional[str] = None
    mood: Optional[str] = None
    genre_or_category: Optional[str] = None
    target_audience: Optional[str] = None
    purpose: Optional[str] = None
    key_messages: Optional[str] = None
    branding: Optional[str] = None

class TechnicalQualityLite(BaseModel):
    video_quality: Optional[str] = None
    production_values: Optional[str] = None

class OverallAssessmentLite(BaseModel):
    summary: Optional[str] = None
    visual_style: Optional[str] = None
    strengths: Optional[str] = None
    areas_for_improvement: Optional[str] = None
    emotional_impact: Optional[str] = None
    memorability_score: Optional[str] = None
    comparable_references: Optional[str] = None

class TimelineSummaryLite(BaseModel):
    intro: Optional[str] = None
    key_moments: Optional[str] = None
    climax: Optional[str] = None
    conclusion: Optional[str] = None
# --- MAIN MODEL ---
class VideoAnalysisResult(BaseModel):
    """Structured analysis result following the detailed vidprompt schema."""
    metadata: Optional[Metadata] = None
    transcript: Optional[Transcript] = None
    characters: List[Character] = Field(default_factory=list)
    props: List[Prop] = Field(default_factory=list)
    environment_and_background: Optional[EnvironmentAndBackground] = None
    scenes: List[Scene] = Field(default_factory=list)
    visual_and_cinematographic_analysis: Optional[VisualAndCinematographicAnalysis] = None
    audio_analysis: Optional[AudioAnalysis] = None
    content_and_themes: Optional[ContentAndThemes] = None
    technical_quality: Optional[TechnicalQuality] = None
    overall_assessment: Optional[OverallAssessment] = None
    timeline_summary: Optional[TimelineSummary] = None

class VideoAnalysisLite(BaseModel):
    """Root-level keys with first-level objects; all fields are strings."""
    metadata: Optional[MetadataLite] = None
    transcript: Optional[TranscriptLite] = None
    hook: Optional[str] = None
    call_to_action: Optional[str] = None
    on_screen_texts: Optional[str] = None
    key_topics: Optional[str] = None
    summary: Optional[str] = None
    hashtags: Optional[str] = None
    characters: Optional[str] = None
    props: Optional[str] = None
    environment_and_background: Optional[EnvironmentAndBackgroundLite] = None
    scenes: Optional[str] = None
    visual_and_cinematographic_analysis: Optional[VisualAndCinematographicAnalysisLite] = None
    audio_analysis: Optional[AudioAnalysisLite] = None
    content_and_themes: Optional[ContentAndThemesLite] = None
    technical_quality: Optional[TechnicalQualityLite] = None
    overall_assessment: Optional[OverallAssessmentLite] = None
    timeline_summary: Optional[TimelineSummaryLite] = None

class VideoAnalysisResponse(BaseModel):
    """Response from video analysis endpoint."""
    id: Optional[UUID] = None
    media_asset_id: UUID
    status: str = "processing"  # processing, completed, failed
    analysis: Optional[str] = None  # Markdown string
    error: Optional[str] = None
    created_at: Optional[datetime] = None
    cached: bool = False

