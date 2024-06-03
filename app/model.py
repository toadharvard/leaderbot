from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    ForeignKey,
    Table,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from app.session import ORMModel

game_participant_association = Table(
    "game_participant_association",
    ORMModel.metadata,
    Column("game_id", Integer, ForeignKey("games.id")),
    Column("player_id", Integer, ForeignKey("players.id")),
)


class User(ORMModel):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    ratings = relationship("Rating", back_populates="user")


class Rating(ORMModel):
    __tablename__ = "ratings"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="ratings")
    players = relationship(
        "Player", back_populates="rating", cascade="all, delete-orphan"
    )
    games = relationship("Game", back_populates="rating", cascade="all, delete-orphan")
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="unique_rating_per_user"),
    )


class Player(ORMModel):
    __tablename__ = "players"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    rating_id = Column(Integer, ForeignKey("ratings.id"), nullable=False)
    rating = relationship("Rating", back_populates="players")
    games = relationship(
        "Game", secondary=game_participant_association, back_populates="participants"
    )
    statistics_id = Column(
        Integer,
        ForeignKey("player_statistics.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    statistics = relationship(
        "PlayerStatistics", back_populates="player", cascade="all, delete"
    )
    __table_args__ = (
        UniqueConstraint("rating_id", "name", name="unique_player_name_per_rating"),
    )


class PlayerStatistics(ORMModel):
    __tablename__ = "player_statistics"
    id = Column(Integer, primary_key=True, autoincrement=True)
    player = relationship("Player", back_populates="statistics", uselist=False)
    played_games = Column(Integer, default=0)
    wins = Column(Integer, nullable=False, default=0)
    rating_value = Column(Float, nullable=False, default=1500.0)

    @property
    def losses(self):
        return self.played_games - self.wins

    @property
    def win_rate(self):
        played_games = self.played_games
        if played_games == 0:
            return 0
        return self.wins / played_games


class Game(ORMModel):
    __tablename__ = "games"
    id = Column(Integer, primary_key=True, autoincrement=True)
    rating_id = Column(Integer, ForeignKey("ratings.id"), nullable=False)
    rating = relationship("Rating", back_populates="games")
    participants = relationship(
        "Player", secondary=game_participant_association, back_populates="games"
    )
