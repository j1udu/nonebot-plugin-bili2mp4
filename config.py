from pydantic import BaseModel, Field


class Config(BaseModel):
    # 超级管理员（可私聊控制本插件）
    super_admins: list[int] = Field(default=[])
