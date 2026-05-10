"""出行计划 数据模型"""
import datetime
from sqlalchemy import String, Boolean, DateTime, Text, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TravelPlan(Base):
    __tablename__ = "travel_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, comment="出行标题")
    destination: Mapped[str] = mapped_column(String(255), nullable=True, default="", comment="目的地")
    plan_date: Mapped[str] = mapped_column(String(20), nullable=True, default="", comment="计划日期 YYYY-MM-DD")
    start_time: Mapped[str] = mapped_column(String(10), nullable=True, default="", comment="出发时间 HH:MM")
    notes: Mapped[str] = mapped_column(Text, nullable=True, default="", comment="备注")
    # 天气提醒相关
    need_umbrella: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否需要带伞")
    weather_tip: Mapped[str] = mapped_column(String(500), nullable=True, default="", comment="天气提示")
    temperature: Mapped[str] = mapped_column(String(50), nullable=True, default="", comment="温度信息")
    completed: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否已完成")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, comment="创建时间"
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        comment="更新时间",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "destination": self.destination or "",
            "plan_date": self.plan_date or "",
            "start_time": self.start_time or "",
            "notes": self.notes or "",
            "need_umbrella": self.need_umbrella,
            "weather_tip": self.weather_tip or "",
            "temperature": self.temperature or "",
            "completed": self.completed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
