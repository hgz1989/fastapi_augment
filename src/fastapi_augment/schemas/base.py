"""
@Author         : hangu
@CreateDate     : 2026/9/1
@Description    : Schema全局基类
"""
from __future__ import annotations

from datetime import datetime, date

from pydantic import field_serializer, BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class _TimeSerializer:
    """时间序列化混入，统一 datetime / date 的 JSON 输出格式。

    datetime → 'YYYY-MM-DD HH:MM:SS'（空格分隔）
    date     → 'YYYY-MM-DD'
    """

    @field_serializer('*', when_used='json')
    def _serialize_time(self, value: object) -> object:
        if isinstance(value, datetime):
            return value.isoformat(sep=' ', timespec='milliseconds').replace('+00:00', 'Z')
        if isinstance(value, date):
            return value.isoformat()
        return value


class SchemaBase(_TimeSerializer, BaseModel):
    """
    API对外输出基类：仅用于接口返回JSON，**不做ORM读取**
    关闭 from_attributes，避免误用；保留驼峰、时间序列化
    """
    model_config = ConfigDict(
        populate_by_name=True,
        extra='ignore',
        alias_generator=to_camel
    )


class ORMSchemaBase(SchemaBase):
    """全局所有Pydantic Schema基类
    统一配置、统一行为
    """
    model_config = ConfigDict(
        **SchemaBase.model_config,  # 复制父类配置
        from_attributes=True,
        arbitrary_types_allowed=True,
    )
