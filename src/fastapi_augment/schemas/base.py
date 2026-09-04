"""
@Author         : hangu
@CreateDate     : 2026/9/1
@Description    : Schema全局基类
"""
from __future__ import annotations

from datetime import datetime, date

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class ORMSchemaBase(BaseModel):
    """全局所有Pydantic Schema基类
    统一配置、统一行为
    """
    model_config = ConfigDict(
        # 允许从ORM对象读取属性
        from_attributes=True,
        # 允许使用别名
        populate_by_name=True,
        # 忽略多余字段
        extra='ignore',
        # 允许任意类型
        arbitrary_types_allowed=True,
        # 全局驼峰别名生成器
        alias_generator=to_camel,
        json_encoders={
            datetime: lambda v: v.isoformat().replace('T', ' '),
            date: lambda v: v.isoformat(),
        }
    )


class APISchemaBase(BaseModel):
    """
    API对外输出基类：仅用于接口返回JSON，**不做ORM读取**
    关闭 from_attributes，避免误用；保留驼峰、时间序列化
    """
    model_config = ConfigDict(
        populate_by_name=True,
        extra='ignore',
        alias_generator=to_camel,
        json_encoders={
            datetime: lambda v: v.isoformat().replace('T', ' '),
            date: lambda v: v.isoformat(),
        }
    )