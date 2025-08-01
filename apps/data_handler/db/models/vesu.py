from sqlalchemy import BigInteger, Column, String
from shared.db.base import Base


class VesuPosition(Base):
    __tablename__ = "vesu_positions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user = Column(String, index=True)
    pool_id = Column(String, index=True)
    collateral_asset = Column(String)
    debt_asset = Column(String)
    block_number = Column(BigInteger)
