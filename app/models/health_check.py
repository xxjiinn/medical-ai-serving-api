"""
SQLAlchemy 모델: raw_health_check, clean_risk_result

ERD.md 스키마를 Python 클래스로 구현
"""

from sqlalchemy import (
    Column, BigInteger, SmallInteger, Integer, String,
    Boolean, DECIMAL, Enum, TIMESTAMP, ForeignKey,
    Index, func
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class RawHealthCheck(Base):
    """
    원본 건강검진 데이터 테이블

    CSV 원본을 최소 처리하여 저장 (재처리 가능)
    """
    __tablename__ = 'raw_health_check'

    # Primary Key
    id = Column(BigInteger, primary_key=True, autoincrement=True)

    # 기본 정보
    reference_year = Column(SmallInteger, nullable=False, default=2024)
    subscriber_id = Column(String(20), nullable=True)
    province_code = Column(SmallInteger, nullable=True)
    gender_code = Column(SmallInteger, nullable=False)
    age_group_code = Column(SmallInteger, nullable=False)

    # 신체 계측
    height = Column(SmallInteger, nullable=True)  # cm
    weight = Column(SmallInteger, nullable=True)  # kg
    waist_circumference = Column(SmallInteger, nullable=True)  # cm

    # 혈압
    systolic_bp = Column(SmallInteger, nullable=True)  # mmHg
    diastolic_bp = Column(SmallInteger, nullable=True)  # mmHg

    # 혈당
    fasting_glucose = Column(SmallInteger, nullable=True)  # mg/dL

    # 지질
    total_cholesterol = Column(SmallInteger, nullable=True)  # mg/dL
    triglycerides = Column(SmallInteger, nullable=True)  # mg/dL
    hdl_cholesterol = Column(SmallInteger, nullable=True)  # mg/dL
    ldl_cholesterol = Column(SmallInteger, nullable=True)  # mg/dL (참고용)

    # 생활습관
    smoking_status = Column(SmallInteger, nullable=True)  # 1: 비흡연, 2: 과거, 3: 현재

    # 메타데이터
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())

    # Relationship (1:1)
    clean_result = relationship(
        'CleanRiskResult',
        back_populates='raw_record',
        uselist=False,  # 1:1 관계
        cascade='all, delete-orphan'
    )

    # 인덱스 (조회 성능)
    __table_args__ = (
        Index('idx_age_group', 'age_group_code'),
        Index('idx_gender', 'gender_code'),
        Index('idx_systolic_bp', 'systolic_bp'),
    )

    def __repr__(self):
        return f"<RawHealthCheck(id={self.id}, age={self.age_group_code}, gender={self.gender_code})>"


class CleanRiskResult(Base):
    """
    위험요인 판정 결과 테이블

    raw 데이터를 기반으로 7개 위험요인 flag + risk_group 계산
    """
    __tablename__ = 'clean_risk_result'

    # Primary Key
    id = Column(BigInteger, primary_key=True, autoincrement=True)

    # Foreign Key
    raw_id = Column(
        BigInteger,
        ForeignKey('raw_health_check.id', ondelete='CASCADE', onupdate='CASCADE'),
        nullable=False,
        unique=True  # 1:1 관계 보장
    )

    # 계산 필드
    bmi = Column(DECIMAL(4, 1), nullable=True)  # BMI = weight / (height/100)^2

    # 위험요인 Flags (7개)
    flag_hypertension = Column(Boolean, nullable=False, default=False)  # SBP≥140 or DBP≥90
    flag_diabetes = Column(Boolean, nullable=False, default=False)      # 공복혈당≥126
    flag_tc_high = Column(Boolean, nullable=False, default=False)       # TC≥240
    flag_tg_high = Column(Boolean, nullable=False, default=False)       # TG≥200
    flag_hdl_low = Column(Boolean, nullable=False, default=False)       # HDL<40
    flag_obesity = Column(Boolean, nullable=False, default=False)       # BMI≥25
    flag_smoking = Column(Boolean, nullable=False, default=False)       # smoking=3

    # 집계 필드
    risk_factor_count = Column(SmallInteger, nullable=False, default=0)  # 0~7
    risk_group = Column(
        Enum(
            'ZERO_TO_ONE_RISK_FACTOR',
            'MULTIPLE_RISK_FACTORS',
            'CHD_RISK_EQUIVALENT',
            name='risk_group_enum'
        ),
        nullable=False
    )

    # 메타데이터
    rule_version = Column(String(20), nullable=False, default='guideline-v1')
    inference_time_ms = Column(SmallInteger, nullable=True)
    invalid_flag = Column(Boolean, nullable=False, default=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())

    # Relationship
    raw_record = relationship('RawHealthCheck', back_populates='clean_result')

    # 인덱스 (통계 쿼리 최적화)
    __table_args__ = (
        Index('idx_raw_id', 'raw_id'),
        Index('idx_risk_group', 'risk_group'),
        Index('idx_risk_count', 'risk_factor_count'),
        Index('idx_invalid', 'invalid_flag'),
        Index('idx_composite_stats', 'risk_group', 'invalid_flag'),  # 복합 인덱스
    )

    def __repr__(self):
        return f"<CleanRiskResult(id={self.id}, count={self.risk_factor_count}, group={self.risk_group})>"
