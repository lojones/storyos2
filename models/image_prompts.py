from pydantic import BaseModel, Field

class VisualPrompts(BaseModel):
    visual_prompt_1: str = Field(..., description="First visual prompt, usually describing characters or events.")
    visual_prompt_2: str = Field(..., description="Second visual prompt, usually describing a setting or environment.")
    visual_prompt_3: str = Field(..., description="Third visual prompt, usually describing a scene with mood or atmosphere.")
