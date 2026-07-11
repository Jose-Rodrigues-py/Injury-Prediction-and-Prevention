from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, Float
from datetime import date

class Base(DeclarativeBase):
    pass

class Athlete(Base): 
    __tablename__ = "athletes"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    age: Mapped[int]
    height: Mapped[int]
    # table relationships
    health_metrics: Mapped[list["HealthMetrics"]] = relationship(back_populates="athlete", cascade="all, delete-orphan")
    workouts: Mapped[list["Workout"]] = relationship(back_populates="athlete", cascade="all, delete-orphan")
    races: Mapped[list["Race"]] = relationship(back_populates="athlete", cascade="all, delete-orphan")

class HealthMetrics(Base): 
    __tablename__ = "health_metrics"
    id: Mapped[int] = mapped_column(primary_key=True)
    athlete_id: Mapped[int] = mapped_column(ForeignKey("athletes.id"))
    created_at: Mapped[date]
    resting_hr: Mapped[int]
    weight: Mapped[float] = mapped_column(Float)
    hrv: Mapped[int]
    mood: Mapped[int]
    ctl: Mapped[float] # chronic training load
    vo2_max: Mapped[float] = mapped_column(Float)
    lt: Mapped[float] = mapped_column(Float) # lactate threshold

    athlete: Mapped["Athlete"] = relationship(back_populates="health_metrics") 

class Workout(Base):
    __tablename__ = "workouts"
    id: Mapped[int] = mapped_column(primary_key=True)
    athlete_id: Mapped[int] = mapped_column(ForeignKey("athletes.id"))
    session_type: Mapped[str]
    date: Mapped[date]
    duration: Mapped[int]
    intensity: Mapped[int]
    speed: Mapped[float] = mapped_column(Float)
    average_hr: Mapped[int]
    rpe: Mapped[int] # rate of perceived exertion

    athlete: Mapped["Athlete"] = relationship(back_populates="workouts")

class Race(Base): 
    __tablename__ = "races"
    id: Mapped[int] = mapped_column(primary_key=True)
    athlete_id: Mapped[int] = mapped_column(ForeignKey("athletes.id"))
    date: Mapped[date]
    distance: Mapped[float]
    goal: Mapped[str]

    athlete: Mapped["Athlete"] = relationship(back_populates="races")
