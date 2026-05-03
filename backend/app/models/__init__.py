# backend/app/models/__init__.py
# Import all models here so Alembic autogenerate picks them up.

from app.models.user import User, Session, PasswordResetToken  # noqa: F401
from app.models.sanctum import Sanctum  # noqa: F401
from app.models.guild import Guild, GuildMember, GuildArchive  # noqa: F401
from app.models.quest import (  # noqa: F401
    QuestTemplate,
    QuestInstance,
    QuestCompletion,
    SideQuest,
    SideQuestCompletion,
    AddonQuest,
    AddonQuestCompletion,
)
from app.models.proposal import QuestProposal, ProposalVote  # noqa: F401
from app.models.competition import CompetitionVote  # noqa: F401
from app.models.economy import (  # noqa: F401
    PointTransaction,
    XpTransaction,
    Trade,
    DailyTradeCap,
    SeasonalPoints,
)
from app.models.streak import DailyStreakLog, WeeklyStreakLog  # noqa: F401
from app.models.notification import Notification, NotificationSetting  # noqa: F401
from app.models.badge import Badge, UserBadge  # noqa: F401
from app.models.level import LevelTitle  # noqa: F401
